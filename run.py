from app import __call__,db
from app.extensions import migrate
from flask import jsonify
from models import User,Cart,Role,Space,Product,Product_cat,Space_cat,users_schema,user_schema
import os

app = __call__(os.getenv("FLASK_CONFIG") or "default")
migrate.init_app(app,db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db,app=app,jsonify=jsonify,User=User,users_schema=users_schema,user_schema=user_schema,Role=Role,Space=Space,Product=Product,Product_cat=Product_cat,Space_cat=Space_cat)
