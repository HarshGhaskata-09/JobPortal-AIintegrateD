from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.job import Job, JobCategory, JobApplication, SavedJob
from app.models.user import User
from app.ml_models.recommender import JobRecommender

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Get recently posted jobs (last 30 days)
    recent_jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(6).all()
    job_categories = JobCategory.query.limit(8).all()
    
    # Get live statistics from database
    total_active_jobs = Job.query.filter_by(is_active=True).count()
    total_companies = User.query.filter_by(is_employer=True, is_active=True).count()
    total_job_seekers = User.query.filter_by(is_employer=False, is_active=True).count()
    
    # Calculate success rate (applications that were accepted)
    total_applications = JobApplication.query.count()
    accepted_applications = JobApplication.query.filter_by(status='accepted').count()
    success_rate = round((accepted_applications / total_applications * 100), 1) if total_applications > 0 else 0
    
    # Format numbers for display
    def format_stat(number):
        if number >= 1000:
            return f"{number // 1000}K+"
        elif number >= 100:
            return f"{number}+"
        else:
            return str(number)
    
    return render_template('index.html', 
                         featured_jobs=recent_jobs,
                         job_categories=job_categories,
                         total_active_jobs=format_stat(total_active_jobs),
                         total_companies=format_stat(total_companies),
                         total_job_seekers=format_stat(total_job_seekers),
                         success_rate=success_rate if success_rate > 0 else 'N/A')

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_employer:
        # Employer dashboard
        posted_jobs = Job.query.filter_by(posted_by=current_user.id).order_by(Job.created_at.desc()).limit(5).all()
        total_applications = sum(job.applications_count for job in posted_jobs)
        return render_template('dashboard/employer_dashboard.html',
                             posted_jobs=posted_jobs,
                             total_applications=total_applications)
    else:
        # Job seeker dashboard
        saved_jobs = SavedJob.query.filter_by(user_id=current_user.id).order_by(SavedJob.saved_at.desc()).limit(5).all()
        applications = JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.applied_at.desc()).limit(5).all()
        
        # Get recommendations
        recommender = JobRecommender()
        recommendations = recommender.get_recommendations_for_user(current_user.id)
        
        return render_template('dashboard/user_dashboard.html',
                             saved_jobs=saved_jobs,
                             applications=applications,
                             recommendations=recommendations)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')