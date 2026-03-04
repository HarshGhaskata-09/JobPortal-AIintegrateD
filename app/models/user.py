from app import db, bcrypt
from flask_login import UserMixin
from datetime import datetime
import jwt
from time import time
from config import Config

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100))
    profile_pic = db.Column(db.String(200), default='default-avatar.png')
    resume = db.Column(db.String(200))  # Resume file path
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    github = db.Column(db.String(200))
    linkedin = db.Column(db.String(200))
    twitter = db.Column(db.String(200))
    experience_years = db.Column(db.Float, default=0)
    education = db.Column(db.Text)
    skills = db.Column(db.Text)  # Comma-separated skills
    is_employer = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolios = db.relationship('Portfolio', backref='user', lazy=True, cascade='all, delete-orphan')
    job_applications = db.relationship('JobApplication', backref='applicant', lazy=True, cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', backref='user', lazy=True, cascade='all, delete-orphan')
    posted_jobs = db.relationship('Job', backref='poster', lazy=True, cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('password is not readable')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_reset_token(self, expires_in=3600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            Config.SECRET_KEY, algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_token(token):
        try:
            id = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])['reset_password']
            return User.query.get(id)
        except:
            return None
    
    def get_skills_list(self):
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',')]
        return []
    
    def __repr__(self):
        return f'<User {self.username}>'