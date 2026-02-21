from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Backup existing users
        result = db.session.execute(text("SELECT id, username, email, password_hash, is_admin, preference FROM user"))
        users = result.fetchall()

        print(f"Found {len(users)} users to backup")

        # Drop and recreate user table with correct schema
        db.session.execute(text("DROP TABLE IF EXISTS user"))
        db.session.execute(text("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(20) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128),
                is_admin BOOLEAN,
                preference VARCHAR(20) DEFAULT 'sign_detection',
                date_joined DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Restore users
        for user in users:
            db.session.execute(text("""
                INSERT INTO user (id, username, email, password_hash, is_admin, preference, date_joined)
                VALUES (:id, :username, :email, :password_hash, :is_admin, :preference, CURRENT_TIMESTAMP)
            """), {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'password_hash': user[3],
                'is_admin': user[4],
                'preference': user[5]
            })

        # Ensure detection_history table exists with all columns
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sign VARCHAR(50) NOT NULL,
                confidence REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                detection_type VARCHAR(20) DEFAULT 'sign_detection',
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """))

        # Add detection_type column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE detection_history ADD COLUMN detection_type VARCHAR(20) DEFAULT 'sign_detection'"))
        except:
            pass  # Column might already exist

        db.session.commit()
        print("Database schema fixed successfully!")

    except Exception as e:
        print(f"Error fixing database: {e}")
        db.session.rollback()
