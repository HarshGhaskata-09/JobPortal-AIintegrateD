from app import db
from datetime import datetime

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    headline = db.Column(db.String(500))
    summary = db.Column(db.Text)
    profile_visibility = db.Column(db.String(20), default='public')  # public, private, connections
    theme = db.Column(db.String(50), default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    experiences = db.relationship('WorkExperience', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    education = db.relationship('Education', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    certifications = db.relationship('Certification', backref='portfolio', lazy=True, cascade='all, delete-orphan')
    skills = db.relationship('PortfolioSkill', backref='portfolio', lazy=True, cascade='all, delete-orphan')

class WorkExperience(db.Model):
    __tablename__ = 'work_experiences'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    achievements = db.Column(db.Text)

class Education(db.Model):
    __tablename__ = 'education'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(200))
    field_of_study = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    grade = db.Column(db.String(50))
    description = db.Column(db.Text)

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    technologies = db.Column(db.Text)  # Comma-separated
    project_url = db.Column(db.String(500))
    github_url = db.Column(db.String(500))
    image = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_featured = db.Column(db.Boolean, default=False)

class Certification(db.Model):
    __tablename__ = 'certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(200))
    issue_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    credential_id = db.Column(db.String(100))
    credential_url = db.Column(db.String(500))

class PortfolioSkill(db.Model):
    __tablename__ = 'portfolio_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.Integer)  # 1-5
    years_experience = db.Column(db.Float)