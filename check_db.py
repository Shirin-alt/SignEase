from app import app, db

with app.app_context():
    # Check current user table schema
    result = db.session.execute(db.text('PRAGMA table_info(user)'))
    columns = result.fetchall()
    print('Current user table columns:')
    for col in columns:
        print(f'  {col[1]}: {col[2]}')

    # Check if detection_history table exists
    result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='detection_history'"))
    table_exists = result.fetchone()
    print(f'\nDetection_history table exists: {table_exists is not None}')
