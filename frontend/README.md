# Sign Detector - Vue.js Frontend

## Setup Instructions

### Backend (Flask)
1. Activate virtual environment:
   ```bash
   .venv\Scripts\activate
   ```

2. Install dependencies (if not already installed):
   ```bash
   pip install flask-cors
   ```

3. Run Flask backend:
   ```bash
   python app.py
   ```
   Backend will run on http://localhost:5000

### Frontend (Vue.js)
1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Run Vue development server:
   ```bash
   npm run dev
   ```
   Frontend will run on http://localhost:3000

## Access the Application
Open your browser and go to: **http://localhost:3000**

## Project Structure
```
sign_detector/
├── app.py                 # Flask backend (API)
├── frontend/              # Vue.js frontend
│   ├── src/
│   │   ├── views/        # Page components
│   │   ├── components/   # Reusable components
│   │   ├── api.js        # API service
│   │   ├── router.js     # Vue Router
│   │   └── main.js       # Entry point
│   └── vite.config.js    # Vite configuration
├── static/               # Old static files (can be removed)
└── templates/            # Old templates (can be removed)
```

## Features Implemented
- ✅ Vue 3 with Composition API
- ✅ Vue Router for navigation
- ✅ Axios for API calls
- ✅ Sign Detection with camera feed
- ✅ Speech to Text recognition
- ✅ Authentication (Login/Register)
- ✅ Dark/Light theme toggle
- ✅ Responsive sidebar
- ✅ Gamification stats (XP, Streak)

## Next Steps
Complete the remaining views:
- Profile page with user stats
- History page with detection records
- Learn page with lessons
- Admin panel with user management

All existing JavaScript logic from `static/js/` can be migrated to Vue components.
