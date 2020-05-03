from flask import Flask
from .extensions import db,ma,mail,bcrypt
from config import config



def __call__(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    db.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)

    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint,url_prefix='/api')

    return app