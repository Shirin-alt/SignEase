import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    existing = User.query.filter_by(username='signease').first()
    if existing:
        print('User "signease" already exists.')
        sys.exit(0)

    u = User(username='signease', email='signease@example.com', is_admin=True)
    u.set_password('signease')
    db.session.add(u)
    db.session.commit()
    print('Admin user "signease" created with email "signease@example.com".')
