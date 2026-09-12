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
      <div class="hero-icon"><i class="fas fa-history"></i></div>
      <div>
        <h2>Conversation History</h2>
        <p>Your sign and speech conversation log</p>
      </div>
    </div>

    <!-- Panel -->
    <div class="panel">
      <div class="panel-header">
        <span><i class="fas fa-comments"></i> Conversation</span>
        <div class="panel-actions">
          <button v-if="conversation.length > 0" @click="printHistory" class="btn btn-sm btn-print">
            <i class="fas fa-print"></i> Print
          </button>
          <button v-if="signHistory.length > 0" @click="confirmClearAll('sign_detection')" class="btn btn-sm btn-danger">
            <i class="fas fa-hand-paper"></i> Clear Signs
          </button>
          <button v-if="speechHistory.length > 0" @click="confirmClearAll('speech_to_text')" class="btn btn-sm btn-danger">
            <i class="fas fa-microphone"></i> Clear Speech
          </button>
        </div>
      </div>
      <div class="panel-body chat-body">
        <div v-if="conversation.length === 0" class="empty-state">
          <i class="fas fa-comments"></i>
          <p>No conversation history yet</p>
        </div>
        <div v-else class="chat-list">
          <div
            v-for="item in conversation"
            :key="item.id"
            class="chat-row"
            :class="item.type === 'speech_to_text' ? 'chat-right' : 'chat-left'"
          >
            <div class="chat-avatar" v-if="item.type === 'sign_detection'">
              <i class="fas fa-hand-paper"></i>
            </div>
            <div class="chat-bubble-wrap">
              <div class="chat-bubble" :class="item.type === 'speech_to_text' ? 'bubble-right' : 'bubble-left'">
                <span class="bubble-text">{{ item.sign }}</span>
                <span class="bubble-conf" v-if="item.type === 'sign_detection'">{{ Math.round(item.confidence * 100) }}%</span>
              </div>
              <div class="bubble-meta" :class="item.type === 'speech_to_text' ? 'meta-right' : 'meta-left'">
                <span>{{ formatDate(item.timestamp) }}</span>
                <button @click="confirmDelete(item.id)" class="btn-delete no-print"><i class="fas fa-trash"></i></button>
              </div>
            </div>
            <div class="chat-avatar" v-if="item.type === 'speech_to_text'">
              <i class="fas fa-microphone"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '../components/Layout.vue'
import Notification from '../components/Notification.vue'
import Modal from '../components/Modal.vue'
import api from '../api'

const signHistory = ref([])
const speechHistory = ref([])
const conversation = ref([])
const notification = ref({ message: '', type: 'success' })
const modal = ref({ show: false, title: '', message: '', type: 'warning', confirmText: 'Confirm', onConfirm: () => {} })

const showNotification = (message, type = 'success') => { notification.value = { message, type } }

const loadHistory = async () => {
  try {
    const response = await fetch('/api/history', { headers: { 'Accept': 'application/json' }, credentials: 'include' })
    const data = await response.json()
    signHistory.value = data.sign_history || []
    speechHistory.value = data.speech_history || []
    conversation.value = [...signHistory.value, ...speechHistory.value]
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  } catch {
    showNotification('Error loading history', 'error')
  }
}

const confirmDelete = (id) => {
  modal.value = {
    show: true, title: 'Delete Item',
    message: 'Are you sure you want to delete this item? This action cannot be undone.',
    type: 'danger', confirmText: 'Delete', onConfirm: () => deleteItem(id)
  }
}

const deleteItem = async (id) => {
  modal.value.show = false
  try {
    await api.deleteDetection(id)
    await loadHistory()
    showNotification('Item deleted successfully')
  } catch { showNotification('Error deleting item', 'error') }
}

const confirmClearAll = (type) => {
  const name = type === 'sign_detection' ? 'sign detection' : 'speech transcription'
  modal.value = {
    show: true, title: 'Clear All History',
    message: `Are you sure you want to clear all ${name} history? This action cannot be undone.`,
    type: 'danger', confirmText: 'Clear All', onConfirm: () => clearAll(type)
  }
}

