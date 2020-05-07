import os

basedir = os.getcwd()
dbpassword = os.getenv('dbpassword')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or os.urandom(24)
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('USERNAME')
    MAIL_PASSWORD = os.environ.get('PASSWORD')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_URI') or f"sqlite:///{basedir}/fdevdb.sqlite"
    FLASKY_ADMIN = os.environ.get('FLASK_ADMIN')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_URI') or f"sqlite:///{basedir}/ftest.sqlite"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,

    'default' : DevelopmentConfig
}