from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes import auth, main, jobs, portfolio, admin, employer, employer_auth, chatbot
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(employer.bp)
    app.register_blueprint(employer_auth.bp)
    app.register_blueprint(chatbot.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        from app.models.user import User
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@jobportal.com',
                full_name='Administrator',
                is_admin=True,
                password='Admin@123'  # Change this in production!
            )
            db.session.add(admin)
            db.session.commit()
    
    return app