from flask import Flask, render_template, Response, jsonify, redirect, url_for, flash, request, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import threading
import subprocess
import os
import time
from datetime import datetime
import cv2
import warnings

# Suppress SQLAlchemy 2.0 deprecation warnings (LegacyAPIWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='sqlalchemy')
warnings.filterwarnings('ignore', message='.*LegacyAPIWarning.*')

# Import your Detector class
from detect_signs import Detector

# Import speech recognizer
from speech_recognizer import get_whisper_recognizer

# --- Basic App Configuration ---
app = Flask(__name__)
# IMPORTANT: Change this to a random secret key
app.config['SECRET_KEY'] = 'a_very_secret_key_that_is_long_and_random'
# Configuration for SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost/sign_language_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# database tables
with app.app_context():
    db.create_all()

# --- Database Models ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)
    is_admin = db.Column(db.Boolean(), nullable=True)
    preference = db.Column(db.String(20), default='sign_detection')
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class DetectionHistory(db.Model):
    __tablename__ = 'detection_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sign = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    detection_type = db.Column(db.String(20), default='sign_detection')  # 'sign_detection' or 'speech_to_text'

class LessonModule(db.Model):
    __tablename__ = 'lesson_modules'
    id = db.Column(db.Integer, primary_key=True)
    lesson_number = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    is_unlocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- WTForms Classes ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class PreferenceForm(FlaskForm):
    preference = StringField('Preference', validators=[DataRequired()])
    submit = SubmitField('Update')

# --- Initialize Camera Check First ---
camera_available = False
try:
    print("[App] Checking camera availability...")
    test_camera = cv2.VideoCapture(0)
    if test_camera.isOpened():
        camera_available = True
        print("[App] Camera test successful")
    else:
        print("[App] Camera test failed - could not open VideoCapture")
    test_camera.release()
    import time
    time.sleep(0.2)  # Small delay to ensure camera fully releases
    print(f"[App] Camera available: {camera_available}")
except Exception as e:
    print(f"[App] Camera check failed with exception: {e}")
    camera_available = False

# --- Detector Setup ---
# We initialize a single detector instance for the app.
# Pre-initialize the detector to avoid delays when user accesses sign detection
detector = None
detector_lock = threading.Lock()

def get_detector():
    global detector
    with detector_lock:
        if detector is None:
            if not camera_available:
                print("[App] Camera not available, sign detection will not work")
                return None
            # Detector does not depend on the database; create without passing db.
            print("[App] Initializing sign detector...")
            detector = Detector()
            print("[App] Sign detector ready!")
        return detector

# Pre-initialize detector on app startup
def initialize_detector_on_startup():
    """Initialize detector on app startup to avoid delays on first access"""
    try:
        print("[App] Pre-initializing sign detector on startup...")
        detector = get_detector()
        if detector is None:
            print("[App] Detector is None, camera unavailable")
            return
        # Give camera time to warm up
        import time
        time.sleep(2)
        print("[App] Sign detector fully warmed up and ready!")
    except Exception as e:
        print(f"[App] Warning: Could not pre-initialize detector: {e}")
        import traceback
        traceback.print_exc()

# Initialize after app context ONLY if not in debug reloader
import os
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    # Main process, not debug reloader child
    with app.app_context():
        initialize_detector_on_startup()

# --- Routes ---
@app.route('/')
@app.route('/home')
@login_required
def index():
    preference = current_user.preference if hasattr(current_user, 'preference') and current_user.preference else 'sign_detection'
    return render_template('index.html', title='Dashboard', user_preference=preference)

@app.route('/test')
def test():
    return 'Hello World! The app is working.'

