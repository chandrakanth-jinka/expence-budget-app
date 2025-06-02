from app import create_app, db
from migrations.add_currency_preference import upgrade

app = create_app()

with app.app_context():
    try:
        upgrade()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {str(e)}") 