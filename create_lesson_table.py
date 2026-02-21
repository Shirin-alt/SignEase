import sys
sys.path.insert(0, '.')

try:
    from app import app, db
    from app import LessonModule
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating table directly...")
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from datetime import datetime
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/sign_language_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    
    class LessonModule(db.Model):
        __tablename__ = 'lesson_modules'
        id = db.Column(db.Integer, primary_key=True)
        lesson_number = db.Column(db.Integer, unique=True, nullable=False)
        title = db.Column(db.String(100), nullable=False)
        is_unlocked = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    print("Lesson modules table created successfully!")
