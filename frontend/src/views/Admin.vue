<template>
  <Layout>
    <Notification :message="notification.message" :type="notification.type" />
    <Modal
      :show="modal.show"
      :title="modal.title"
      :message="modal.message"
      :type="modal.type"
      :confirmText="modal.confirmText"
      @confirm="modal.onConfirm"
      @cancel="modal.show = false"
    />

    <!-- Hero -->
    <div class="page-hero">
      <div class="hero-icon"><i class="fas fa-cog"></i></div>
      <div>
        <h2>Admin Panel</h2>
        <p>Manage the sign detection model and system settings</p>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#0052cc,#00d4ff)">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_users }}</div>
          <div class="stat-label">Total Users</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#28a745,#38ef7d)">
          <i class="fas fa-hand-paper"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_sign_detections }}</div>
          <div class="stat-label">Sign Detections</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#f7971e,#ffd200)">
          <i class="fas fa-microphone"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_speech_transcriptions }}</div>
          <div class="stat-label">Transcriptions</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#e74c3c,#ff6b6b)">
          <i class="fas fa-calendar-day"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.today_total }}</div>
          <div class="stat-label">Today's Total</div>
        </div>
      </div>
    </div>

    <div v-if="!stats" style="margin-bottom:2rem">
      <button @click="loadStats" class="btn btn-primary">
        <i class="fas fa-sync"></i> Load Statistics
      </button>
    </div>

    <!-- Top Users -->
    <div v-if="stats?.top_users?.length" class="panel" style="margin-bottom:1.5rem">
      <div class="panel-header">
        <span><i class="fas fa-trophy"></i> Most Active Users</span>
        <button @click="loadStats" class="btn btn-sm btn-outline">
          <i class="fas fa-sync"></i> Refresh
        </button>
      </div>
      <div class="panel-body">
        <div v-for="(user, i) in stats.top_users" :key="user.username" class="top-user-row">
          <span class="rank-badge" :class="`rank-${i+1}`">{{ i + 1 }}</span>
          <span class="user-name">{{ user.username }}</span>
          <span class="user-count">{{ user.count }} detections</span>
        </div>
      </div>
    </div>

    <!-- Model Management -->
    <div class="panel" style="margin-bottom:1.5rem">
      <div class="panel-header">
        <span><i class="fas fa-brain"></i> Model Management</span>
      </div>
      <div class="panel-body">
        <p style="color:var(--text-gray);margin-bottom:1rem;font-size:0.9rem">Retrain the sign detection model with new data.</p>
        <div style="display:flex;gap:0.75rem;flex-wrap:wrap">
          <button @click="retrainModel" class="btn btn-primary" :disabled="retraining">
            <i class="fas fa-brain"></i> {{ retraining ? 'Retraining...' : 'Retrain Model' }}
          </button>
          <button @click="checkRetrainStatus" class="btn btn-outline">
            <i class="fas fa-sync"></i> Check Status
          </button>
        </div>
        <div v-if="retrainStatus" class="status-box">
          <div class="status-row">
            <span class="status-label">Status</span>
            <span class="status-pill" :class="retrainStatus.running ? 'running' : 'done'">
              {{ retrainStatus.running ? 'Running' : 'Completed' }}
            </span>
          </div>
          <div class="status-row">
            <span class="status-label">Exit Code</span>
            <span>{{ retrainStatus.last_exit_code }}</span>
          </div>
          <div v-if="retrainStatus.log" class="log-box">{{ retrainStatus.log }}</div>
        </div>
      </div>
    </div>

    <!-- User Management -->
    <div class="panel" style="margin-bottom:1.5rem">
      <div class="panel-header">
        <span><i class="fas fa-users"></i> User Management</span>
        <button @click="loadUsers" class="btn btn-sm btn-outline">
          <i class="fas fa-list"></i> {{ users.length > 0 ? 'Refresh' : 'Load Users' }}
        </button>
      </div>
      <div class="panel-body" style="padding:0">
        <div v-if="users.length === 0" class="empty-state">
          <i class="fas fa-users"></i>
          <p>Click "Load Users" to view all users</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Level</th>
              <th>XP</th>
              <th>Streak</th>
              <th>Admin</th>
              <th>Detections</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td class="muted">{{ user.id }}</td>
              <td><strong>{{ user.username }}</strong></td>
              <td class="muted">{{ user.email }}</td>
              <td><span class="level-pill">Lv {{ user.level }}</span></td>
              <td>{{ user.xp }}</td>
              <td>🔥 {{ user.streak }}</td>
              <td>
                <span class="admin-pill" :class="user.is_admin ? 'yes' : 'no'">
                  {{ user.is_admin ? 'Yes' : 'No' }}
                </span>
              </td>
              <td>{{ user.total_detections }}</td>
              <td>
                <button @click="confirmDeleteUser(user.id, user.username)" class="btn btn-sm btn-danger icon-btn">
                  <i class="fas fa-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Lesson Management -->
    <div class="panel">
      <div class="panel-header">
        <span><i class="fas fa-graduation-cap"></i> Lesson Management</span>
      </div>
      <div class="panel-body">
        <div class="lesson-manage-row">
          <div class="lesson-manage-info">
            <span class="lesson-num">Lesson 4</span>
            <span class="lesson-title-text">Alphabet A-M</span>
          </div>
          <div class="lesson-manage-actions">
            <button @click="confirmUnlockLesson(4)" class="btn btn-sm btn-success">
              <i class="fas fa-unlock"></i> Unlock
            </button>
            <button @click="confirmLockLesson(4)" class="btn btn-sm btn-warning">
              <i class="fas fa-lock"></i> Lock
            </button>
          </div>
        </div>
        <div class="lesson-manage-row">
          <div class="lesson-manage-info">
            <span class="lesson-num">Lesson 5</span>
            <span class="lesson-title-text">Alphabet N-Z</span>
          </div>
          <div class="lesson-manage-actions">
            <button @click="confirmUnlockLesson(5)" class="btn btn-sm btn-success">
              <i class="fas fa-unlock"></i> Unlock
            </button>
            <button @click="confirmLockLesson(5)" class="btn btn-sm btn-warning">
              <i class="fas fa-lock"></i> Lock
            </button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import Notification from '../components/Notification.vue'
