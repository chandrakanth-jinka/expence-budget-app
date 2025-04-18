from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from app.services import create_user

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/login.html')
            
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('views.index'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if not email or not password or not name:
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
            
        # Create user using the service function
        user = create_user(email, password, name)
        
        login_user(user)
        flash('Registration successful! Welcome to Personal Finance Tracker.', 'success')
        return redirect(url_for('views.index'))
        
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name
    }) 