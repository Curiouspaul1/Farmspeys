from .import api
from flask import request,jsonify,make_response,current_app
from ..models import User,Space,space_schema,spaces_schema,Space_cat,Product,Order,Review,Cart,Product_cat,user_schema,users_schema
from app.extensions import emailcheck
from sqlalchemy.exc import IntegrityError
from app import bcrypt,db,ma
from uuid import UUID,uuid4
import datetime as d
import jwt, json


# ================================== User Handlers =================================== #

@api.route("/createaccount",methods=['POST'])
def register_user():
    data = request.get_json(force=True)
    phash = bcrypt.generate_password_hash(data["password"])
    new_user = User(name=data['name'],password=phash,member_since=d.datetime.utcnow(),userId=str(uuid4()))
    db.session.add(new_user)
    if emailcheck(data['email']):
        try:
            new_user.email = data['email']
            new_user.username = data['username']
            new_user.telephone = data['telephone']
            db.session.commit()
        except IntegrityError as e:
            return jsonify({'error':'User with email or username or telephone already exists'}),401
    else:
        return jsonify({'error':'Please enter in a valid email address'}),401
    return jsonify({'msg':'Registeration successful'})

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
def getuser(publicId):
    user = User.query.filter_by(userId=publicId).first()
    if not user:
        return jsonify({'error':'No such user found'}),401
    
    return user_schema.jsonify(user)

@api.route('/getusers')
def getusers():
    users = User.query.all()
    return jsonify(users_schema.dump(users))


# ================================== Space Handlers =================================== #

@api.route('/newspace',methods=['POST'])
def newspace():
    data = request.get_json(force=True)
    new_space = Space(store_name=data['storeName'],description=data['description'],telephone=data['storeTel'],email=data['storeEmail'],farm_address=data['farmAddress'],logo=data['logoUrl'])
    db.session.add(new_space)
    if not IntegrityError:
        db.session.commit()
    elif IntegrityError:
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
def getspace():
    result = Space.query.all()
    return jsonify(spaces_schema.dump(result)),200

@api.route('/addproduct')
def addproducts(current_user):
    data = request.get_json()
    