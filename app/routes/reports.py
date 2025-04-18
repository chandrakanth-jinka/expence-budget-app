from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app.services import get_monthly_report, get_group_balance
from app.models import Group, Expense, Budget
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from app import db

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

def get_date_range(days):
    """Helper function to get date range"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=int(days))
    return start_date, end_date

@bp.route('/debug', methods=['GET'])
@login_required
def debug_data():
    """Debug endpoint to check raw expense data"""
    # Get all expenses for the current user
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Get all categories
    categories = db.session.query(Expense.category).filter_by(user_id=current_user.id).distinct().all()
    unique_categories = [cat[0] for cat in categories]
    
    # Get expense count by category
    category_counts = {}
    for cat in unique_categories:
        count = Expense.query.filter_by(user_id=current_user.id, category=cat).count()
        category_counts[cat] = count
    
    # Get raw data that would be sent for category report
    date_range = request.args.get('dateRange', '365')  # Default to a year
    start_date, end_date = get_date_range(date_range)
    
    # Raw query results
    raw_query = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by(Expense.category).all()
    
    raw_results = [{'category': cat, 'amount': float(total)} for cat, total in raw_query]
    
    result = {
        'total_expenses': len(expenses),
        'unique_categories': unique_categories,
        'category_counts': category_counts,
        'raw_query_results': raw_results,
        'expenses_sample': [expense.to_dict() for expense in expenses[:10]]  # First 10 expenses
    }
    
    return jsonify(result)

@bp.route('/monthly', methods=['GET'])
@login_required
def monthly_report():
    """Get expense report for a date range"""
    date_range = request.args.get('dateRange', '30')  # Default to 30 days
    
    start_date, end_date = get_date_range(date_range)
    
    # Get expenses for the date range
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).order_by(Expense.date).all()
    
    # Calculate totals and prepare data
    total_spent = sum(expense.amount for expense in expenses)
    expense_data = [expense.to_dict() for expense in expenses]
    
    # Get current month's budgets
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month,
        year=current_year
    ).all()
    
    budget_dict = {budget.category: budget.amount for budget in budgets}
    
    # Debug information
    expense_categories = set([expense.category for expense in expenses])
    category_amounts = {}
    for category in expense_categories:
        category_amounts[category] = sum(expense.amount for expense in expenses if expense.category == category)
    
    # Even if no expenses, return valid data structure
    return jsonify({
        'success': True,
        'data': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_spent': total_spent,
            'expenses': expense_data if expense_data else [],
            'budgets': budget_dict,
            'debug': {
                'unique_categories': list(expense_categories),
                'category_amounts': category_amounts,
                'expense_count': len(expenses)
            }
        }
    })

@bp.route('/category', methods=['GET'])
@login_required
def category_report():
    """Get category-wise expense breakdown for a date range"""
    date_range = request.args.get('dateRange', '30')  # Default to 30 days
    
    start_date, end_date = get_date_range(date_range)
    
    # Get all expenses for debugging
    all_expenses = Expense.query.filter(
        Expense.user_id == current_user.id
    ).all()
    
    all_categories = set([expense.category for expense in all_expenses])
    
    # Get expenses grouped by category
    category_totals = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by(Expense.category).all()
    
    # Convert to list of dictionaries for the chart
    expenses = [{'category': cat, 'amount': float(total)} for cat, total in category_totals]
    total_spent = sum(expense['amount'] for expense in expenses) if expenses else 0
    
    # Get budgets for the current month
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month,
        year=current_year
    ).all()
    
    budget_dict = {budget.category: budget.amount for budget in budgets}
    
    # Calculate budget vs actual for each category
    category_breakdown = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        category_breakdown[category] = {
            'spent': amount,
            'budget': budget_dict.get(category, 0),
            'remaining': budget_dict.get(category, 0) - amount
        }
    
    # Add categories with budget but no expenses
    for category, amount in budget_dict.items():
        if category not in category_breakdown:
            category_breakdown[category] = {
                'spent': 0,
                'budget': amount,
                'remaining': amount
            }
            expenses.append({'category': category, 'amount': 0})
    
    # Debug info for development
    debug_info = {
        'all_categories': list(all_categories),
        'filtered_categories': [item['category'] for item in expenses],
        'date_range': f"{start_date} to {end_date}",
        'raw_query_results': [{'category': cat, 'amount': float(total)} for cat, total in category_totals],
        'expense_count': {
            'total': len(all_expenses),
            'filtered': sum(1 for exp in all_expenses if exp.date >= start_date and exp.date <= end_date)
        }
    }
    
    # Even if no expenses, return valid data structure
    return jsonify({
        'success': True,
        'data': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_spent': total_spent,
            'expenses': expenses if expenses else [],
            'category_breakdown': category_breakdown,
            'debug': debug_info
        }
    })

@bp.route('/balance/<int:group_id>', methods=['GET'])
@login_required
def group_balance(group_id):
    """Get balance report for a group"""
    group = Group.query.get_or_404(group_id)
    
    # Check if user is a member of the group
    if current_user not in group.members:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    balances = get_group_balance(group_id)
    
    if not balances:
        return jsonify({'success': False, 'message': 'Failed to calculate balances'}), 400
    
    # Get user names for the balances
    from app.models import User
    user_names = {user.id: user.name for user in User.query.filter(User.id.in_(balances.keys())).all()}
    
    return jsonify({
        'success': True,
        'group_id': group_id,
        'group_name': group.name,
        'balances': {
            user_names[user_id]: amount
            for user_id, amount in balances.items()
        }
    }) 