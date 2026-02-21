import os
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User

pwd = os.environ.get('ADMIN_PWD')
if not pwd:
    print('ERROR: ADMIN_PWD env var not set. Set it and re-run this script.')
    sys.exit(2)

username = os.environ.get('ADMIN_USER', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')

with app.app_context():
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f'User "{username}" already exists. No changes made.')
        sys.exit(0)

    u = User(username=username, email=email, is_admin=True)
    try:
        u.set_password(pwd)
    except Exception:
        try:
            u.password = pwd
        except Exception:
            pass

    db.session.add(u)
    db.session.commit()
    print(f'Admin user "{username}" created with email "{email}".')
