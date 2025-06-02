from flask import Blueprint, render_template, redirect, url_for, request, flash, Response, send_file, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime
from sqlalchemy import func # Import func for aggregation
import os
from app import db
from app.models import Expense, User, Budget # Import the Expense, User, and Budget models

bp = Blueprint('views', __name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Render the index page"""
    return render_template('index.html', user=current_user)

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

@bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    """Handle expenses page GET and POST requests"""
    if request.method == 'POST':
        # Handle adding a new expense
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid data provided'}), 400

        amount = data.get('amount')
        category = data.get('category')
        description = data.get('description')
        date_str = data.get('date')

        # Basic validation
        if not all([amount, category, date_str]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        try:
            # Convert date string to datetime object
            expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Create new expense object
            new_expense = Expense(
                amount=amount,
                category=category,
                description=description,
                date=expense_date,
                user_id=current_user.id
            )

            # Add to database and commit
            db.session.add(new_expense)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Expense added successfully!'}), 201

        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        except Exception as e:
            db.session.rollback() # Rollback changes in case of error
            print(f"Error adding expense: {e}") # Log the error on the server side
            return jsonify({'success': False, 'message': 'An error occurred while adding the expense.'}), 500

    else:
        # Handle GET request to render the page
        return render_template('expenses.html', user=current_user, currency_preference=current_user.currency_preference)

@bp.route('/expenses_data')
@login_required
def expenses_data():
    """Return expense data for the current user as JSON"""
    try:
        expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
        # Convert expenses objects to a list of dictionaries
        expenses_list = [{
            'id': expense.id,
            'amount': expense.amount,
            'category': expense.category,
            'description': expense.description,
            'date': expense.date.isoformat() # Format date as ISO string
        } for expense in expenses]
        return jsonify({'success': True, 'expenses': expenses_list})
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching expenses.'}), 500

@bp.route('/budgets')
@login_required
def budgets():
    """Render the budgets page"""
    return render_template('budgets.html', user=current_user, currency_preference=current_user.currency_preference)

@bp.route('/budgets_data')
@login_required
def budgets_data():
    """Return budget data for the current user as JSON"""
    try:
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        budgets_list = []
        for budget in budgets:
            # Calculate spent amount for the budget period
            spent_amount = db.session.query(func.sum(Expense.amount)).filter(
                Expense.user_id == current_user.id,
                func.strftime('%Y-%m', Expense.date) == f'{budget.year}-{budget.month:02}' # Filter by year and month
            ).scalar() or 0

            remaining_amount = budget.amount - spent_amount

            budgets_list.append({
                'id': budget.id,
                'category': budget.category,
                'amount': budget.amount,
                'period': f'{budget.year}-{budget.month:02}', # Format period as YYYY-MM
                'spent': spent_amount,
                'remaining': remaining_amount
            })

        return jsonify({'success': True, 'budgets': budgets_list})
    except Exception as e:
        print(f"Error fetching budgets: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching budgets.'}), 500

@bp.route('/reports')
@login_required
def reports():
    """Render the reports page"""
    return render_template('reports.html', user=current_user)

@bp.route('/profile')
@login_required
def profile():
    """Render the profile page"""
    return render_template('profile.html', user=current_user)

@bp.route('/settings')
@login_required
def settings():
    """Render the settings page"""
    return render_template('settings.html', user=current_user)

@bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    """Handle profile information updates"""
    username = request.form.get('username')
    email = request.form.get('email')

    # TODO: Add validation (e.g., check if email is already taken)
    # Example validation:
    # from app.models import User # Assuming you have a User model
    # existing_user_with_email = User.query.filter_by(email=email).first()
    # if existing_user_with_email and existing_user_with_email.id != current_user.id:
    #     flash('Email address already in use.', 'danger')
    #     return redirect(url_for('views.profile'))

    current_user.name = username
    current_user.email = email

    # TODO: Save changes to the database
    # Example save:
    # from app import db # Assuming your db object is in __init__.py
    # db.session.commit()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('views.profile'))

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Handle password change requests"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # TODO: Add validation
    # Check if current password is correct
    # if not check_password_hash(current_user.password_hash, current_password):
    #     flash('Incorrect current password.', 'danger')
    #     return redirect(url_for('views.profile'))

    # Check if new password matches confirm password
    if new_password != confirm_password:
        flash('New password and confirm password do not match.', 'danger')
        return redirect(url_for('views.profile'))

    # TODO: Update password in the database (remember to hash the new password)
    # Example update:
    # current_user.password_hash = generate_password_hash(new_password)
    # from app import db # Assuming your db object is in __init__.py
    # db.session.commit()

    flash('Password changed successfully!', 'success')
    # Consider re-authenticating the user or logging them out for security
    return redirect(url_for('views.profile'))

@bp.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    """Handle settings updates"""
    currency = request.form.get('currency')
    
    # Update user's currency preference
    current_user.currency_preference = currency
    db.session.commit()
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('views.settings'))

@bp.route('/export_data')
@login_required
def export_data():
    """Handle data export request"""
    try:
        # Create a new workbook
        wb = Workbook()
        
        # Create sheets for expenses and budgets
        expenses_ws = wb.active
        expenses_ws.title = "Expenses"
        budgets_ws = wb.create_sheet("Budgets")
        
        # Add headers for expenses
        expenses_ws.append(['Date', 'Category', 'Description', 'Amount'])
        
        # Add headers for budgets
        budgets_ws.append(['Category', 'Amount', 'Period'])
        
        # TODO: Replace these with actual database queries
        # For now, we'll add some sample data
        sample_expenses = [
            ['2024-03-20', 'Food', 'Groceries', 50.00],
            ['2024-03-19', 'Transport', 'Bus fare', 25.00],
            ['2024-03-18', 'Entertainment', 'Movie tickets', 30.00]
        ]
        
        sample_budgets = [
            ['Food', 500.00, 'Monthly'],
            ['Transport', 200.00, 'Monthly'],
            ['Entertainment', 300.00, 'Monthly']
        ]
        
        # Add sample data to sheets
        for expense in sample_expenses:
            expenses_ws.append(expense)
            
        for budget in sample_budgets:
            budgets_ws.append(budget)
            
        # Auto-adjust columns' width
        for ws in [expenses_ws, budgets_ws]:
            for column in ws.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column[0].column_letter].width = adjusted_width
        
        # Create a temporary file
        temp_file = BytesIO()
        wb.save(temp_file)
        temp_file.seek(0)
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y%m%d')
        filename = f'expense_tracker_data_{current_date}.xlsx'
        
        # Return the file using send_file
        return send_file(
            temp_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'danger')
        return redirect(url_for('views.settings'))

@bp.route('/import_data', methods=['POST'])
@login_required
def import_data():
    """Handle data import request"""
    # TODO: Implement data import functionality
    flash('Import data functionality not yet implemented.', 'info')
    return redirect(url_for('views.settings'))

@bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Handle account deletion request"""
    # TODO: Implement account deletion functionality
    flash('Account deletion functionality not yet implemented.', 'info')
    return redirect(url_for('views.settings')) 