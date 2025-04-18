# Personal Finance Tracker

A comprehensive web application for tracking personal finances, managing budgets, and monitoring spending patterns.

## Features

- **Expense Tracking**: Record and categorize your daily expenses
- **Budget Management**: Set monthly budgets for different spending categories
- **Visual Reports**: View your spending patterns with interactive charts and graphs
- **Multi-category Support**: Organize expenses by categories such as Food, Transportation, Housing, etc.
- **Data Visualization**: Pie charts and trend analysis for better financial insights

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (file-based database)
- **ORM**: SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js
- **Authentication**: Flask-Login

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Web browser (Chrome, Firefox, Safari, or Edge)

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-folder>
```

### 2. Create a Virtual Environment

#### For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file to set up:
- A secret key for session security
- Email configuration (optional for budget alerts)
- Database location (default is an SQLite file in the instance folder)

### 5. Run the Application

```bash
python run.py
```

The application will start and be accessible at:
```
http://127.0.0.1:5000
```

## Usage Guide

### Getting Started

1. **Registration/Login**:
   - Create a new account or log in with existing credentials

2. **Adding Expenses**:
   - Navigate to the "Expenses" page
   - Click "Add Expense" and fill in the details:
     - Amount
     - Category
     - Description (optional)
     - Date

3. **Setting Budgets**:
   - Go to the "Budgets" page
   - Click "Set Budget" to create a budget:
     - Select a category
     - Enter the budget amount
     - Choose the period (YYYY-MM format)

4. **Viewing Reports**:
   - Visit the "Reports" page
   - Select report type:
     - Category Breakdown (pie chart)
     - Expense Trends (line chart)
     - Budget vs Actual (bar chart)
   - Choose a date range for the report

### Managing Data

- **Edit/Delete Expenses**: Use the action buttons in the expense table
- **Batch Delete**: Select multiple expenses using checkboxes and delete them at once
- **Update Budgets**: Click the edit icon next to any budget to modify it

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Ensure Python is properly installed and in your PATH
   - Verify that all dependencies are installed (`pip install -r requirements.txt`)
   - Check if another application is using port 5000

2. **Database errors**:
   - Delete the instance folder if there's a database schema mismatch
   - The application will recreate the database on next start

3. **Chart display issues**:
   - Try clearing your browser cache
   - Ensure you have at least one expense for the selected time period

## Developer Notes

- The application uses SQLite by default, which stores data in a file
- Data is persisted between application restarts
- The database file is created in the `instance` folder automatically

## License

This project is licensed under the MIT License - see the LICENSE file for details. 