import Modal from '../components/Modal.vue'
import api from '../api'

const stats = ref(null)
const users = ref([])
const retraining = ref(false)
const retrainStatus = ref(null)
const notification = ref({ message: '', type: 'success' })
const modal = ref({ show: false, title: '', message: '', type: 'warning', confirmText: 'Confirm', onConfirm: () => {} })

const showNotification = (message, type = 'success') => { notification.value = { message, type } }

const loadStats = async () => {
  try {
    const { data } = await api.getAdminStats()
    stats.value = data
  } catch { showNotification('Error loading stats', 'error') }
}

const loadUsers = async () => {
  try {
    const { data } = await api.getUsers()
    users.value = data.users
  } catch { showNotification('Error loading users', 'error') }
}

const confirmDeleteUser = (id, username) => {
  modal.value = {
    show: true, title: 'Delete User',
    message: `Are you sure you want to delete user "${username}"? This will also delete all their detection history.`,
    type: 'danger', confirmText: 'Delete User', onConfirm: () => deleteUser(id, username)
  }
}

const deleteUser = async (id, username) => {
  modal.value.show = false
  try {
    await api.deleteUser(id)
    showNotification(`User ${username} deleted successfully`)
    await loadUsers()
  } catch { showNotification('Error deleting user', 'error') }
}

const retrainModel = async () => {
  modal.value = {
    show: true, title: 'Retrain Model',
    message: 'Are you sure you want to retrain the model? This may take some time.',
    type: 'warning', confirmText: 'Start Retraining',
    onConfirm: async () => {
      modal.value.show = false
      try {
        retraining.value = true
        const { data } = await api.retrain()
        if (data.status === 'started') {
          showNotification('Model retraining started!')
          checkRetrainStatus()
        } else if (data.status === 'already_running') {
          showNotification('Retraining is already in progress', 'info')
        }
      } catch { showNotification('Error starting retrain', 'error') }
      finally { retraining.value = false }
    }
  }
}

const checkRetrainStatus = async () => {
  try {
    const { data } = await api.getRetrainStatus()
    retrainStatus.value = data
    retraining.value = data.running
  } catch {}
}

const confirmUnlockLesson = (n) => {
  modal.value = {
    show: true, title: 'Unlock Lesson',
    message: `Are you sure you want to unlock Lesson ${n}?`,
    type: 'info', confirmText: 'Unlock', onConfirm: () => unlockLesson(n)
  }
}

const unlockLesson = async (n) => {
  modal.value.show = false
  try {
    const { data } = await api.unlockLesson(n)
    showNotification(data.message || `Lesson ${n} unlocked successfully!`)
  } catch { showNotification('Error unlocking lesson', 'error') }
}

