from datetime import datetime
from sqlalchemy import func
from app import db, mail
from app.models import User, Expense, Budget, Group
from flask import current_app
from flask_mail import Message
import logging

logger = logging.getLogger(__name__)

def send_expense_notification(user, expense, remaining_budget):
    """Send email notification for new expense"""
    subject = "New Expense Recorded"
    body = f"""
    A new expense has been added. Here's your updated financial summary:

    Expense Details:
    - Amount: ₹{expense.amount:.2f}
    - Category: {expense.category}
    - Description: {expense.description}
    - Date: {expense.date.strftime('%Y-%m-%d')}

    Remaining Budget: ₹{remaining_budget:.2f}

    Please review your spending patterns regularly.
    """
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body
    )
    mail.send(msg)

def send_budget_notification(user, budget, current_expenses):
    """Send email notification for new budget"""
    subject = "New Budget Update"
    body = f"""
    A new budget has been added. Here's your updated financial summary:

    Budget Details:
    - Category: {budget.category}
    - Amount: ₹{budget.amount:.2f}
    - Period: {budget.period}
    - Month: {budget.month}
    - Year: {budget.year}

    Current Expenses in this Category: ₹{current_expenses:.2f}

    Please review your budget regularly.
    """
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body
    )
    mail.send(msg)

def send_low_budget_alert(user, category, remaining_amount, total_budget):
    """Send email alert when budget is low"""
    subject = "⚠️ Low Budget Alert - Only 10% Remaining"
    body = f"""
    Your budget has reached a critical level.

    Category: {category}
    Total Budget: ₹{total_budget:.2f}
    Remaining Amount: ₹{remaining_amount:.2f}

    Warning: Your budget has reached a critical level. Only ₹{remaining_amount:.2f} is left.
    Please review your spending and consider adjusting your budget if necessary.
    """
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body
    )
    mail.send(msg)

def create_expense(user_id, amount, category, description, date, group_id=None):
    """Create a new expense and check budget alerts"""
    expense = Expense(
        user_id=user_id,
        amount=amount,
        category=category,
        description=description,
        date=date,
        group_id=group_id
    )
    db.session.add(expense)
    db.session.commit()
    
    # Get user for email notification
    user = User.query.get(user_id)
    
    # Calculate remaining budget
    budget = Budget.query.filter_by(
        user_id=user_id,
        category=category,
        month=date.month,
        year=date.year
    ).first()
    
    if budget:
        # Calculate total expenses for the category in the month
        total_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.category == category,
            func.extract('month', Expense.date) == date.month,
            func.extract('year', Expense.date) == date.year
        ).scalar() or 0
        
        remaining_budget = budget.amount - total_expenses
        
        # Send expense notification
        send_expense_notification(user, expense, remaining_budget)
        
        # Check for low budget alert (10% or less remaining)
        if remaining_budget <= (budget.amount * 0.1):
            send_low_budget_alert(user, category, remaining_budget, budget.amount)
    
    return expense

def set_budget(user_id, category, amount, month, year, period='monthly'):
    """Set or update monthly budget for a category"""
    budget = Budget.query.filter_by(
        user_id=user_id,
        category=category,
        month=month,
        year=year
    ).first()
    
    if budget:
        budget.amount = amount
        budget.period = period
    else:
        budget = Budget(
            user_id=user_id,
            category=category,
            amount=amount,
            month=month,
            year=year,
            period=period
        )
        db.session.add(budget)
    
    db.session.commit()
    
    # Get user for email notification
    user = User.query.get(user_id)
    
    # Calculate current expenses for the category
    current_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        func.extract('month', Expense.date) == month,
        func.extract('year', Expense.date) == year
    ).scalar() or 0
    
    # Send budget notification
    send_budget_notification(user, budget, current_expenses)
    
    return budget

