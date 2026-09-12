import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  timeout: 10000
})

export default {
  // Auth
  login(username, password, remember) {
    return api.post('/login', { username, password, remember })
  },
  register(username, email, password) {
    return api.post('/register', { username, email, password })
  },
  logout() {
    return api.get('/logout')
  },
  googleLogin() {
    window.location.href = '/api/login/google'
  },

  // Detection
  getLatest() {
    return api.get('/latest')
  },
  saveDetection(sign, confidence) {
    return api.post('/save_detection', { sign, confidence })
  },
  getHistoryData() {
    return api.get('/history_data')
  },

  // Speech
  recognizeSpeech(audioBlob, language = 'en') {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    formData.append('language', language)
    return api.post('/speech_recognize', formData)
  },
  saveTranscription(text) {
    return api.post('/save_transcription', { text })
  },
  getSignVideo(text) {
    return api.post('/get_sign_video', { text })
  },

  // Profile
  updateUsername(username) {
    return api.post('/update_username', { username })
  },
  updatePreference(preference) {
    return api.post('/update_preference', { preference })
  },
  syncProgress(data) {
    return api.post('/sync_progress', data)
  },
  updateStreak() {
    return api.post('/update_streak')
  },
  getLeaderboard() {
    return api.get('/leaderboard')
  },
  setDetectionMode(mode) {
    return api.post('/set_mode', { mode })
  },

  // History
  getHistoryData() {
    return api.get('/history_data')
  },
  clearAllHistory(detectionType) {
    return api.delete(`/clear_all_history/${detectionType}`)
  },
  deleteDetection(id) {
    return api.delete(`/delete_detection/${id}`)
  },

  // Admin
  getUsers() {
    return api.get('/admin/users')
  },
  deleteUser(id) {
    return api.delete(`/admin/users/${id}`)
  },
  getAdminStats() {
    return api.get('/admin/stats')
  },
  unlockLesson(lessonNumber) {
    return api.post(`/admin/unlock_lesson/${lessonNumber}`)
  },
  lockLesson(lessonNumber) {
    return api.post(`/admin/lock_lesson/${lessonNumber}`)
  },
  retrain() {
    return api.post('/retrain')
  },
  getRetrainStatus() {
    return api.get('/retrain_status')
  },

  // Chat Rooms
  createRoom() {
    return api.post('/room/create')
  },
  joinRoom(code) {
    return api.post('/room/join', { code })
  },
  getRoomMessages(code) {
    return api.get(`/room/${code}/messages`)
  }
}
