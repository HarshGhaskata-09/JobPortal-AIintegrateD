from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

bp = Blueprint('employer_auth', __name__, url_prefix='/employer')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Employer/Company Registration"""
    if current_user.is_authenticated:
        if current_user.is_employer:
            return redirect(url_for('employer.dashboard'))
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        website = request.form.get('website', '')
        location = request.form.get('location', '')
        description = request.form.get('description', '')
        
        # Validation
        if not all([company_name, email, password, confirm_password]):
            flash('All required fields must be filled!', 'danger')
            return render_template('employer/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('employer/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
            return render_template('employer/register.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return render_template('employer/register.html')
        
        # Create username from company name
        username = company_name.lower().replace(' ', '_').replace('-', '_')
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        
        # Create employer account
        employer = User(
            username=username,
            email=email,
            full_name=company_name,
            is_employer=True,
            is_admin=False,
            is_active=True,
            website=website,
            location=location,
            bio=description,
            profile_pic='default.jpg'
        )
        employer.password = password
        
        db.session.add(employer)
        db.session.commit()
        
        flash('Company account created successfully! Please login.', 'success')
        return redirect(url_for('employer_auth.login'))
    
    return render_template('employer/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Employer/Company Login"""
    if current_user.is_authenticated:
        if current_user.is_employer:
            return redirect(url_for('employer.dashboard'))
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please provide email and password!', 'danger')
            return render_template('employer/login.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid email or password!', 'danger')
            return render_template('employer/login.html')
        
        # Check if user is an employer
        if not user.is_employer:
            flash('This is an employer login. Please use the regular login for job seekers.', 'warning')
            return render_template('employer/login.html')
        
        # Verify password
        if not user.verify_password(password):
            flash('Invalid email or password!', 'danger')
            return render_template('employer/login.html')
        
        # Check if account is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return render_template('employer/login.html')
        
        # Login user
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.full_name}!', 'success')
        
        # Redirect to employer dashboard
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/employer'):
            return redirect(next_page)
        return redirect(url_for('employer.dashboard'))
    
    return render_template('employer/login.html')

@bp.route('/logout')
@login_required
def logout():
    """Employer Logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('employer_auth.login'))
