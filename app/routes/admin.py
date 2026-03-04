from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.job import Job, JobApplication, JobCategory
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get statistics
    total_users = User.query.count()
    total_employers = User.query.filter_by(is_employer=True).count()
    total_job_seekers = User.query.filter_by(is_employer=False, is_admin=False).count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(is_active=True).count()
    total_applications = JobApplication.query.count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_applications = JobApplication.query.order_by(JobApplication.applied_at.desc()).limit(5).all()
    
    # Weekly stats
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_jobs_week = Job.query.filter(Job.created_at >= week_ago).count()
    new_applications_week = JobApplication.query.filter(JobApplication.applied_at >= week_ago).count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_employers=total_employers,
                         total_job_seekers=total_job_seekers,
                         total_jobs=total_jobs,
                         active_jobs=active_jobs,
                         total_applications=total_applications,
                         recent_users=recent_users,
                         recent_jobs=recent_jobs,
                         recent_applications=recent_applications,
                         new_users_week=new_users_week,
                         new_jobs_week=new_jobs_week,
                         new_applications_week=new_applications_week)


@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage all users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)


@bp.route('/user/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activate/Deactivate user"""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot deactivate admin users.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin users.', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/jobs')
@login_required
@admin_required
def jobs():
    """Manage all jobs"""
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.order_by(Job.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/jobs.html', jobs=jobs)


@bp.route('/job/<int:job_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_job_active(job_id):
    """Activate/Deactivate job"""
    job = Job.query.get_or_404(job_id)
    job.is_active = not job.is_active
    db.session.commit()
    
    status = 'activated' if job.is_active else 'deactivated'
    flash(f'Job "{job.title}" has been {status}.', 'success')
    return redirect(url_for('admin.jobs'))


@bp.route('/job/<int:job_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_job(job_id):
    """Delete job"""
    job = Job.query.get_or_404(job_id)
    title = job.title
    db.session.delete(job)
    db.session.commit()
    
    flash(f'Job "{title}" has been deleted.', 'success')
    return redirect(url_for('admin.jobs'))


@bp.route('/applications')
@login_required
@admin_required
def applications():
    """View all applications"""
    page = request.args.get('page', 1, type=int)
    applications = JobApplication.query.order_by(JobApplication.applied_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/applications.html', applications=applications)

