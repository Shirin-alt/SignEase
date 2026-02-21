from app import app, db, User, DetectionHistory

with app.app_context():
    # Check if test user exists
    user = User.query.filter_by(username='testuser').first()
    print(f'Test user exists: {user is not None}')

    if not user:
        print('Creating test user...')
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        print('Test user created')

    # Test saving a detection
    print('Testing save detection...')
    detection = DetectionHistory(
        user_id=user.id,
        sign='hello',
        confidence=0.95,
        detection_type='sign_detection'
    )
    db.session.add(detection)
    db.session.commit()
    print('Detection saved successfully')

    # Check total detections
    total = DetectionHistory.query.filter_by(user_id=user.id).count()
    print(f'Total detections for user: {total}')

    print('Database tests completed successfully!')
