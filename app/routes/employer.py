from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.job import Job, JobCategory, JobApplication
from app.models.user import User
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('employer', __name__, url_prefix='/employer')

def employer_required(f):
    """Decorator to ensure user is an employer"""
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_employer and not current_user.is_admin:
            flash('Access denied. Employer account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@employer_required
def dashboard():
    """Enhanced employer dashboard with analytics"""
    # Get employer's jobs
    jobs = Job.query.filter_by(posted_by=current_user.id).all()
    active_jobs = [j for j in jobs if j.is_active]
    inactive_jobs = [j for j in jobs if not j.is_active]
    
    # Calculate statistics
    total_jobs = len(jobs)
    total_applications = sum(job.applications_count for job in jobs)
    total_views = sum(job.views_count for job in jobs)
    
    # Recent applications (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_applications = JobApplication.query.join(Job).filter(
        Job.posted_by == current_user.id,
        JobApplication.applied_at >= thirty_days_ago
    ).order_by(JobApplication.applied_at.desc()).limit(10).all()
    
    # Top performing jobs
    top_jobs = sorted(jobs, key=lambda x: x.applications_count, reverse=True)[:5]
    
    # Applications by status
    all_applications = JobApplication.query.join(Job).filter(
        Job.posted_by == current_user.id
    ).all()
    
    status_counts = {
        'pending': len([a for a in all_applications if a.status == 'pending']),
        'reviewed': len([a for a in all_applications if a.status == 'reviewed']),
        'accepted': len([a for a in all_applications if a.status == 'accepted']),
        'rejected': len([a for a in all_applications if a.status == 'rejected'])
    }
    
    return render_template('employer/dashboard.html',
                         jobs=active_jobs,
                         inactive_jobs=inactive_jobs,
                         total_jobs=total_jobs,
                         total_applications=total_applications,
                         total_views=total_views,
                         recent_applications=recent_applications,
                         top_jobs=top_jobs,
                         status_counts=status_counts)

