from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Budget, Expense
from app.services import set_budget
from app import db
from datetime import datetime
from sqlalchemy import func
import re
import calendar

bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

@bp.route('', methods=['GET'])
@login_required
def get_budgets():
    """Get all budgets for the current user, optionally filtered by month and year"""
    # Get query parameters for filtering
    period = request.args.get('period')
    
    try:
        # Base query
        query = Budget.query.filter_by(user_id=current_user.id)
        
        # Apply period filter if provided
        if period:
            if not re.match(r'^\d{4}-\d{2}$', period):
                return jsonify({
                    'success': False,
                    'message': 'Period must be in format YYYY-MM'
                }), 400
            year, month = period.split('-')
            query = query.filter_by(year=int(year), month=int(month))
        
        # Execute query and get all matching budgets
        budgets = query.all()
        
        # Process each budget to calculate spent and remaining amounts
        result = []
        for budget in budgets:
            # Format period as YYYY-MM for frontend
            period_str = f"{budget.year}-{budget.month:02d}"
            
            # Calculate the date range for the month
            start_date = f"{budget.year}-{budget.month:02d}-01"
            last_day = calendar.monthrange(budget.year, budget.month)[1]
            end_date = f"{budget.year}-{budget.month:02d}-{last_day}"
            
            # Sum expenses for this category in this period
            spent = sum(expense.amount for expense in Expense.query.filter(
                Expense.user_id == current_user.id,
                Expense.category == budget.category,
                Expense.date >= start_date,
                Expense.date <= end_date
            ).all())
            
            # Calculate remaining amount
            remaining = budget.amount - spent
            
            # Add to results
            result.append({
                'id': budget.id,
                'category': budget.category,
                'amount': budget.amount,
                'period': period_str,
                'spent': spent,
                'remaining': remaining
            })
        
        return jsonify({
            'success': True,
            'budgets': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving budgets: {str(e)}'
        }), 500

@bp.route('', methods=['POST'])
@login_required
def add_budget():
    """Set or update a budget"""
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    category = data.get('category')
    amount = data.get('amount')
    period = data.get('period')
    
    if not category:
        return jsonify({
            'success': False,
            'message': 'Category is required'
        }), 400
        
    if not amount:
        return jsonify({
            'success': False,
            'message': 'Amount is required'
        }), 400
    
    if not period:
        return jsonify({
            'success': False,
            'message': 'Period is required'
        }), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Amount must be a number'
        }), 400
    
    # Period format should be YYYY-MM
    if not re.match(r'^\d{4}-\d{2}$', period):
        return jsonify({
            'success': False,
            'message': 'Period must be in format YYYY-MM'
        }), 400
    
    # Extract year and month from period
    year, month = period.split('-')
    year = int(year)
    month = int(month)
    
    # Check if a budget already exists for this category and period
    existing_budget = Budget.query.filter_by(
        user_id=current_user.id,
        category=category,
        month=month,
        year=year
    ).first()
    
    try:
        if existing_budget:
            # Update existing budget
            existing_budget.amount = amount
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Budget updated successfully',
                'data': {
                    'id': existing_budget.id,
                    'category': existing_budget.category,
                    'amount': existing_budget.amount,
                    'period': f"{existing_budget.year}-{existing_budget.month:02d}"
                }
            })
        else:
            # Create new budget
            new_budget = Budget(
                user_id=current_user.id,
                category=category,
                amount=amount,
                month=month,
                year=year,
                period='monthly'  # Default to monthly budgets
            )
            db.session.add(new_budget)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Budget created successfully',
                'data': {
                    'id': new_budget.id,
                    'category': new_budget.category,
                    'amount': new_budget.amount,
                    'period': f"{new_budget.year}-{new_budget.month:02d}"
                }
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error saving budget: {str(e)}'
        }), 500

@bp.route('/<int:budget_id>', methods=['GET'])
@login_required
def get_budget(budget_id):
    """Get a specific budget by ID"""
    try:
        budget = Budget.query.get(budget_id)
        
        if not budget:
            return jsonify({
                'success': False,
                'message': 'Budget not found'
            }), 404
            
        if budget.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
            
        # Format period as YYYY-MM
        period_str = f"{budget.year}-{budget.month:02d}"
            
        # Calculate spent and remaining
        start_date = f"{budget.year}-{budget.month:02d}-01"
        last_day = calendar.monthrange(budget.year, budget.month)[1]
        end_date = f"{budget.year}-{budget.month:02d}-{last_day}"
        
        spent = sum(expense.amount for expense in Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.category == budget.category,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all())
        
        remaining = budget.amount - spent
        
        return jsonify({
            'success': True,
            'id': budget.id,
            'category': budget.category,
            'amount': budget.amount,
            'period': period_str,
            'spent': spent,
            'remaining': remaining
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving budget: {str(e)}'
        }), 500

@bp.route('/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    """Delete a budget by id"""
    budget = Budget.query.get(budget_id)
    
    if not budget:
        return jsonify({
            'success': False,
            'message': 'Budget not found'
        }), 404
    
    if budget.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Unauthorized access'
        }), 403
    
    try:
        db.session.delete(budget)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Budget deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting budget: {str(e)}'
        }), 500

@bp.route('/<int:budget_id>', methods=['PUT'])
@login_required
def update_budget(budget_id):
    """Update a budget"""
    budget = Budget.query.get_or_404(budget_id)
    
    if budget.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
        
    try:
        if 'amount' in data:
            amount = float(data['amount'])
            if amount < 0:
                return jsonify({'success': False, 'message': 'Amount cannot be negative'}), 400
            budget.amount = amount
            
        if 'category' in data:
            budget.category = data['category']
            
        if 'period' in data:
            period = data['period']
            # Validate period format
            if not re.match(r'^\d{4}-\d{2}$', period):
                return jsonify({
                    'success': False, 
                    'message': 'Period must be in format YYYY-MM'
                }), 400
                
            # Extract year and month
            year, month = period.split('-')
            budget.year = int(year)
            budget.month = int(month)
        
        db.session.commit()
        
        # Format period for response
        period_str = f"{budget.year}-{budget.month:02d}"
        
        # Calculate spent amount
        start_date = f"{budget.year}-{budget.month:02d}-01"
        last_day = calendar.monthrange(budget.year, budget.month)[1]
        end_date = f"{budget.year}-{budget.month:02d}-{last_day}"
        
        spent = sum(expense.amount for expense in Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.category == budget.category,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all())
        
        budget_dict = {
            'id': budget.id,
            'category': budget.category,
            'amount': budget.amount,
            'period': period_str,
            'spent': spent,
            'remaining': budget.amount - spent
        }
        
        return jsonify({
            'success': True,
            'message': 'Budget updated successfully',
            'budget': budget_dict
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid number format'}), 400 