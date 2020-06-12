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
from flask_jwt_extended import (
    jwt_required,create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity,set_access_cookies,
    set_refesh_cookies, unset_jwt_cookies
)

from functools import wraps

# ================================== User Handlers =================================== #

@api.route("/createaccount",methods=['POST'])
#@cross_origin()
def register_user():
    data = request.get_json(force=True)
    phash = bcrypt.generate_password_hash(data["password"])
    new_user = User(name=data['name'],password=phash,member_since=d.datetime.utcnow(),userId=str(uuid4()))
    if new_user.role == None:
        new_user.role = Role.query.filter_by(default=True).first()
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
            

@api.route('/token/auth',methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username:
        resp = jsonify({'error':'Invalid auth details'})
        return resp,401
    user = User.query.filter_by(username=auth.username).first() or User.query.filter_by(email=auth.username).first()
    if user:
        if bcrypt.check_password_hash(user.password,auth.password):
            # create tokens
            access_token = create_access_token(identity=username)
            refresh_token = create_refresh_token(identity=username)
            user.addlastLogin()
            resp = jsonify({'login':True})
            set_access_cookies(resp,access_token)
            set_refesh_cookies(resp,refresh_token)
            return make_response(resp,200)
        else:
            resp = jsonify({'error':'Incorrect Password'})
            return make_response(resp,401)
    else:
        resp = jsonify({'error':'No such user found'})
        return make_response(resp,404)

@api.route('/token/refresh',methods=['POST'])
@jwt_refresh_token_required
def refresh_token():
    # create new access-token
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)

    resp = jsonify({'refresh':True})
    set_access_cookies(resp,access_token)
    return make_response(resp,200)

@api.route('/token/remove',methods=['POST'])
def logout():
    resp = jsonify({'logout':True})
    unset_jwt_cookies(resp)
    return make_response(resp,200)

@api.route('/getuser')
@jwt_required
def getuser():
    user = User.query.filter_by(userId=get_jwt_identity()).first()
    if not user:
        return jsonify({'error':'No such user found'}),401
    
    return user_schema.jsonify(user)

@api.route('/getusers')
@jwt_required
def getusers():
    users = User.query.all()
    return jsonify(users_schema.dump(users))

@api.route('/promoteuser',methods=['PUT'])
@jwt_required
def promote():
    user = User.query.filter_by(userId=get_jwt_identity()).first()
    user_role = user.role
    user_role.add_permission(Permission.SELL) # adds seller permission
    db.session.commit()

    return jsonify({'msg':'Successfully promoted user to seller'}),200


# ================================== Space Handlers =================================== #

@api.route('/newspace',methods=['POST'])
@jwt_required
def newspace():
    user = User.query.filter_by(userId=get_jwt_identity()).first()
    if not user.role.has_permission(Permission.SELL):
        return jsonify({'error':'You don\'t have permission to perform such action'}),401
    data = request.get_json(force=True)
    new_space = Space(store_name=data['storeName'],description=data['description'],telephone=data['storeTel'],email=data['storeEmail'],farm_address=data['farmAddress'],logo=data['logoUrl'])
    db.session.add(new_space)
    try:
        new_space.farmer = user
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
@jwt_required
def addproducts():
    user = User.query.filter_by(userId=get_jwt_identity()).first()
    data = request.get_json()
    new_product = Product(name=data['productName'],description=data['productDesc'],sale_unit=data['sale_unit'],price=data['price'],images=data['images'],Instock=data['available_stock'],discount=data['discount'],date_created=d.datetime.utcnow())
    db.session.add(new_product)
    # fetch store 
    current_space = user.space
    new_product.space = current_space
    db.session.commit()
    return jsonify({'msg':f'Added {new_product.name} successfully'}),200

#@api.route('/delete_product/<product_id>')
#def delete_product(current_user,product_id)

