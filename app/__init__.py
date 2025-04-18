from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-please-change')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration with validation
    mail_config = {
        'MAIL_SERVER': os.getenv('MAIL_SERVER'),
        'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'true').lower() == 'true',
        'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.getenv('MAIL_DEFAULT_SENDER')
    }
    
    # Log email configuration (without password)
    logger.info("Email Configuration:")
    logger.info(f"Server: {mail_config['MAIL_SERVER']}")
    logger.info(f"Port: {mail_config['MAIL_PORT']}")
    logger.info(f"Use TLS: {mail_config['MAIL_USE_TLS']}")
    logger.info(f"Username: {mail_config['MAIL_USERNAME']}")
    logger.info(f"Default Sender: {mail_config['MAIL_DEFAULT_SENDER']}")
    
    # Validate email configuration
    if not all([mail_config['MAIL_SERVER'], mail_config['MAIL_USERNAME'], mail_config['MAIL_PASSWORD']]):
        logger.warning("Email configuration is incomplete. Email notifications will not work.")
    else:
        logger.info("Email configuration is complete.")
    
    # Update app config
    app.config.update(mail_config)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from app.routes import auth, views, expenses, budgets, reports
    app.register_blueprint(auth.bp)
    app.register_blueprint(views.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(budgets.bp)
    app.register_blueprint(reports.bp)
    
    # Add template context processor
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now()
        }
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 