@app.route('/video_feed')
@login_required
def video_feed():
    # This endpoint streams MJPEG frames for live video feed
    # Optimize for minimal latency with aggressive no-cache headers
    detector = get_detector()
    if detector is None:
        print("[App] /video_feed called but detector is None (camera unavailable)")
        return jsonify({'error': 'Camera not available'}), 503
    
    response = Response(detector.generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable proxy buffering
    response.headers['Connection'] = 'keep-alive'
    response.headers['Transfer-Encoding'] = 'chunked'
    return response

@app.route('/test_frame')
@login_required
def test_frame():
    """Return a single JPEG frame to test camera access"""
    try:
        det = get_detector()
        if det.frame is None:
            return jsonify({'error': 'No frame available yet'}), 503
        
        frame = det.frame.copy()
        processed = det._process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', processed, [cv2.IMWRITE_JPEG_QUALITY, 70])
        
        if not ret:
            return jsonify({'error': 'Failed to encode frame'}), 500
        
        return Response(buffer.tobytes(), mimetype='image/jpeg')
    except Exception as e:
        print(f"[App] /test_frame error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_detector')
@login_required
def check_detector():
    """Check if detector is ready for sign detection"""
    global detector
    try:
        det = get_detector()
        has_frame = det.frame is not None and det.ret
        return jsonify({
            'status': 'ready', 
            'initialized': True,
            'has_frame': has_frame,
            'frame_count': det.frame_count if hasattr(det, 'frame_count') else 0
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e), 'initialized': False}), 500

@app.route('/latest')
@login_required
def latest():
    # Return the most recent detection as JSON
    return jsonify(get_detector().get_latest())

@app.route('/save_detection', methods=['POST'])
@login_required
def save_detection():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'})

    sign = data.get('sign')
    confidence = data.get('confidence', 0.0)
    detection_type = current_user.preference or 'sign_detection'

    if sign:
        detection = DetectionHistory(
            user_id=current_user.id,
            sign=sign,
            confidence=float(confidence),
            detection_type=detection_type
        )
        db.session.add(detection)
        db.session.commit()
        return jsonify({'status': 'saved'})
    else:
        return jsonify({'status': 'error', 'message': 'No sign provided'})

@app.route('/sync_progress', methods=['POST'])
@login_required
def sync_progress():
    data = request.get_json()
    if data:
        from datetime import datetime, timedelta
        
        current_user.xp = data.get('xp', 0)
        current_user.level = data.get('level', 1)
        
        # Calculate streak
        today = datetime.utcnow().date()
        if current_user.last_active:
            last_active_date = current_user.last_active.date()
            days_diff = (today - last_active_date).days
            
            if days_diff == 0:
                # Same day, keep streak
                pass
            elif days_diff == 1:
                # Next day, increment streak
                current_user.streak = data.get('streak', 0)
            else:
                # Missed days, reset streak
                current_user.streak = 1
        else:
            # First time, start streak
            current_user.streak = 1
        
        current_user.last_active = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'synced', 'streak': current_user.streak})
    return jsonify({'status': 'error'})

@app.route('/history_data')
@login_required
def history_data():
    from datetime import datetime, timedelta

    detection_type = current_user.preference or 'sign_detection'

    # Get today's detections
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_today = DetectionHistory.query.filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == detection_type,
        DetectionHistory.timestamp >= today_start
    ).count()

    # Get recent history (last 10)
    recent_history = DetectionHistory.query.filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == detection_type
    ).order_by(DetectionHistory.timestamp.desc()).limit(10).all()

    history_data = []
    for record in recent_history:
        history_data.append({
            'sign': record.sign,
            'confidence': record.confidence,
            'timestamp': record.timestamp.strftime('%H:%M:%S'),
            'date': record.timestamp.strftime('%Y-%m-%d')
        })

    return jsonify({
        'total_today': total_today,
        'history': history_data
    })

@app.route('/save_transcription', methods=['POST'])
@login_required
def save_transcription():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'})

    text = data.get('text')
    if text:
        detection = DetectionHistory(
            user_id=current_user.id,
            sign=text,
            confidence=1.0,  # Speech recognition is considered 100% confident
            detection_type='speech_to_text'
        )
        db.session.add(detection)
        db.session.commit()
        return jsonify({'status': 'saved'})
    else:
        return jsonify({'status': 'error', 'message': 'No text provided'})

