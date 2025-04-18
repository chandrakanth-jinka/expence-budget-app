from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Expense
from app.services import create_expense, add_expense_to_group
from app import db
import random

bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')

@bp.route('', methods=['GET'])
@login_required
def get_expenses():
    """Get all expenses for current user"""
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'success': True,
        'expenses': [expense.to_dict() for expense in expenses]
    })

@bp.route('', methods=['POST'])
@login_required
def add_expense():
    """Add a new expense"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('amount', 'category', 'date')):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    try:
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    expense = create_expense(
        user_id=current_user.id,
        amount=float(data['amount']),
        category=data['category'],
        description=data.get('description', ''),
        date=date,
        group_id=data.get('group_id')
    )
    
    return jsonify({
        'success': True,
        'message': 'Expense added successfully',
        'expense': expense.to_dict()
    }), 201

@bp.route('/<int:expense_id>', methods=['GET'])
@login_required
def get_expense(expense_id):
    """Get a specific expense"""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'id': expense.id,
        'amount': expense.amount,
        'category': expense.category,
        'description': expense.description,
        'date': expense.date.isoformat()
    })

@bp.route('/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    """Update an expense"""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'amount' in data:
        expense.amount = float(data['amount'])
    if 'category' in data:
        expense.category = data['category']
    if 'description' in data:
        expense.description = data['description']
    if 'date' in data:
        try:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Expense updated successfully',
        'expense': expense.to_dict()
    })

@bp.route('/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db.session.delete(expense)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Expense deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting expense: {str(e)}'
        }), 500

@bp.route('/<int:expense_id>/group/<int:group_id>', methods=['POST'])
@login_required
def add_to_group(expense_id, group_id):
    """Add an expense to a group"""
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    updated_expense = add_expense_to_group(expense_id, group_id)
    
    if not updated_expense:
        return jsonify({'success': False, 'message': 'Failed to add expense to group'}), 400
    
    return jsonify({
        'success': True,
        'message': 'Expense added to group successfully',
        'expense': updated_expense.to_dict()
    })

@bp.route('/test', methods=['POST'])
@login_required
def add_test_expenses():
    """Add 10 test expenses with different categories"""
    try:
        test_categories = [
            'Food', 'Transportation', 'Entertainment', 'Shopping',
            'Utilities', 'Healthcare', 'Education', 'Housing', 'Other'
        ]
        
        descriptions = [
            'Monthly expense', 'Regular purchase', 'One-time payment', 'Weekly expense',
            'Subscription', 'Emergency expense', 'Planned purchase', 'Routine expense',
            'Special occasion', 'Misc expense'
        ]
        
        today = datetime.now().date()
        
        for i in range(min(len(test_categories), 9)):
            # Create expenses with dates spread over the last month
            days_ago = i * 3  # Spread out dates
            expense_date = today - timedelta(days=days_ago)
            
            amount = round((20 + i * 10 + random.uniform(0, 30)), 2)  # Random amount
            
            expense = Expense(
                user_id=current_user.id,
                amount=amount,
                category=test_categories[i],
                description=descriptions[i],
                date=expense_date
            )
            db.session.add(expense)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Test expenses added successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding test expenses: {str(e)}'}), 500 