def check_budget_alerts(user_id, category, date):
    """Check if budget alerts should be triggered"""
    month = date.month
    year = date.year
    
    # Get budget for the category
    budget = Budget.query.filter_by(
        user_id=user_id,
        category=category,
        month=month,
        year=year
    ).first()
    
    if not budget:
        return
    
    # Calculate total expenses for the category in the month
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        func.extract('month', Expense.date) == month,
        func.extract('year', Expense.date) == year
    ).scalar() or 0
    
    # Get user for email
    user = User.query.get(user_id)
    
    # Check if budget is exceeded
    if total_expenses > budget.amount:
        send_budget_alert(user, category, total_expenses, budget.amount, "exceeded")
    
    # Check if budget is near limit (90%)
    threshold = budget.amount * (int(current_app.config.get('BUDGET_ALERT_THRESHOLD', 90)) / 100)
    if total_expenses >= threshold and total_expenses < budget.amount:
        send_budget_alert(user, category, total_expenses, budget.amount, "approaching")

def send_budget_alert(user, category, spent, budget, alert_type):
    """Send email alert for budget thresholds"""
    subject = f"Budget Alert: {category}"
    if alert_type == "exceeded":
        body = f"Your {category} budget of ${budget:.2f} has been exceeded. You have spent ${spent:.2f}."
    else:
        body = f"Your {category} budget is approaching the limit. You have spent ${spent:.2f} out of ${budget:.2f}."
    
    msg = Message(
        subject=subject,
        recipients=[user.email],
        body=body
    )
    mail.send(msg)

def get_monthly_report(user_id, month, year):
    """Generate monthly expense report"""
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        func.extract('month', Expense.date) == month,
        func.extract('year', Expense.date) == year
    ).all()
    
    total_spent = sum(expense.amount for expense in expenses)
    category_totals = {}
    
    for expense in expenses:
        if expense.category not in category_totals:
            category_totals[expense.category] = 0
        category_totals[expense.category] += expense.amount
    
    return {
        'total_spent': total_spent,
        'category_totals': category_totals,
        'expenses': [expense.to_dict() for expense in expenses]
    }

def create_group(name, created_by):
    """Create a new expense sharing group"""
    group = Group(name=name, created_by=created_by)
    db.session.add(group)
    db.session.commit()
    return group

def add_expense_to_group(expense_id, group_id):
    """Add an existing expense to a group"""
    expense = Expense.query.get(expense_id)
    if expense:
        expense.group_id = group_id
        db.session.commit()
    return expense

def get_group_balance(group_id):
    """Calculate balances between group members"""
    group = Group.query.get(group_id)
    if not group:
        return None
    
    balances = {}
    for member in group.members:
        balances[member.id] = 0
    
    for expense in group.expenses:
        # Add expense amount to payer's balance
        balances[expense.user_id] += expense.amount
        # Subtract equal share from all members
        share = expense.amount / len(group.members)
        for member in group.members:
            balances[member.id] -= share
    
    return balances

def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        subject = "Welcome to Personal Finance Tracker!"
        body = f"""
        Dear {user.name},

        Welcome to Personal Finance Tracker! We're excited to have you on board.

        Your account has been successfully created. Here's what you can do:

        1. Track your daily expenses
        2. Set monthly budgets for different categories
        3. View detailed reports and charts
        4. Get email notifications for your spending

        Start managing your finances better today!

        Best regards,
        Personal Finance Tracker Team
        """
        
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=body
        )
        
        logger.info(f"Attempting to send welcome email to {user.email}")
        mail.send(msg)
        logger.info(f"Welcome email sent successfully to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        # Don't raise the exception to prevent registration from failing
        # Just log the error and continue

def create_user(email, password, name):
    """Create a new user and send welcome email"""
    try:
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User {email} created successfully")
        
        # Send welcome email
        send_welcome_email(user)
        
        return user
    except Exception as e:
        logger.error(f"Failed to create user {email}: {str(e)}")
        raise  # Re-raise the exception to handle it in the route 