const clearAll = async (type) => {
  modal.value.show = false
  try {
    await api.clearAllHistory(type)
    await loadHistory()
    showNotification('History cleared successfully')
  } catch { showNotification('Error clearing history', 'error') }
}

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('en-PH', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

// --- Print ---
const printHistory = () => {
  const rows = conversation.value.map(item => {
    const isSign = item.type === 'sign_detection'
    const side = isSign ? 'left' : 'right'
    const label = isSign ? '🤟 Sign (Kausap)' : '🎤 Speech (Ikaw)'
    const conf = isSign ? Math.round(item.confidence * 100) + '%' : ''
    return `<div class="msg ${side}"><div class="bubble"><span class="label">${label}</span><span class="text">${item.sign}</span>${conf ? `<span class="conf">${conf}</span>` : ''}<span class="time">${formatDate(item.timestamp)}</span></div></div>`
  }).join('')

  const win = window.open('', '_blank')
  win.document.write(`<!DOCTYPE html><html><head><title>Conversation History</title><style>
    body{font-family:Arial,sans-serif;padding:2rem;background:#f5f5f5;}
    h1{font-size:1.3rem;margin-bottom:0.25rem;}
    .meta{color:#555;font-size:0.82rem;margin-bottom:1.5rem;}
    .msg{display:flex;margin-bottom:0.75rem;}
    .msg.left{justify-content:flex-start;}
    .msg.right{justify-content:flex-end;}
    .bubble{max-width:60%;padding:0.6rem 1rem;border-radius:16px;font-size:0.9rem;display:flex;flex-direction:column;gap:0.2rem;}
    .msg.left .bubble{background:#fff;border:1px solid #ddd;border-bottom-left-radius:4px;}
    .msg.right .bubble{background:#0052cc;color:#fff;border-bottom-right-radius:4px;}
    .label{font-size:0.7rem;font-weight:700;opacity:0.6;}
    .text{font-weight:600;font-size:1rem;}
    .conf{font-size:0.72rem;opacity:0.7;}
    .time{font-size:0.7rem;opacity:0.55;}
    .footer{margin-top:2rem;font-size:0.78rem;color:#777;border-top:1px solid #ccc;padding-top:0.75rem;}
  </style></head><body>
    <h1>Conversation History</h1>
    <div class="meta">Printed on: ${new Date().toLocaleString('en-PH')} &nbsp;|&nbsp; Total: ${conversation.value.length} messages</div>
    ${rows}
    <div class="footer">Generated from the Sign Language Detection System.</div>
  </body></html>`)
  win.document.close()
  win.focus()
  setTimeout(() => win.print(), 400)
}

onMounted(loadHistory)
</script>

<style scoped>
.page-hero {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: linear-gradient(135deg, #6f42c1, #a855f7);
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
.panel-body { padding: 0; }

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-gray);
}

.empty-state i { font-size: 2.5rem; margin-bottom: 0.75rem; opacity: 0.4; display: block; }
.empty-state p { margin: 0; font-style: italic; }

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  padding: 0.75rem 1.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-gray);
  border-bottom: 1px solid var(--border);
  background: var(--bg-light);
}

.data-table td {
  padding: 0.875rem 1.5rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
  color: var(--text-dark);
}

.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--bg-light); }

.panel-actions { display: flex; gap: 0.5rem; align-items: center; }

.btn-print {
  background: linear-gradient(135deg, #0052cc, #00d4ff);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.chat-body { padding: 1rem 1.5rem; }

.chat-list { display: flex; flex-direction: column; gap: 0.75rem; }

.chat-row {
  display: flex;
  align-items: flex-end;
  gap: 0.6rem;
}

.chat-row.chat-right { flex-direction: row-reverse; }

.chat-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--bg-light);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  color: var(--text-gray);
  flex-shrink: 0;
}

.chat-bubble-wrap { display: flex; flex-direction: column; max-width: 60%; }

.chat-bubble {
  padding: 0.6rem 1rem;
  border-radius: 18px;
  font-size: 0.95rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  word-break: break-word;
}

.bubble-left {
  background: var(--bg-light);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  color: var(--text-dark);
}

.bubble-right {
  background: linear-gradient(135deg, #0052cc, #00d4ff);
  border-bottom-right-radius: 4px;
  color: white;
}

.bubble-conf {
  font-size: 0.72rem;
  opacity: 0.6;
  font-weight: 400;
}

.bubble-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.25rem;
  font-size: 0.72rem;
  color: var(--text-gray);
}

.meta-right { justify-content: flex-end; }
.meta-left { justify-content: flex-start; }

.btn-delete {
  background: none;
  border: none;
  color: var(--text-gray);
  cursor: pointer;
  font-size: 0.7rem;
  padding: 0;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.btn-delete:hover { opacity: 1; color: #e53e3e; }

@media print {
  .no-print { display: none !important; }
}
</style>
