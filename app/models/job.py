from app import db
from datetime import datetime

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    company_logo = db.Column(db.String(200))
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(50))  # Full-time, Part-time, Remote, Contract
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    required_skills = db.Column(db.Text)  # Comma-separated skills
    experience_min = db.Column(db.Integer)
    experience_max = db.Column(db.Integer)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_currency = db.Column(db.String(10), default='USD')
    benefits = db.Column(db.Text)
    application_deadline = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    applications_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('job_categories.id'))
    
    # Relationships
    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')
    saved_by_users = db.relationship('SavedJob', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def get_required_skills_list(self):
        if self.required_skills:
            return [skill.strip() for skill in self.required_skills.split(',')]
        return []
    
    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'

class JobCategory(db.Model):
    __tablename__ = 'job_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50))
    description = db.Column(db.Text)
    jobs = db.relationship('Job', backref='category', lazy=True)

class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    resume = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')  # pending, reviewed, rejected, accepted
    notes = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'job_id', name='unique_application'),)

class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'job_id', name='unique_saved_job'),)