@app.route('/latest_transcription')
@login_required
def latest_transcription():
    # Get the most recent speech-to-text detection
    latest = DetectionHistory.query.filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == 'speech_to_text'
    ).order_by(DetectionHistory.timestamp.desc()).first()

    if latest:
        return jsonify({
            'text': latest.sign,
            'timestamp': latest.timestamp.isoformat()
        })
    else:
        return jsonify({'text': None})

@app.route('/speech_recognize', methods=['POST'])
@login_required
def speech_recognize():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    try:
        recognizer = get_whisper_recognizer()
        # Use None for language to enable auto-detection (better for Taglish)
        # Or specify 'tl' for Tagalog, 'en' for English, or None for auto-detect
        result = recognizer.transcribe_audio(audio_data, language=None)
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        return jsonify({
            'text': result['text'],
            'language': result['language'],
            'confidence': result['confidence']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/learn')
@login_required
def learn():
    unlocked_lessons = {1: True, 2: True, 3: True}
    lesson_4 = LessonModule.query.filter_by(lesson_number=4).first()
    if lesson_4 and lesson_4.is_unlocked:
        unlocked_lessons[4] = True
    lesson_5 = LessonModule.query.filter_by(lesson_number=5).first()
    if lesson_5 and lesson_5.is_unlocked:
        unlocked_lessons[5] = True
    return render_template('learn.html', title='Learn', unlocked_lessons=unlocked_lessons)

@app.route('/profile')
@login_required
def profile():
    from sqlalchemy import func

    # Get statistics based on user preference
    detection_type = current_user.preference or 'sign_detection'

    # Total detections for this user and preference
    total_detections = DetectionHistory.query.filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == detection_type
    ).count()

    # Most common sign/word
    most_common = db.session.query(
        DetectionHistory.sign,
        func.count(DetectionHistory.sign).label('count')
    ).filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == detection_type
    ).group_by(DetectionHistory.sign).order_by(func.count(DetectionHistory.sign).desc()).first()

    most_common_sign = most_common[0] if most_common else 'N/A'

    form = PreferenceForm()
    form.preference.data = current_user.preference or 'sign_detection'
    return render_template('profile.html', title='Profile',
                         total_detections=total_detections,
                         most_common_sign=most_common_sign,
                         form=form)

@app.route('/update_preference', methods=['POST'])
@login_required
def update_preference():
    preference = request.form.get('preference')
    if preference in ['sign_detection', 'speech_to_text']:
        current_user.preference = preference
        db.session.commit()
        
        # Pre-initialize detector if switching to sign detection
        if preference == 'sign_detection':
            try:
                print(f"[App] Pre-loading detector for user {current_user.username}...")
                detector = get_detector()  # This will initialize if not already done
                # Give camera a moment to warmup if just initialized
                import time
                time.sleep(0.5)
                print(f"[App] Detector ready for user {current_user.username}")
            except Exception as e:
                print(f"[App] Error pre-loading detector: {e}")
        
        flash('Your preference has been updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/history')
@login_required
def history():
    # Fetch both sign detection and speech-to-text history for current user
    sign_history = DetectionHistory.query.filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == 'sign_detection'
    ).order_by(DetectionHistory.timestamp.desc()).all()

    speech_history = DetectionHistory.query.filter(
        DetectionHistory.user_id == current_user.id,
        DetectionHistory.detection_type == 'speech_to_text'
    ).order_by(DetectionHistory.timestamp.desc()).all()

    return render_template('history.html',
                         title='History',
                         sign_history=sign_history,
                         speech_history=speech_history)

@app.route('/clear_all_history/<detection_type>', methods=['DELETE'])
@login_required
def clear_all_history(detection_type):
    try:
        if detection_type not in ['sign_detection', 'speech_to_text']:
            return jsonify({'error': 'Invalid detection type'}), 400
        
        DetectionHistory.query.filter_by(
            user_id=current_user.id,
            detection_type=detection_type
        ).delete()
        db.session.commit()
        
        return jsonify({'message': 'All history cleared successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to clear history'}), 500

