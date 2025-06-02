from app import db
from sqlalchemy import text

def upgrade():
    # Add currency_preference column with default value '$'
    db.session.execute(text('ALTER TABLE user ADD COLUMN currency_preference VARCHAR(10) DEFAULT "$"'))
    db.session.commit()

def downgrade():
    # Remove currency_preference column
    db.session.execute(text('ALTER TABLE user DROP COLUMN currency_preference'))
    db.session.commit() 