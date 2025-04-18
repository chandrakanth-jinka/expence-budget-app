from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('views', __name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Render the index page"""
    return render_template('index.html')

@bp.route('/login')
def login():
    """Render the login page"""
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    return render_template('login.html')

@bp.route('/register')
def register():
    """Render the register page"""
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    return render_template('register.html')

@bp.route('/expenses')
@login_required
def expenses():
    """Render the expenses page"""
    return render_template('expenses.html')

@bp.route('/budgets')
@login_required
def budgets():
    """Render the budgets page"""
    return render_template('budgets.html')

@bp.route('/reports')
@login_required
def reports():
    """Render the reports page"""
    return render_template('reports.html') 