@app.route('/delete_detection/<int:detection_id>', methods=['DELETE'])
@login_required
def delete_detection(detection_id):
    """Delete a detection history record"""
    try:
        # Find the detection record
        detection = DetectionHistory.query.get(detection_id)
        
        # Check if detection exists
        if not detection:
            return jsonify({'error': 'Detection not found'}), 404
        
        # Check if the detection belongs to the current user
        if detection.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete the detection
        db.session.delete(detection)
        db.session.commit()
        
        print(f"[App] Deleted detection {detection_id} for user {current_user.id}")
        return jsonify({'message': 'Detection deleted successfully'}), 200
    
    except Exception as e:
        print(f"[App] Error deleting detection: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete detection'}), 500

@app.route('/admin/unlock_lesson/<int:lesson_number>', methods=['POST'])
@login_required
def unlock_lesson(lesson_number):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        lesson = LessonModule.query.filter_by(lesson_number=lesson_number).first()
        if not lesson:
            lesson = LessonModule(lesson_number=lesson_number, title=f'Lesson {lesson_number}', is_unlocked=True)
            db.session.add(lesson)
        else:
            lesson.is_unlocked = True
        db.session.commit()
        return jsonify({'message': f'Lesson {lesson_number} unlocked successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lock_lesson/<int:lesson_number>', methods=['POST'])
@login_required
def lock_lesson(lesson_number):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        lesson = LessonModule.query.filter_by(lesson_number=lesson_number).first()
        if lesson:
            lesson.is_unlocked = False
            db.session.commit()
        return jsonify({'message': f'Lesson {lesson_number} locked successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    return render_template('admin.html', title='Admin Panel')

 

# --- Model Management (Admin Only) ---
retrain_lock = threading.Lock()
retrain_thread = None
retrain_status = {"running": False, "last_exit_code": None, "log": ""}

def _run_retrain():
    global retrain_status
    retrain_status.update({"running": True, "last_exit_code": None, "log": ""})
    try:
        py = os.environ.get('PYTHON', 'python')
        proc = subprocess.Popen([py, 'train_model.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.getcwd())
        out_lines = []
        for line in proc.stdout:
            out_lines.append(line)
        proc.wait()
        retrain_status["last_exit_code"] = int(proc.returncode)
        retrain_status["log"] = "".join(out_lines)
        try:
            get_detector().reload_model()
        except Exception as e:
            retrain_status["log"] += f"\nError reloading model: {e}"
    except Exception as e:
        retrain_status["log"] = f"Exception: {e}\n"
        retrain_status["last_exit_code"] = -1
    finally:
        retrain_status["running"] = False

@app.route('/retrain', methods=["POST"])
@login_required
def retrain():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    global retrain_thread
    if retrain_status.get("running"):
        return jsonify({"status": "already_running"}), 409
    t = threading.Thread(target=_run_retrain, daemon=True)
    retrain_thread = t
    t.start()
    return jsonify({"status": "started"})

@app.route('/retrain_status')
@login_required
def retrain_status_route():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(retrain_status)

@app.route('/download_model')
@login_required
def download_model():
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('profile'))
    model_path = 'sign_classifier.p'
    if os.path.exists(model_path):
        return send_file(model_path, as_attachment=True)
    return jsonify({"error": "model_not_found"}), 404

# --- Admin User Management ---
@app.route('/admin/users')
@login_required
def admin_users():
    """Get all users with their detection counts"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        users = User.query.all()
        users_data = []
        
        for user in users:
            # Get detection count for each user
            sign_count = DetectionHistory.query.filter_by(
                user_id=user.id, 
                detection_type='sign_detection'
            ).count()
            
            speech_count = DetectionHistory.query.filter_by(
                user_id=user.id, 
                detection_type='speech_to_text'
            ).count()
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'preference': user.preference,
                'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else None,
                'sign_detections': sign_count,
                'speech_transcriptions': speech_count,
                'total_detections': sign_count + speech_count,
                'level': user.level,
                'xp': user.xp,
                'streak': user.streak
            })
        
        return jsonify({'users': users_data})
    except Exception as e:
        print(f"[App] Error fetching users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def admin_delete_user(user_id):
    """Delete a user and their detection history"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Prevent admin from deleting themselves
        if user_id == current_user.id:
            return jsonify({'error': 'You cannot delete your own account'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user's detection history first
        DetectionHistory.query.filter_by(user_id=user_id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        print(f"[App] Admin {current_user.username} deleted user {user_id} ({user.username})")
        return jsonify({'message': f'User {user.username} deleted successfully'})
    except Exception as e:
        print(f"[App] Error deleting user: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/stats')
@login_required
def admin_stats():
    """Get system-wide statistics"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from sqlalchemy import func
        
        total_users = User.query.count()
        total_sign_detections = DetectionHistory.query.filter_by(detection_type='sign_detection').count()
        total_speech_transcriptions = DetectionHistory.query.filter_by(detection_type='speech_to_text').count()
        total_detections = total_sign_detections + total_speech_transcriptions
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sign_detections = DetectionHistory.query.filter(
            DetectionHistory.detection_type == 'sign_detection',
            DetectionHistory.timestamp >= today_start
        ).count()
        
        today_speech_transcriptions = DetectionHistory.query.filter(
            DetectionHistory.detection_type == 'speech_to_text',
            DetectionHistory.timestamp >= today_start
        ).count()
        
        top_users = db.session.query(
            User.username,
            func.count(DetectionHistory.id).label('detection_count')
        ).join(DetectionHistory).group_by(User.id, User.username).order_by(
            func.count(DetectionHistory.id).desc()
        ).limit(5).all()
        
        top_signs = db.session.query(
            DetectionHistory.sign,
            func.count(DetectionHistory.id).label('count')
        ).filter(
            DetectionHistory.detection_type == 'sign_detection'
        ).group_by(DetectionHistory.sign).order_by(
            func.count(DetectionHistory.id).desc()
        ).limit(10).all()
        
        leaderboard_xp = User.query.order_by(User.xp.desc()).limit(10).all()
        leaderboard_streak = User.query.order_by(User.streak.desc()).limit(10).all()
        
        return jsonify({
            'total_users': total_users,
            'total_sign_detections': total_sign_detections,
            'total_speech_transcriptions': total_speech_transcriptions,
            'total_detections': total_detections,
            'today_sign_detections': today_sign_detections,
            'today_speech_transcriptions': today_speech_transcriptions,
            'today_total': today_sign_detections + today_speech_transcriptions,
            'top_users': [{'username': u[0], 'count': u[1]} for u in top_users],
            'top_signs': [{'sign': s[0], 'count': s[1]} for s in top_signs],
            'leaderboard_xp': [{'username': u.username, 'xp': u.xp, 'level': u.level} for u in leaderboard_xp],
            'leaderboard_streak': [{'username': u.username, 'streak': u.streak} for u in leaderboard_streak]
        })
    except Exception as e:
        print(f"[App] Error fetching admin stats: {e}")
        return jsonify({'error': str(e)}), 500

# --- Clean up when shutting down ---
def release_resources():
    try:
        if detector:
            detector.stop()
            detector.release()
    except:
        pass

import atexit
import webbrowser
import threading

atexit.register(release_resources)

def _open_browser_later():
    try:
        url = os.environ.get('APP_URL', 'http://127.0.0.1:5000/login')
        print(f"[App] Opening browser at {url}")
        # small delay to allow the server to start
        webbrowser.open_new_tab(url)
    except Exception as e:
        print(f"[App] Failed to open browser: {e}")

if __name__ == '__main__':
    # Schedule browser to open shortly after the server starts
    threading.Timer(1.0, _open_browser_later).start()
    print('[App] Starting Flask server on http://127.0.0.1:5000')
    app.run(debug=True, use_reloader=False)