from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.job import Job, JobCategory, JobApplication, SavedJob
from datetime import datetime

bp = Blueprint('jobs', __name__, url_prefix='/jobs')

@bp.route('/saved')
@login_required
def saved_jobs():
    """View all saved jobs"""
    page = request.args.get('page', 1, type=int)
    
    saved = SavedJob.query.filter_by(user_id=current_user.id)\
        .order_by(SavedJob.saved_at.desc())\
        .paginate(page=page, per_page=10)
    
    return render_template('dashboard/saved_jobs.html', saved_jobs=saved)

@bp.route('/browse')
def browse_jobs():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    category = request.args.get('category', '')
    
    query = Job.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(Job.title.contains(search) | Job.company.contains(search))
    if location:
        query = query.filter(Job.location.contains(location))
    if job_type:
        query = query.filter_by(job_type=job_type)
    if category:
        query = query.filter_by(category_id=category)
    
    jobs = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=10)
    
    categories = JobCategory.query.all()
    
    return render_template('jobs/browse_jobs.html', 
                         jobs=jobs, 
                         categories=categories)

@bp.route('/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Increment view count
    job.views_count += 1
    db.session.commit()
    
    # Check if user has saved/applied
    is_saved = False
    has_applied = False
    
    if current_user.is_authenticated:
        is_saved = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first() is not None
        has_applied = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first() is not None
    
    # Similar jobs
    similar_jobs = Job.query.filter(
        Job.category_id == job.category_id,
        Job.id != job.id,
        Job.is_active == True
    ).limit(3).all()
    
    return render_template('jobs/job_detail.html',
                         job=job,
                         is_saved=is_saved,
                         has_applied=has_applied,
                         similar_jobs=similar_jobs)

@bp.route('/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Check if already applied
    existing = JobApplication.query.filter_by(
        user_id=current_user.id, 
        job_id=job_id
    ).first()
    
    if existing:
        flash('You have already applied for this job!', 'warning')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    cover_letter = request.form.get('cover_letter')
    
    application = JobApplication(
        user_id=current_user.id,
        job_id=job_id,
        cover_letter=cover_letter
    )
    
    db.session.add(application)
    
    # Increment applications count
    job.applications_count += 1
    
    db.session.commit()
    
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('jobs.job_detail', job_id=job_id))

@bp.route('/<int:job_id>/save', methods=['POST'])
@login_required
def save_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    saved = SavedJob.query.filter_by(
        user_id=current_user.id, 
        job_id=job_id
    ).first()
    
    if saved:
        db.session.delete(saved)
        db.session.commit()
        return jsonify({'saved': False, 'message': 'Job removed from saved'})
    else:
        saved_job = SavedJob(
            user_id=current_user.id,
            job_id=job_id
        )
        db.session.add(saved_job)
        db.session.commit()
        return jsonify({'saved': True, 'message': 'Job saved successfully'})

@bp.route('/post', methods=['GET', 'POST'])
@login_required
def post_job():
    if not current_user.is_employer and not current_user.is_admin:
        flash('Only employers can post jobs!', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        job = Job(
            title=request.form.get('title'),
            company=request.form.get('company'),
            location=request.form.get('location'),
            job_type=request.form.get('job_type'),
            description=request.form.get('description'),
            requirements=request.form.get('requirements'),
            required_skills=request.form.get('required_skills'),
            experience_min=request.form.get('experience_min'),
            experience_max=request.form.get('experience_max'),
            salary_min=request.form.get('salary_min'),
            salary_max=request.form.get('salary_max'),
            category_id=request.form.get('category'),
            posted_by=current_user.id,
            application_deadline=datetime.strptime(request.form.get('deadline'), '%Y-%m-%d') if request.form.get('deadline') else None
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    categories = JobCategory.query.all()
    return render_template('jobs/post_job.html', categories=categories)