const confirmLockLesson = (n) => {
  modal.value = {
    show: true, title: 'Lock Lesson',
    message: `Are you sure you want to lock Lesson ${n}?`,
    type: 'warning', confirmText: 'Lock', onConfirm: () => lockLesson(n)
  }
}

const lockLesson = async (n) => {
  modal.value.show = false
  try {
    const { data } = await api.lockLesson(n)
    showNotification(data.message || `Lesson ${n} locked successfully!`)
  } catch { showNotification('Error locking lesson', 'error') }
}

onMounted(async () => {
  await loadStats()
  checkRetrainStatus()
})
</script>

<style scoped>
.page-hero {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: linear-gradient(135deg, #6c757d, #495057);
  color: white;
  padding: 1.75rem 2rem;
  border-radius: 20px;
  margin-bottom: 2rem;
}

.hero-icon {
  width: 56px;
  height: 56px;
  background: rgba(255,255,255,0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.page-hero h2 { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
.page-hero p { margin: 0; opacity: 0.85; font-size: 0.9rem; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.stat-value { font-size: 1.75rem; font-weight: 700; color: var(--text-dark); line-height: 1; }
.stat-label { font-size: 0.8rem; color: var(--text-gray); margin-top: 0.2rem; }

.panel {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  overflow: hidden;
  border: 1px solid var(--border);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  background: var(--bg-light);
}

.panel-header i { margin-right: 0.4rem; }
.panel-body { padding: 1.25rem 1.5rem; }

.top-user-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.625rem 0;
  border-bottom: 1px solid var(--border);
}

.top-user-row:last-child { border-bottom: none; }

.rank-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.rank-1 { background: linear-gradient(135deg, #f7971e, #ffd200); }
.rank-2 { background: linear-gradient(135deg, #adb5bd, #6c757d); }
.rank-3 { background: linear-gradient(135deg, #cd7f32, #a0522d); }
.rank-badge:not(.rank-1):not(.rank-2):not(.rank-3) { background: var(--bg-light); color: var(--text-gray); }

.user-name { flex: 1; font-weight: 600; color: var(--text-dark); }
.user-count { font-size: 0.82rem; color: var(--text-gray); }

.status-box {
  margin-top: 1.25rem;
  background: var(--bg-light);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  border: 1px solid var(--border);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.status-label { font-weight: 600; color: var(--text-gray); width: 80px; }

.status-pill {
  padding: 0.2rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
}

.status-pill.running { background: rgba(0,82,204,0.1); color: #0052cc; }
.status-pill.done { background: rgba(40,167,69,0.1); color: #28a745; }

.log-box {
  margin-top: 0.75rem;
  max-height: 180px;
  overflow-y: auto;
  background: var(--bg-card);
  padding: 0.75rem;
  border-radius: 8px;
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--text-dark);
  border: 1px solid var(--border);
  white-space: pre-wrap;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: var(--text-gray);
}

.empty-state i { font-size: 2rem; margin-bottom: 0.5rem; opacity: 0.4; display: block; }
.empty-state p { margin: 0; font-style: italic; font-size: 0.875rem; }

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 0.75rem 1rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-gray);
  border-bottom: 1px solid var(--border);
  background: var(--bg-light);
  white-space: nowrap;
}

.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.875rem;
  color: var(--text-dark);
}

.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--bg-light); }

.muted { color: var(--text-gray); font-size: 0.82rem; }

.level-pill {
  background: rgba(0,82,204,0.1);
  color: #0052cc;
  padding: 0.15rem 0.5rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
}

.admin-pill {
  padding: 0.15rem 0.5rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
}

.admin-pill.yes { background: rgba(40,167,69,0.1); color: #28a745; }
.admin-pill.no { background: var(--bg-light); color: var(--text-gray); }

.icon-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.lesson-manage-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 0;
  border-bottom: 1px solid var(--border);
  gap: 1rem;
}

.lesson-manage-row:last-child { border-bottom: none; }

.lesson-manage-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.lesson-num {
  background: linear-gradient(135deg, #0052cc, #00d4ff);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
}

.lesson-title-text { font-weight: 600; color: var(--text-dark); }

.lesson-manage-actions { display: flex; gap: 0.5rem; }

.btn-success { background: linear-gradient(135deg, #28a745, #38ef7d); color: white; }
.btn-warning { background: linear-gradient(135deg, #f7971e, #ffd200); color: white; }
.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-gray);
}
.btn-outline:hover { border-color: #0052cc; color: #0052cc; }
</style>
