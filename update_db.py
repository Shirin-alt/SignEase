from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Add preference column to user table
        db.session.execute(text("ALTER TABLE user ADD COLUMN preference VARCHAR(20) DEFAULT 'sign_detection'"))
        print("Added preference column to user table")

        # Add date_joined column to user table
        db.session.execute(text("ALTER TABLE user ADD COLUMN date_joined DATETIME DEFAULT CURRENT_TIMESTAMP"))
        print("Added date_joined column to user table")

        # Create detection_history table
        db.session.execute(text("""
            CREATE TABLE detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sign VARCHAR(50) NOT NULL,
                confidence REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                detection_type VARCHAR(20) DEFAULT 'sign_detection',
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """))
        print("Created detection_history table")

        db.session.commit()
        print("Database update completed successfully!")

    except Exception as e:
        print(f"Error updating database: {e}")
        db.session.rollback()
