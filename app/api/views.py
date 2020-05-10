from .import api
from flask import request,jsonify,make_response,current_app
from flask_cors import cross_origin
from models import User,Space,space_schema,Permission,spaces_schema,Space_cat,Product,Order,Review,Cart,Product_cat,user_schema,users_schema
from app.extensions import emailcheck
from sqlalchemy.exc import IntegrityError
from app import bcrypt,db,ma,cors
from uuid import UUID,uuid4
import datetime as d
import jwt, json
from functools import wraps

# ================================== User Handlers =================================== #

# authorization handler
def login_required(f):
    @wraps(f)
    def endpoint(*args,**kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
            if not token:
                return make_response(jsonify({'error':'Token is missing'})),401
            #try:
            data = jwt.decode(token,current_app.config['SECRET_KEY'])
            #except:
            #return make_response(jsonify({'error':'An error occurred while trying to decode token'})),500
            
            # fetch logged in user
            current_user = User.query.filter_by(userId=data['publicId']).first()
            
            return f(current_user,*args,**kwargs)
        else:
            return make_response(jsonify({'error':'Token header not found'})),401
    return endpoint

@api.route("/createaccount",methods=['POST'])
#@cross_origin()
def register_user():
    data = request.get_json(force=True)
    phash = bcrypt.generate_password_hash(data["password"])
    new_user = User(name=data['name'],password=phash,member_since=d.datetime.utcnow(),userId=str(uuid4()))
    #if new_user.role == None:
    #    new_user.role = Role.query.filter_by(default=True).first()
    db.session.add(new_user)

    if emailcheck(data['email']):
        try:
            new_user.email = data['email']
            db.session.flush(objects=[new_user])
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({'msg':'Email already exists'}),401)
    else:
        return make_response(jsonify({'msg':'Please enter a valid email address'}),401)
    
    try:
        new_user.username = data['username']
        db.session.flush(objects=[new_user])
    except IntegrityError:
        db.session.rollback()
        return make_response(jsonify({'msg':'username already exists'}),401)
    
    try:
        new_user.telephone = data['telephone']
        db.session.flush(objects=[new_user])
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return make_response(jsonify({'msg':'Telephone already exists'}),401)

    return make_response(jsonify({'msg':'registration successful'}),200)
            

@api.route('/login',methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username:   
        return jsonify({'error':'Invalid auth details'}),401
    
    user = User.query.filter_by(username=auth.username).first() or User.query.filter_by(email=auth.username).first()
    if user:
        if bcrypt.check_password_hash(user.password,auth.password):
            token = jwt.encode({'publicId':user.userId,'exp':d.datetime.utcnow() + d.timedelta(minutes=30)},current_app.config['SECRET_KEY'])
            user.addlastLogin()
            return make_response(jsonify({'token':token.decode('UTF-8')}),200)
        else:
            return jsonify({'error':'Incorrect password'}),401
    else:
        return make_response(jsonify({'error':'No such user found'}),401,{'WWW-Authenticate':'Basic realm="Login Required"'})

@api.route('/getuser/<publicId>')   
@login_required
def getuser(current_user,publicId):
    user = User.query.filter_by(userId=publicId).first()
    if not user:
        return jsonify({'error':'No such user found'}),401
    
    return user_schema.jsonify(user)

@api.route('/getusers')
@login_required
def getusers(current_user):
    users = User.query.all()
    return jsonify(users_schema.dump(users))

@api.route('/promoteuser',methods=['PUT'])
@login_required
def promote(current_user):
    user_role = current_user.role
    user_role.add_permission(Permission.SELL) # adds seller permission
    db.session.commit()

    return jsonify({'msg':'Successfully promoted user to seller'}),200


# ================================== Space Handlers =================================== #

@api.route('/newspace',methods=['POST'])
@login_required
def newspace(current_user):
    if not current_user.role.has_permission(Permission.SELL):
        return jsonify({'error':'You don\'t have permission to perform such action'}),401
    data = request.get_json(force=True)
    new_space = Space(store_name=data['storeName'],description=data['description'],telephone=data['storeTel'],email=data['storeEmail'],farm_address=data['farmAddress'],logo=data['logoUrl'])
    db.session.add(new_space)
    try:
        new_space.farmer = current_user
        db.session.flush()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error':'Store Name is already taken'}),401
    return jsonify({'msg':'New store created successfully!'}),200

@api.route('/getspace/<spaceId>')
def getspace(spaceId):
    result = Space.query.filter_by(id=spaceId).first()
    if not result:
        return jsonify({'error':'No such store found'}),401
    return space_schema.jsonify(result),200

@api.route('/getspaces')
def getspaces():
    result = Space.query.all()
    return jsonify(spaces_schema.dump(result)),200

@api.route('/addproduct',methods=['POST'])
@login_required
def addproducts(current_user):
    data = request.get_json()
    new_product = Product(name=data['productName'],description=data['productDesc'],sale_unit=data['sale_unit'],price=data['price'],images=data['images'],Instock=data['available_stock'],discount=data['discount'],date_created=d.datetime.utcnow())
    db.session.add(new_product)
    # fetch store 
    current_space = current_user.space
    new_product.space = current_space
    db.session.commit()
    return jsonify({'msg':f'Added {new_product.name} successfully'}),200

@api.route('/getallproducts', methods=['GET'])
def getallproducts():
    products = Product.query.all();
    return jsonify(product_schema.dump(products)), 200

@api.route('/updateproduct', methods=['POST'])
def updateproduct(current_user):
    data = request.get_json(force=True) # route accepts json
    product = Product.query.filter_by(productID=product_id).first()

    product.name = data['productName']
    product.description = data['productDesc']
    product.price = data['price']
    product.images = data['images']
    product.Instock = data['available_stock']
    product.discount = data['discount']
    product.date_created = d.datetime.utcnow()

    current_space = current_user.space
    product.space = current_space
    db.session.commit()
    
    return({'msg':f'Updated products successfully'}), 200
    
#@api.route('/delete_product/<product_id>')
#def delete_product(current_user,product_id)

