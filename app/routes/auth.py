from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db, bcrypt
from app.models.user import User
from app.models.portfolio import Portfolio
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import os

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if user exists
        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if user_exists:
            flash('Username or email already exists!', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password=password
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create portfolio for user
        portfolio = Portfolio(
            user_id=user.id,
            title=f"{full_name}'s Portfolio"
        )
        db.session.add(portfolio)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.verify_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact admin.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.dashboard')
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update basic info
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.bio = request.form.get('bio')
        current_user.location = request.form.get('location')
        current_user.website = request.form.get('website')
        current_user.github = request.form.get('github')
        current_user.linkedin = request.form.get('linkedin')
        current_user.twitter = request.form.get('twitter')
        current_user.skills = request.form.get('skills')
        current_user.education = request.form.get('education')
        current_user.experience_years = request.form.get('experience_years', 0)
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
                # Delete old profile pic if not default
                if current_user.profile_pic != 'default-avatar.png':
                    old_pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_pic)
                    if os.path.exists(old_pic_path):
                        os.remove(old_pic_path)
                
                # Save new profile pic
                filename = secure_filename(f"profile_{current_user.id}_{file.filename}")
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                current_user.profile_pic = filename
        
        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '' and allowed_file(file.filename, {'pdf', 'doc', 'docx'}):
                # Delete old resume if exists
                if current_user.resume:
                    old_resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.resume)
                    if os.path.exists(old_resume_path):
                        os.remove(old_resume_path)
                
                # Save new resume
                filename = secure_filename(f"resume_{current_user.id}_{file.filename}")
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                current_user.resume = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')


@bp.route('/delete-resume', methods=['POST'])
@login_required
def delete_resume():
    if current_user.resume:
        resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.resume)
        if os.path.exists(resume_path):
            os.remove(resume_path)
        current_user.resume = None
        db.session.commit()
        flash('Resume deleted successfully!', 'success')
    return redirect(url_for('auth.profile'))

@bp.route('/delete-profile-pic', methods=['POST'])
@login_required
def delete_profile_pic():
    if current_user.profile_pic != 'default-avatar.png':
        pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_pic)
        if os.path.exists(pic_path):
            os.remove(pic_path)
        current_user.profile_pic = 'default-avatar.png'
        db.session.commit()
        flash('Profile picture reset to default!', 'success')
    return redirect(url_for('auth.profile'))
