from app import db,ma
from flask import current_app
import datetime as d

class User(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    userId = db.Column(db.String(50))
    name = db.Column(db.String(100))
    username = db.Column(db.String(100),unique=True)
    telephone = db.Column(db.String(50),unique=True)
    email = db.Column(db.String(50),unique=True)
    password = db.Column(db.String(200))
    member_since = db.Column(db.DateTime())
    lastLogin = db.Column(db.DateTime())
    cart = db.relationship('Cart',backref='buyer',uselist=False)
    reviews = db.relationship('Review',backref='customer')
    space = db.relationship('Space',backref='farmer',uselist=False)
    product= db.relationship('Product', backref='farmer')
    role_id = db.Column(db.Integer,db.ForeignKey('role.id'))
    orders = db.relationship('Order',backref='customer')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == 'admin@farmspeys.com':
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def addlastLogin(self):
        self.lastLogin = d.datetime.utcnow()


class Permission:
    BUY = 1
    SELL = 2
    RATE = 4
    ADMIN = 16

class Role(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    name = db.Column(db.String(50))
    default = db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User',backref='role', lazy='dynamic')

    # sets permission for each instance to zero if it has "None" permission
    def __init__(self,**kwargs):
        super(Role,self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def has_permission(self,perm):
        return self.permissions & perm == perm

    def add_permission(self,perm):
        if not self.has_permission(perm):
           self.permissions += perm

    def remove_permission(self,perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permission(self):
        self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'SELLER':[Permission.BUY,Permission.SELL,Permission.RATE],
            'USER' : [Permission.BUY,Permission.RATE],
            'ADMIN' : [Permission.BUY,Permission.RATE,Permission.SELL,Permission.ADMIN]
        }

        default = 'USER'
        for r in roles:
            role = Role.query.filter_by(name=r).first()  # check to see if role exists
            if role is None:    # if role doesn't exist already
                role = Role(name=r)     # create role
            role.reset_permission()     # reset role permission
            for perm in roles[r]:       # assign role permission
                role.add_permission(perm)

            role.default = role.name == default # assigns the role as default if its name == the set default role in this method
    
            db.session.add(role)
        db.session.commit()
    
class Space(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    spaceId = db.Column(db.String(50))
    store_name = db.Column(db.String(100),unique=True)
    description = db.Column(db.Text)
    telephone = db.Column(db.String(50))
    email = db.Column(db.String(50),unique=True)
    verified = db.Column(db.Boolean,default=False)
    farm_address = db.Column(db.PickleType())
    suspended = db.Column(db.Boolean,default=False)
    logo = db.Column(db.String(50))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    space_cat_id = db.Column(db.Integer,db.ForeignKey('space_cat.id'))
    products = db.relationship('Product',backref='space')
    reviews = db.relationship('Review',backref='space')

class Product(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    productID = db.Column(db.String(50))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    images = db.Column(db.PickleType())
    Instock = db.Column(db.Integer,default=0)
    sale_unit = db.Column(db.String(50))
    discount = db.Column(db.Float)
    date_created = db.Column(db.DateTime())
    reviews = db.relationship('Review',backref='product')
    space_id = db.Column(db.Integer,db.ForeignKey('space.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_cat_id = db.Column(db.Integer,db.ForeignKey('product_cat.id'))

class Product_cat(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    name = db.Column(db.String(100))
    products = db.relationship('Product',backref='product_cat')

class Space_cat(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    name = db.Column(db.String(100))
    stores = db.relationship('Space',backref='space_cat')

class Cart(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    dateCreated = db.Column(db.DateTime())
    products = db.Column(db.PickleType())

class Order(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    status = db.Column(db.String(20))
    refId = db.Column(db.String(100))
    date_created = db.Column(db.DateTime())
    shippingAddress = db.Column(db.PickleType())
    paid = db.Column(db.Boolean)
    customer_id = db.Column(db.Integer,db.ForeignKey('user.id'))

class Review(db.Model):
    id = db.Column(db.Integer,nullable=False,primary_key=True)
    product_id = db.Column(db.Integer,db.ForeignKey('product.id'))
    customer_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    date_created = db.Column(db.DateTime())
    ratings = db.Column(db.Integer)
    description = db.Column(db.Text)
    space_id = db.Column(db.Integer,db.ForeignKey('space.id'))
    verified = db.Column(db.Boolean,default=False)



class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        fields = (
            'id','email','username','userId','telephone','member_since',
            'lastLogin','role_id'
        )

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class SpaceSchema(ma.ModelSchema):
    class Meta:
        model = Space
        fields = (
            'spaceId','id','email','username','userId','telephone','member_since',
            'lastLogin','role_id'
            )

space_schema = SpaceSchema()
spaces_schema = SpaceSchema(many=True)

class ProductSchema(ma.ModelSchema):
    class Meta:
        model = Product
        fields = (
            'id', 'productID', 'name', 'description', 'price', 'images',
            'Instock', 'discount','date_created', 'space_id', 'user_id'
        )

product_schema = ProductSchema()
products_schema  = ProductSchema(many=True)