@bp.route('/jobs')
@employer_required
def my_jobs():
    """List all employer's jobs"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Job.query.filter_by(posted_by=current_user.id)
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    jobs = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('employer/my_jobs.html', jobs=jobs, status=status)

@bp.route('/job/<int:job_id>')
@employer_required
def job_detail(job_id):
    """View job details and applications"""
    job = Job.query.get_or_404(job_id)
    
    # Ensure this is the employer's job
    if job.posted_by != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('employer.dashboard'))
    
    # Get applications
    applications = JobApplication.query.filter_by(job_id=job_id).order_by(
        JobApplication.applied_at.desc()
    ).all()
    
    # Group by status
    applications_by_status = {
        'pending': [a for a in applications if a.status == 'pending'],
        'reviewed': [a for a in applications if a.status == 'reviewed'],
        'accepted': [a for a in applications if a.status == 'accepted'],
        'rejected': [a for a in applications if a.status == 'rejected']
    }
    
    return render_template('employer/job_detail.html',
                         job=job,
                         applications=applications,
                         applications_by_status=applications_by_status)

@bp.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
@employer_required
def edit_job(job_id):
    """Edit a job posting"""
    job = Job.query.get_or_404(job_id)
    
    # Ensure this is the employer's job
    if job.posted_by != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('employer.dashboard'))
    
    if request.method == 'POST':
        job.title = request.form.get('title')
        job.company = request.form.get('company')
        job.location = request.form.get('location')
        job.job_type = request.form.get('job_type')
        job.description = request.form.get('description')
        job.requirements = request.form.get('requirements')
        job.required_skills = request.form.get('required_skills')
        job.experience_min = request.form.get('experience_min', type=int)
        job.experience_max = request.form.get('experience_max', type=int)
        job.salary_min = request.form.get('salary_min', type=int)
        job.salary_max = request.form.get('salary_max', type=int)
        job.category_id = request.form.get('category', type=int)
        job.is_featured = request.form.get('is_featured') == 'on'
        
        deadline = request.form.get('deadline')
        if deadline:
            job.application_deadline = datetime.strptime(deadline, '%Y-%m-%d')
        
        job.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Job updated successfully!', 'success')
        return redirect(url_for('employer.job_detail', job_id=job.id))
    
    categories = JobCategory.query.all()
    return render_template('employer/edit_job.html', job=job, categories=categories)

@bp.route('/job/<int:job_id>/toggle-status', methods=['POST'])
@employer_required
def toggle_job_status(job_id):
    """Activate or deactivate a job"""
    job = Job.query.get_or_404(job_id)
    
    if job.posted_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    job.is_active = not job.is_active
    db.session.commit()
    
    status = 'activated' if job.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'Job {status}', 'is_active': job.is_active})

@bp.route('/job/<int:job_id>/delete', methods=['POST'])
@employer_required
def delete_job(job_id):
    """Delete a job posting"""
    job = Job.query.get_or_404(job_id)
    
    if job.posted_by != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('employer.dashboard'))
    
    db.session.delete(job)
    db.session.commit()
    
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('employer.my_jobs'))

@bp.route('/application/<int:application_id>')
@employer_required
def view_application(application_id):
    """View detailed application"""
    application = JobApplication.query.get_or_404(application_id)
    job = application.job
    
    # Ensure this is the employer's job
    if job.posted_by != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('employer.dashboard'))
    
    applicant = User.query.get(application.user_id)
    
    return render_template('employer/view_application.html',
                         application=application,
                         job=job,
                         applicant=applicant)

@bp.route('/application/<int:application_id>/update-status', methods=['POST'])
@employer_required
def update_application_status(application_id):
    """Update application status"""
    application = JobApplication.query.get_or_404(application_id)
    job = application.job
    
    if job.posted_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    new_status = request.json.get('status')
    notes = request.json.get('notes', '')
    
    if new_status not in ['pending', 'reviewed', 'accepted', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    application.status = new_status
    if notes:
        application.notes = notes
    application.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Application status updated to {new_status}',
        'status': new_status
    })

@bp.route('/analytics')
@employer_required
def analytics():
    """Detailed analytics for employer"""
    jobs = Job.query.filter_by(posted_by=current_user.id).all()
    
    # Time-based analytics (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Applications over time
    applications_by_day = db.session.query(
        func.date(JobApplication.applied_at).label('date'),
        func.count(JobApplication.id).label('count')
    ).join(Job).filter(
        Job.posted_by == current_user.id,
        JobApplication.applied_at >= thirty_days_ago
    ).group_by(func.date(JobApplication.applied_at)).all()
    
    # Views over time
    views_data = {
        'total': sum(job.views_count for job in jobs),
        'per_job': [(job.title, job.views_count) for job in sorted(jobs, key=lambda x: x.views_count, reverse=True)[:10]]
    }
    
    # Category performance
    category_stats = db.session.query(
        JobCategory.name,
        func.count(Job.id).label('job_count'),
        func.sum(Job.applications_count).label('total_applications')
    ).join(Job).filter(
        Job.posted_by == current_user.id
    ).group_by(JobCategory.name).all()
    
    return render_template('employer/analytics.html',
                         jobs=jobs,
                         applications_by_day=applications_by_day,
                         views_data=views_data,
                         category_stats=category_stats)

@bp.route('/candidates/search')
@employer_required
def search_candidates():
    """Search for potential candidates"""
    search = request.args.get('search', '')
    skills = request.args.get('skills', '')
    experience = request.args.get('experience', type=int)
    
    query = User.query.filter_by(is_employer=False, is_active=True)
    
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.skills.contains(search))
        )
    
    if skills:
        query = query.filter(User.skills.contains(skills))
    
    if experience:
        query = query.filter(User.experience_years >= experience)
    
    candidates = query.limit(50).all()
    
    return render_template('employer/search_candidates.html',
                         candidates=candidates,
                         search=search,
                         skills=skills,
                         experience=experience)
