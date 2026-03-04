from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.portfolio import Portfolio, WorkExperience, Education, Project, Certification, PortfolioSkill
from datetime import datetime

bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')

@bp.route('/<username>')
def view_portfolio(username):
    from app.models.user import User
    user = User.query.filter_by(username=username).first_or_404()
    portfolio = Portfolio.query.filter_by(user_id=user.id).first()
    
    if not portfolio or (portfolio.profile_visibility == 'private' and current_user.id != user.id):
        flash('This portfolio is private!', 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('portfolio/view_portfolio.html', 
                         user=user, 
                         portfolio=portfolio)

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_portfolio():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.session.add(portfolio)
        db.session.commit()
    
    if request.method == 'POST':
        # Update portfolio basic info
        portfolio.title = request.form.get('title')
        portfolio.headline = request.form.get('headline')
        portfolio.summary = request.form.get('summary')
        portfolio.profile_visibility = request.form.get('visibility', 'public')
        
        db.session.commit()
        flash('Portfolio updated successfully!', 'success')
        return redirect(url_for('portfolio.view_portfolio', username=current_user.username))
    
    return render_template('portfolio/edit_portfolio.html', portfolio=portfolio)

@bp.route('/experience/add', methods=['POST'])
@login_required
def add_experience():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    
    experience = WorkExperience(
        portfolio_id=portfolio.id,
        company=request.form.get('company'),
        position=request.form.get('position'),
        location=request.form.get('location'),
        start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
        end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None,
        current=bool(request.form.get('current')),
        description=request.form.get('description')
    )
    
    db.session.add(experience)
    db.session.commit()
    
    flash('Work experience added!', 'success')
    return redirect(url_for('portfolio.edit_portfolio'))

@bp.route('/project/add', methods=['POST'])
@login_required
def add_project():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    
    project = Project(
        portfolio_id=portfolio.id,
        name=request.form.get('name'),
        description=request.form.get('description'),
        technologies=request.form.get('technologies'),
        project_url=request.form.get('project_url'),
        github_url=request.form.get('github_url'),
        start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d') if request.form.get('start_date') else None,
        end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d') if request.form.get('end_date') else None
    )
    
    db.session.add(project)
    db.session.commit()
    
    flash('Project added!', 'success')
    return redirect(url_for('portfolio.edit_portfolio'))

@bp.route('/skill/add', methods=['POST'])
@login_required
def add_skill():
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    
    skill = PortfolioSkill(
        portfolio_id=portfolio.id,
        skill_name=request.form.get('skill_name'),
        proficiency=request.form.get('proficiency'),
        years_experience=request.form.get('years_experience')
    )
    
    db.session.add(skill)
    db.session.commit()
    
    return jsonify({'success': True, 'skill': skill.skill_name})