import os
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User

def create_admin():
    print("Create Admin User")
    print("=================")

    username = input("Enter admin username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    email = input("Enter admin email: ").strip()
    if not email:
        print("Email cannot be empty.")
        return

    password = input("Enter admin password: ").strip()
    if not password:
        print("Password cannot be empty.")
        return

    confirm_password = input("Confirm admin password: ").strip()
    if password != confirm_password:
        print("Passwords do not match.")
        return

    with app.app_context():
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f'User "{username}" already exists. No changes made.')
            return

        u = User(username=username, email=email, is_admin=True)
        u.set_password(password)

        db.session.add(u)
        db.session.commit()
        print(f'Admin user "{username}" created successfully with email "{email}".')

if __name__ == "__main__":
    create_admin()
