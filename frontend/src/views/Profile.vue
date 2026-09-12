<template>
  <Layout>
    <Notification :message="notification.message" :type="notification.type" />

    <!-- Hero -->
    <div class="page-hero">
      <div class="avatar-circle">{{ usernameInitial }}</div>
      <div>
        <h2>{{ username }}</h2>
        <p>{{ email }}</p>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#0052cc,#00d4ff)">
          <i class="fas fa-hand-paper"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ totalSigns }}</div>
          <div class="stat-label">Total Signs</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#28a745,#38ef7d)">
          <i class="fas fa-bullseye"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ accuracy }}%</div>
          <div class="stat-label">Accuracy</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#f7971e,#ffd200)">
          <i class="fas fa-fire"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ streak }}</div>
          <div class="stat-label">Day Streak</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:linear-gradient(135deg,#6f42c1,#a855f7)">
          <i class="fas fa-clock"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ practiceTime }}m</div>
          <div class="stat-label">Practice Time</div>
        </div>
      </div>
    </div>

    <!-- Account Info -->
    <div class="panel">
      <div class="panel-header">
        <span><i class="fas fa-user-circle"></i> Account Info</span>
      </div>
      <div class="panel-body">
        <div class="info-row">
          <span class="info-label">Username</span>
          <div v-if="!editingUsername" class="info-value">
            {{ username }}
            <button @click="startEdit" class="btn btn-sm btn-outline">
              <i class="fas fa-edit"></i> Edit
            </button>
          </div>
          <div v-else class="edit-row">
            <input v-model="newUsername" type="text" class="form-control" placeholder="New username" style="max-width:260px">
            <button @click="saveUsername" class="btn btn-sm btn-primary" :disabled="!newUsername.trim()">
              <i class="fas fa-save"></i> Save
            </button>
            <button @click="cancelEdit" class="btn btn-sm btn-outline">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div class="info-row">
          <span class="info-label">Email</span>
          <span class="info-value">{{ email }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Favorite Sign</span>
          <span class="info-value">{{ favoriteSign }}</span>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import Notification from '../components/Notification.vue'
import api from '../api'

const username = ref(localStorage.getItem('username') || '')
const email = ref(localStorage.getItem('email') || '')
const streak = ref(parseInt(localStorage.getItem('streak') || 0))
const totalSigns = ref(0)
const accuracy = ref(95)
const practiceTime = ref(30)
const favoriteSign = ref('N/A')
const editingUsername = ref(false)
const newUsername = ref('')
const notification = ref({ message: '', type: 'success' })

const usernameInitial = computed(() => (username.value || '?')[0].toUpperCase())

const showNotification = (message, type = 'success') => {
  notification.value = { message, type }
}

const startEdit = () => {
  newUsername.value = username.value
  editingUsername.value = true
}

const saveUsername = async () => {
  if (!newUsername.value.trim()) { showNotification('Username cannot be empty', 'error'); return }
  try {
    await api.updateUsername(newUsername.value)
    username.value = newUsername.value
    localStorage.setItem('username', newUsername.value)
    editingUsername.value = false
    showNotification('Username updated successfully!')
  } catch (error) {
    showNotification(error.response?.data?.error || 'Error updating username', 'error')
  }
}

const cancelEdit = () => { editingUsername.value = false; newUsername.value = '' }

onMounted(async () => {
  try {
    const { data } = await api.getHistoryData()
    totalSigns.value = data.total_today || 0
  } catch {}
})
</script>

<style scoped>
.page-hero {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  background: linear-gradient(135deg, #0052cc, #00d4ff);
  color: white;
  padding: 2rem;
  border-radius: 20px;
  margin-bottom: 2rem;
}

.avatar-circle {
  width: 72px;
  height: 72px;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  flex-shrink: 0;
  backdrop-filter: blur(10px);
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
  align-items: center;
  padding: 1rem 1.5rem;
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  background: var(--bg-light);
}

.panel-header i { margin-right: 0.4rem; }
.panel-body { padding: 0.5rem 0; }

.info-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1.5rem;
  border-bottom: 1px solid var(--border);
}

.info-row:last-child { border-bottom: none; }

.info-label {
  width: 120px;
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-gray);
  flex-shrink: 0;
}

.info-value {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-dark);
  font-size: 0.9rem;
}

.edit-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-gray);
}

.btn-outline:hover {
  border-color: #0052cc;
  color: #0052cc;
}
</style>
