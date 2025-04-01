from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config  # Import Config from our config.py file

db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Initialize config
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .auth.routes import auth
    from .dashboard.routes import dashboard
    from .api.routes import api
    
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/dashboard')
    app.register_blueprint(api, url_prefix='/api')
    
    return app