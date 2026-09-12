<template>
  <Layout>
    <template #header>
      <div class="conv-header-label">
        <i class="fas fa-comments"></i> Conversation
      </div>
    </template>

    <!-- ── SELECT (mode picker) ── -->
    <div v-if="view === 'select'" class="select-wrapper">
      <h2 class="select-title">Choose a Mode</h2>
      <div class="select-cards">
        <div class="mode-card" @click="enterSolo">
          <i class="fas fa-user"></i>
          <span class="mode-card-title">Solo Practice</span>
          <span class="mode-card-sub">Practice signing on your own, no internet required.</span>
        </div>
        <div class="mode-card" @click="view = 'lobby'">
          <i class="fas fa-door-open"></i>
          <span class="mode-card-title">Conversation Room</span>
          <span class="mode-card-sub">Join or create a room to chat with others in real time.</span>
        </div>
      </div>
    </div>

    <!-- ── LOBBY ── -->
    <div v-else-if="view === 'lobby'" class="lobby-wrapper">
      <div class="lobby-card">
        <h2 class="lobby-title"><i class="fas fa-door-open"></i> Conversation Room</h2>
        <p class="lobby-sub">Choose your role, then create or join a room.</p>

        <!-- Role Picker -->
        <div class="role-picker">
          <button :class="['role-btn', { active: role === 'deaf' }]" @click="role = 'deaf'">
            <i class="fas fa-hand-paper"></i>
            <span>Sign Language</span>
          </button>
          <button :class="['role-btn', { active: role === 'hearing' }]" @click="role = 'hearing'">
            <i class="fas fa-microphone"></i>
            <span>Speech / Typing</span>
          </button>
        </div>

        <button class="btn-primary" @click="createRoom" :disabled="lobbyLoading">
          <i class="fas fa-plus"></i> Create Room
        </button>

        <div class="lobby-divider">or</div>

        <div class="join-row">
          <input
            v-model="joinCode"
            class="join-input"
            placeholder="Enter room code"
            maxlength="10"
            @keyup.enter="joinRoom"
          />
          <button class="btn-primary" @click="joinRoom" :disabled="!joinCode || lobbyLoading">
            <i class="fas fa-sign-in-alt"></i> Join
          </button>
        </div>

        <p v-if="lobbyError" class="lobby-error">{{ lobbyError }}</p>

        <button class="btn-back" @click="view = 'select'">
          <i class="fas fa-arrow-left"></i> Back
        </button>
      </div>
    </div>

    <!-- ── SOLO ── -->
    <div v-else-if="view === 'solo'" class="conv-wrapper">

      <!-- ── LEFT: Camera Panel (always shown in solo) ── -->
      <div class="cam-panel">
        <div class="cam-top-bar">
          <span class="cam-title"><i class="fas fa-hand-paper"></i> Sign Detection</span>
          <span class="live-badge">● LIVE</span>
        </div>

        <div class="cam-frame">
          <video ref="videoRef" class="camera-source" autoplay muted playsinline></video>
          <img v-if="useServerCamera" class="server-camera-source" :src="SERVER_FEED_URL" alt="Live camera feed">
          <canvas ref="canvasRef" width="640" height="480" class="cam-canvas"></canvas>
          <div v-if="cameraError" class="camera-error">{{ cameraError }}</div>
          <div class="det-badge" v-if="latestSign">
            <span class="det-sign">{{ latestSign }}</span>
            <span class="det-conf">{{ latestConf }}%</span>
          </div>
        </div>

        <div class="cam-bottom-bar">
          <div class="det-mode-toggle">
            <button
              :class="['det-btn', { active: detectionMode === 'alphabet' }]"
              @click="switchMode('alphabet')">
              <i class="fas fa-font"></i> Alphabet
            </button>
            <button
              :class="['det-btn', { active: detectionMode === 'phrase' }]"
              @click="switchMode('phrase')">
              <i class="fas fa-hands"></i> Phrase
            </button>
          </div>
          <button class="btn-send-sign" @click="manualSendSign" :disabled="!currentSign">
            <i class="fas fa-paper-plane"></i> Send
          </button>
        </div>
      </div>

      <!-- ── RIGHT: Chat Panel ── -->
      <div class="chat-panel">
        <div class="chat-top-bar">
          <span class="chat-title">
            <i class="fas fa-comment-dots"></i>
            <template v-if="view === 'solo'">Solo Practice</template>
            <template v-else>Room: <code>{{ roomCode }}</code></template>
          </span>
          <button v-if="view === 'solo'" class="btn-back" @click="exitSolo"><i class="fas fa-arrow-left"></i> Exit</button>
          <button v-else class="btn-leave" @click="leaveRoom"><i class="fas fa-sign-out-alt"></i> Leave</button>
          <button class="btn-clear" @click="clearChat"><i class="fas fa-trash"></i></button>
        </div>

        <div class="chat-body" ref="chatBody">
          <div v-if="messages.length === 0" class="chat-empty">
            <i class="fas fa-sign-language"></i>
            <p>Start signing or speaking to begin!</p>
          </div>

          <div
            v-for="(msg, i) in messages"
            :key="i"
            :class="['bubble', msg.type === 'sign' ? 'bubble-sign' : msg.type === 'fsl_video' || msg.type === 'fsl_spell' ? 'bubble-sign' : (msg.self ? 'bubble-speech' : 'bubble-remote')]">
            <!-- FSL video bubble -->
            <template v-if="msg.type === 'fsl_video'">
              <span class="bubble-label">🤟 FSL: {{ msg.matched }}</span>
              <video :src="BACKEND_URL + msg.video" autoplay loop muted playsinline style="width:100%;max-width:200px;border-radius:10px;margin-top:4px;"></video>
              <span class="bubble-time">{{ msg.time }}</span>
            </template>
            <!-- FSL fingerspell bubble -->
            <template v-else-if="msg.type === 'fsl_spell'">
              <span class="bubble-label">🤟 FSL Fingerspell</span>
              <div class="fingerspell-row">
                <img v-for="f in msg.letters" :key="f.letter" :src="BACKEND_URL + f.image" :title="f.letter.toUpperCase()" @error="$event.target.style.display='none'">
              </div>
              <span class="bubble-time">{{ msg.time }}</span>
            </template>
            <!-- Normal text bubble -->
            <template v-else>
              <span class="bubble-label">{{ msg.type === 'sign' ? '🤟 Kausap' : (msg.self ? '🎤 You' : '👤 ' + msg.sender) }}</span>
              <span class="bubble-text">{{ msg.text }}</span>
              <span v-if="msg.sub" class="bubble-sub">{{ msg.sub }}</span>
              <!-- Inline FSL translation -->
              <template v-if="msg.fsl">
                <span class="bubble-fsl-label">🤟 FSL{{ msg.fsl.fslType === 'video' ? ': ' + msg.fsl.matched : ' Fingerspell' }}</span>
                <video v-if="msg.fsl.fslType === 'video'" :src="BACKEND_URL + msg.fsl.video" autoplay loop muted playsinline class="bubble-fsl-video"></video>
                <div v-else class="fingerspell-row">
                  <img v-for="f in msg.fsl.letters" :key="f.letter" :src="BACKEND_URL + f.image" :title="f.letter.toUpperCase()" @error="$event.target.style.display='none'">
                </div>
              </template>
              <span class="bubble-time">{{ msg.time }}</span>
            </template>
          </div>

          <div v-if="pendingLetters" class="bubble bubble-sign pending-sign">
            <span class="bubble-label">🤟 Detected sign</span>
            <span class="bubble-text">{{ pendingLetters }}</span>
            <span class="bubble-sub">Building word...</span>
          </div>

          <div v-if="processing" class="bubble bubble-speech processing">
            <span class="bubble-label">🎤 You</span>
            <span class="bubble-text"><i class="fas fa-spinner fa-spin"></i> Processing...</span>
          </div>
        </div>

        <div class="chat-input">
          <div v-if="isRecording" class="rec-status">
            <span class="rec-dot"></span> Recording...
          </div>
          <div class="input-row">
            <div class="lang-select-wrap">
              <select v-model="selectedLang" class="lang-select">
                <option value="en">EN</option>
                <option value="tl">TL</option>
              </select>
            </div>
            <button :class="['btn-mic', { recording: isRecording }]" @click="toggleSpeech">
              <i :class="isRecording ? 'fas fa-stop' : 'fas fa-microphone'"></i>
            </button>
            <input
              v-model="soloText"
              class="solo-text-input"
              placeholder="Reply via speech or type..."
              @keyup.enter="sendText"
            />
            <button class="btn-send-text" @click="sendText" :disabled="!soloText.trim()">
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>

    </div>

    <!-- ── ROOM ── -->
    <div v-else-if="view === 'room'" class="conv-wrapper">

      <!-- ── LEFT: Camera Panel (deaf role only) ── -->
      <div class="cam-panel" v-if="role === 'deaf'">
        <div class="cam-top-bar">
          <span class="cam-title"><i class="fas fa-hand-paper"></i> Sign Detection</span>
          <span class="live-badge">● LIVE</span>
        </div>

        <div class="cam-frame">
          <video ref="videoRef" class="camera-source" autoplay muted playsinline></video>
          <img v-if="useServerCamera" class="server-camera-source" :src="SERVER_FEED_URL" alt="Live camera feed">
          <canvas ref="canvasRef" width="640" height="480" class="cam-canvas"></canvas>
          <div v-if="cameraError" class="camera-error">{{ cameraError }}</div>
          <div class="det-badge" v-if="latestSign">
            <span class="det-sign">{{ latestSign }}</span>
            <span class="det-conf">{{ latestConf }}%</span>
          </div>
        </div>

        <div class="cam-bottom-bar">
          <div class="det-mode-toggle">
            <button :class="['det-btn', { active: detectionMode === 'alphabet' }]" @click="switchMode('alphabet')">
              <i class="fas fa-font"></i> Alphabet
            </button>
            <button :class="['det-btn', { active: detectionMode === 'phrase' }]" @click="switchMode('phrase')">
              <i class="fas fa-hands"></i> Phrase
            </button>
          </div>
          <button class="btn-send-sign" @click="manualSendSign" :disabled="!currentSign">
            <i class="fas fa-paper-plane"></i> Send
          </button>
        </div>
      </div>

      <!-- ── RIGHT: Chat Panel ── -->
      <div class="chat-panel">
        <div class="chat-top-bar">
          <span class="chat-title">
            <i class="fas fa-comment-dots"></i> Room: <code>{{ roomCode }}</code>
          </span>
          <!-- Role switcher -->
          <div class="role-toggle">
            <button :class="['role-toggle-btn', { active: role === 'deaf' }]" @click="switchRole('deaf')">
              <i class="fas fa-hand-paper"></i>
            </button>
            <button :class="['role-toggle-btn', { active: role === 'hearing' }]" @click="switchRole('hearing')">
              <i class="fas fa-microphone"></i>
            </button>
          </div>
          <button class="btn-leave" @click="leaveRoom"><i class="fas fa-sign-out-alt"></i> Leave</button>
          <button class="btn-clear" @click="clearChat"><i class="fas fa-trash"></i></button>
        </div>

        <div class="chat-body" ref="chatBody">
          <div v-if="messages.length === 0" class="chat-empty">
            <i class="fas fa-sign-language"></i>
            <p>Start signing or speaking to begin!</p>
          </div>

          <div
            v-for="(msg, i) in messages"
            :key="i"
            :class="['bubble', msg.type === 'sign' ? 'bubble-sign' : msg.type === 'fsl_video' || msg.type === 'fsl_spell' ? 'bubble-sign' : (msg.self ? 'bubble-speech' : 'bubble-remote')]">
            <!-- FSL video bubble -->
            <template v-if="msg.type === 'fsl_video'">
              <span class="bubble-label">🤟 FSL: {{ msg.matched }}</span>
              <video :src="BACKEND_URL + msg.video" autoplay loop muted playsinline style="width:100%;max-width:200px;border-radius:10px;margin-top:4px;"></video>
              <span class="bubble-time">{{ msg.time }}</span>
            </template>
            <!-- FSL fingerspell bubble -->
            <template v-else-if="msg.type === 'fsl_spell'">
              <span class="bubble-label">🤟 FSL Fingerspell</span>
              <div class="fingerspell-row">
                <img v-for="f in msg.letters" :key="f.letter" :src="BACKEND_URL + f.image" :title="f.letter.toUpperCase()" @error="$event.target.style.display='none'">
              </div>
              <span class="bubble-time">{{ msg.time }}</span>
            </template>
            <!-- Normal text bubble -->
            <template v-else>
              <span class="bubble-label">{{ msg.self ? (msg.type === 'sign' ? '🤟 You (Sign)' : '🎤 You') : '👤 ' + msg.sender }}</span>
              <span class="bubble-text">{{ msg.text }}</span>
              <span v-if="msg.sub" class="bubble-sub">{{ msg.sub }}</span>
              <!-- Inline FSL translation -->
              <template v-if="msg.fsl">
                <span class="bubble-fsl-label">🤟 FSL{{ msg.fsl.fslType === 'video' ? ': ' + msg.fsl.matched : ' Fingerspell' }}</span>
                <video v-if="msg.fsl.fslType === 'video'" :src="BACKEND_URL + msg.fsl.video" autoplay loop muted playsinline class="bubble-fsl-video"></video>
                <div v-else class="fingerspell-row">
                  <img v-for="f in msg.fsl.letters" :key="f.letter" :src="BACKEND_URL + f.image" :title="f.letter.toUpperCase()" @error="$event.target.style.display='none'">
                </div>
              </template>
              <span class="bubble-time">{{ msg.time }}</span>
            </template>
          </div>

          <div v-if="pendingLetters" class="bubble bubble-sign pending-sign">
            <span class="bubble-label">🤟 Detected sign</span>
            <span class="bubble-text">{{ pendingLetters }}</span>
            <span class="bubble-sub">Building word...</span>
          </div>

          <div v-if="processing" class="bubble bubble-speech processing">
            <span class="bubble-label">🎤 You</span>
            <span class="bubble-text"><i class="fas fa-spinner fa-spin"></i> Processing...</span>
          </div>
        </div>

        <div class="chat-input">
          <div v-if="role === 'hearing'">
            <div v-if="isRecording" class="rec-status">
              <span class="rec-dot"></span> Recording...
            </div>
            <div class="input-row">
              <div class="lang-select-wrap">
                <select v-model="selectedLang" class="lang-select">
                  <option value="en">EN</option>
                  <option value="tl">TL</option>
                </select>
              </div>
              <button :class="['btn-mic', { recording: isRecording }]" @click="toggleSpeech">
                <i :class="isRecording ? 'fas fa-stop' : 'fas fa-microphone'"></i>
              </button>
              <input
                v-model="soloText"
                class="solo-text-input"
                placeholder="Type a message..."
                @keyup.enter="sendText"
              />
              <button class="btn-send-text" @click="sendText" :disabled="!soloText.trim()">
                <i class="fas fa-paper-plane"></i>
              </button>
            </div>
          </div>
          <div v-else class="input-hint">
            <i class="fas fa-hand-paper"></i> Signs are auto-detected and sent.
            <span class="role-hint">Switch to <i class="fas fa-microphone"></i> to type/speak.</span>
          </div>
        </div>
      </div>

    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { io } from 'socket.io-client'
import Layout from '../components/Layout.vue'
import api from '../api'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:5000`
const SERVER_FEED_URL = '/video_feed'

// ── Lobby state ───────────────────────────────────────────────────────
const view        = ref('select')
const joinCode    = ref('')
const roomCode    = ref('')
const lobbyLoading = ref(false)
const lobbyError  = ref('')
const role        = ref('hearing')

// ── Room / chat state ─────────────────────────────────────────────────
const canvasRef    = ref(null)
const videoRef     = ref(null)
const cameraError  = ref('')
const useServerCamera = ref(['localhost', '127.0.0.1'].includes(window.location.hostname))
const chatBody     = ref(null)
const messages     = ref([])
const pendingLetters = ref('')
const latestSign   = ref('')
const latestConf   = ref(0)
const isRecording  = ref(false)
const processing   = ref(false)
const selectedLang = ref('en')
const detectionMode = ref('alphabet')
const currentSign  = ref(null)
const soloText     = ref('')

let lastSignTimestamp = null
let isSwitching       = false
let pollInterval      = null
let frameInterval     = null
let cameraStream      = null
let captureCanvas     = null
let mediaRecorder     = null
let audioChunks       = []
let socket            = null
let sessionId         = null
let sessionLabel      = ''

// ── Letter buffer for fingerspelling ─────────────────────────────────
let letterBuffer      = []
let letterFlushTimer  = null
const LETTER_FLUSH_MS = 2000  // flush after 2s of no new letter

function flushLetterBuffer() {
  if (!letterBuffer.length) {
    pendingLetters.value = ''
    return
  }
  const word = letterBuffer.join('')
  letterBuffer = []
  pendingLetters.value = ''
  const sub = `(Fingerspelled)`
  addMessage(word, 'sign', sub)
  if (view.value === 'room') emitMessage(word, 'sign', sub)
  api.saveDetection(word, 1.0).catch(() => {})
  if (window.Gamification) window.Gamification.addXP(10)
}

function bufferLetter(letter, conf) {
  letterBuffer.push(letter.toUpperCase())
  pendingLetters.value = letterBuffer.join('')
  scrollDown()
  // Reset flush timer on each new letter
  clearTimeout(letterFlushTimer)
  letterFlushTimer = setTimeout(flushLetterBuffer, LETTER_FLUSH_MS)
}

const PHRASE_KEYS = [
  'hi','good_morning','good_afternoon','good_evening',
  'how_are_you','i_am_fine','i_am_not_fine',
  'whats_your_name','my_name_is','sorry','thank_you'
]

// ── Helpers ───────────────────────────────────────────────────────────
function nowTime() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

async function scrollDown() {
  await nextTick()
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

function addMessage(text, type, sub = '', self = true, sender = '') {
  messages.value.push({ text, type, sub, self, sender, time: nowTime() })
  scrollDown()
}

function saveSession() {
  if (!sessionId || !messages.value.length) return
  const sessions = JSON.parse(localStorage.getItem('conv_sessions') || '[]')
  const existing = sessions.findIndex(s => s.id === sessionId)
  const entry = { id: sessionId, label: sessionLabel, messages: messages.value }
  if (existing >= 0) sessions[existing] = entry
  else sessions.unshift(entry)
  localStorage.setItem('conv_sessions', JSON.stringify(sessions.slice(0, 50)))
}

// ── Socket ────────────────────────────────────────────────────────────
function connectSocket(code) {
  socket = io(BACKEND_URL, { withCredentials: true })

  socket.on('connect', () => {
    socket.emit('join_room', { room: code })
  })

  socket.on('chat_message', async (msg) => {
    // Ignore own echoes; the sender already rendered its local message.
    if (msg.self) return
    const remoteMessage = {
      text: msg.text,
      type: msg.type,
      sub: msg.sub || '',
      self: false,
      sender: msg.sender || 'Partner',
      time: nowTime(),
      fsl: null
    }
    messages.value.push(remoteMessage)
    scrollDown()

    // Translate remote speech/typing for the deaf participant too.
    if (msg.type === 'speech' && msg.text) {
      remoteMessage.fsl = await showSignForText(msg.text)
      scrollDown()
    }
  })
}

function emitMessage(text, type, sub = '') {
  if (!socket?.connected) return
  socket.emit('chat_message', { room: roomCode.value, text, type, sub })
}

// ── Lobby actions ─────────────────────────────────────────────────────
async function createRoom() {
  lobbyLoading.value = true
  lobbyError.value = ''
  try {
    const { data } = await api.createRoom()
    enterRoom(data.code)
  } catch (e) {
    lobbyError.value = e.response?.data?.error || 'Failed to create room.'
  }
  lobbyLoading.value = false
}

async function joinRoom() {
  if (!joinCode.value) return
  lobbyLoading.value = true
  lobbyError.value = ''
  try {
    const { data } = await api.joinRoom(joinCode.value.trim())
    enterRoom(data.code)
  } catch (e) {
    lobbyError.value = e.response?.data?.error || 'Room not found.'
  }
  lobbyLoading.value = false
}

function enterRoom(code) {
  roomCode.value = code
  messages.value = []
  lastSignTimestamp = null
  sessionId = Date.now().toString()
  sessionLabel = `Kwarto ${code} — ${new Date().toLocaleString('fil-PH', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`
  view.value = 'room'
  connectSocket(code)
  if (role.value === 'deaf') {
    startCamera()
    pollInterval  = setInterval(fetchLatest, 350)
    frameInterval = setInterval(fetchFrame, 100)
  }
}

function switchRole(newRole) {
  if (role.value === newRole) return
  role.value = newRole
  stopSpeech()
  if (newRole === 'deaf') {
    startCamera()
    if (!pollInterval)  pollInterval  = setInterval(fetchLatest, 350)
    if (!frameInterval) frameInterval = setInterval(fetchFrame, 100)
  } else {
    stopCamera()
    clearInterval(pollInterval)
    clearInterval(frameInterval)
    pollInterval = frameInterval = null
    latestSign.value = ''
    latestConf.value = 0
    currentSign.value = null
  }
}

function leaveRoom() {
  flushLetterBuffer()
  saveSession()
  clearInterval(pollInterval)
  clearInterval(frameInterval)
  clearTimeout(letterFlushTimer)
  letterBuffer = []
  pollInterval = frameInterval = null
  stopSpeech()
  stopCamera()
  socket?.disconnect()
  socket = null
  roomCode.value = ''
  joinCode.value = ''
  messages.value = []
  latestSign.value = ''
  latestConf.value = 0
  currentSign.value = null
  sessionId = null
  view.value = 'lobby'
}

function enterSolo() {
  messages.value = []
  lastSignTimestamp = null
  sessionId = Date.now().toString()
  sessionLabel = `Solo — ${new Date().toLocaleString('fil-PH', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`
  view.value = 'solo'
  startCamera()
  pollInterval  = setInterval(fetchLatest, 350)
  frameInterval = setInterval(fetchFrame, 100)
}

function exitSolo() {
  flushLetterBuffer()
  saveSession()
  clearInterval(pollInterval)
  clearInterval(frameInterval)
  clearTimeout(letterFlushTimer)
  letterBuffer = []
  pollInterval = frameInterval = null
  stopSpeech()
  stopCamera()
  messages.value = []
  latestSign.value = ''
  latestConf.value = 0
  currentSign.value = null
  soloText.value = ''
  sessionId = null
  view.value = 'select'
}

async function showSignForText(text) {
  try {
    const { data } = await api.getSignVideo(text)
    if (data.video) {
      return { fslType: 'video', video: data.video, matched: data.matched }
    } else if (data.fingerspell?.length) {
      return { fslType: 'spell', letters: data.fingerspell }
    }
  } catch {}
  return null
}

async function sendText() {
  const text = soloText.value.trim()
  if (!text) return
  const msg = { text, type: 'speech', sub: '', self: true, sender: '', time: nowTime(), fsl: null }
  messages.value.push(msg)
  scrollDown()
  if (view.value === 'room') emitMessage(text, 'speech')
  api.saveTranscription(text).catch(() => {})
  soloText.value = ''
  const fsl = await showSignForText(text)
  if (fsl) { msg.fsl = fsl; scrollDown() }
}

// ── Camera frame polling ──────────────────────────────────────────────
async function fetchFrame() {
  if (!canvasRef.value || !videoRef.value || videoRef.value.readyState < 2) return
  try {
    if (!captureCanvas) captureCanvas = document.createElement('canvas')
    captureCanvas.width = videoRef.value.videoWidth || 640
    captureCanvas.height = videoRef.value.videoHeight || 480
    captureCanvas.getContext('2d').drawImage(videoRef.value, 0, 0, captureCanvas.width, captureCanvas.height)
    const frameBlob = await new Promise(resolve => captureCanvas.toBlob(resolve, 'image/jpeg', 0.75))
    if (!frameBlob) return
    const formData = new FormData()
    formData.append('frame', frameBlob, 'camera.jpg')
    const res = await fetch('/process_frame', { method: 'POST', body: formData, credentials: 'include' })
    if (!res.ok) return
    const ct = res.headers.get('content-type')
    if (!ct?.includes('image')) return
    const blob = await res.blob()
    if (!blob.size) return
    const img = new Image()
    img.onload = () => {
      const ctx = canvasRef.value?.getContext('2d')
      if (ctx) ctx.drawImage(img, 0, 0, 640, 480)
      URL.revokeObjectURL(img.src)
    }
    img.src = URL.createObjectURL(blob)
  } catch {}
}

async function startCamera() {
  await nextTick()
  if (useServerCamera.value) return
  if (cameraStream || !videoRef.value) return
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = 'Camera requires HTTPS or localhost.'
    useServerCamera.value = true
    return
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    })
    videoRef.value.srcObject = cameraStream
    await videoRef.value.play()
    cameraError.value = ''
    useServerCamera.value = false
  } catch (e) {
    cameraError.value = `Camera unavailable: ${e.message}`
    useServerCamera.value = true
  }
}

function stopCamera() {
  cameraStream?.getTracks().forEach(track => track.stop())
  cameraStream = null
  if (videoRef.value) videoRef.value.srcObject = null
}

// ── Sign detection polling ────────────────────────────────────────────
async function fetchLatest() {
  if (isSwitching || (role.value !== 'deaf' && view.value !== 'solo')) return
  try {
    const { data } = await api.getLatest()
    if (data.mode && data.mode !== detectionMode.value) return

    if (data.sign && data.conf >= 0.70) {
      const display  = data.display || data.sign.toUpperCase()
      const conf     = Math.round(data.conf * 100)
      const isPhrase = PHRASE_KEYS.includes(data.sign)

      if (detectionMode.value === 'alphabet' && isPhrase) return
      if (detectionMode.value === 'phrase'   && !isPhrase) return

      latestSign.value = display
      latestConf.value = conf
      currentSign.value = { sign: data.sign, display, conf, filipino: data.filipino, timestamp: data.timestamp }

      // Dedup: only send if backend timestamp changed (new detection event)
      const ts = data.timestamp ?? null
      if (ts && ts !== lastSignTimestamp) {
        lastSignTimestamp = ts
        if (detectionMode.value === 'alphabet') {
          // Buffer letters — flush to one bubble after 2s pause
          bufferLetter(data.sign)
        } else {
          const sub = data.filipino ? `(${data.filipino})` : ''
          addMessage(display, 'sign', sub)
          if (view.value === 'room') emitMessage(display, 'sign', sub)
          api.saveDetection(data.sign, data.conf).catch(() => {})
          if (window.Gamification) window.Gamification.addXP(10)
        }
      }
    } else {
      latestSign.value = ''
      latestConf.value = 0
      currentSign.value = null
    }
  } catch {}
}

// ── Manual send sign ──────────────────────────────────────────────────
function manualSendSign() {
  if (!currentSign.value) return
  const { sign, display, conf, filipino } = currentSign.value
  const sub = filipino ? `(${filipino})` : ''
  addMessage(display, 'sign', sub)
  if (view.value === 'room') emitMessage(display, 'sign', sub)
  api.saveDetection(sign, conf / 100).catch(() => {})
}

// ── Switch detection mode ─────────────────────────────────────────────
async function switchMode(mode) {
  if (detectionMode.value === mode) return
  isSwitching = true
  detectionMode.value = mode
  latestSign.value = ''
  latestConf.value = 0
  currentSign.value = null
  lastSignTimestamp = null
  clearTimeout(letterFlushTimer)
  letterBuffer = []
  try { await api.setDetectionMode(mode) } catch {}
  await new Promise(r => setTimeout(r, 700))
  isSwitching = false
}

// ── Speech recording ──────────────────────────────────────────────────
async function toggleSpeech() {
  isRecording.value ? stopSpeech() : await startSpeech()
}

async function startSpeech() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mime = ['audio/webm;codecs=opus','audio/webm','audio/mp4','']
      .find(m => !m || MediaRecorder.isTypeSupported(m))
    mediaRecorder = new MediaRecorder(stream, mime ? { mimeType: mime } : {})
    audioChunks = []

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data)
    mediaRecorder.onstop = async () => {
      isRecording.value = false
      stream.getTracks().forEach(t => t.stop())
      const blob = new Blob(audioChunks, { type: mime || 'audio/webm' })
      if (!blob.size) return
      processing.value = true
      scrollDown()
      try {
        const { data } = await api.recognizeSpeech(blob, selectedLang.value)
        if (data.text) {
          const msg = { text: data.text, type: 'speech', sub: '', self: true, sender: '', time: nowTime(), fsl: null }
          messages.value.push(msg)
          scrollDown()
          if (view.value === 'room') emitMessage(data.text, 'speech')
          api.saveTranscription(data.text).catch(() => {})
          if (window.Gamification) window.Gamification.addXP(5)
          const fsl = await showSignForText(data.text)
          if (fsl) { msg.fsl = fsl; scrollDown() }
        }
      } catch {}
      processing.value = false
    }

    mediaRecorder.start()
    isRecording.value = true
  } catch (e) {
    alert('Microphone error: ' + e.message)
  }
}

function stopSpeech() {
  if (mediaRecorder?.state === 'recording') mediaRecorder.stop()
}

// ── Clear chat ────────────────────────────────────────────────────────
function clearChat() {
  messages.value = []
  lastSignTimestamp = null
}

// ── Lifecycle ─────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const { data } = await api.updateStreak()
    localStorage.setItem('streak', data.streak)
    window.dispatchEvent(new Event('streakUpdated'))
  } catch {}
})

onUnmounted(() => {
  flushLetterBuffer()
  clearInterval(pollInterval)
  clearInterval(frameInterval)
  clearTimeout(letterFlushTimer)
  stopSpeech()
  stopCamera()
  socket?.disconnect()
})
</script>

<style scoped>
.conv-header-label {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-dark);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.camera-source {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.server-camera-source {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ── Select (mode picker) ── */
.select-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 96px);
  gap: 1.5rem;
}

.select-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-dark);
  margin: 0;
}

.select-cards {
  display: flex;
  gap: 1.5rem;
}

.mode-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2.5rem 2rem;
  width: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: transform 0.18s, box-shadow 0.18s;
  text-align: center;
}
.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,82,204,0.18);
}
.mode-card i { font-size: 2.2rem; color: #0052cc; }
.mode-card-title { font-size: 1.05rem; font-weight: 700; color: var(--text-dark); }
.mode-card-sub { font-size: 0.82rem; color: var(--text-gray); }

/* ── Back button ── */
.btn-back {
  padding: 0.35rem 0.8rem;
  background: var(--bg-light);
  color: var(--text-dark);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: background 0.2s;
}
.btn-back:hover { background: var(--border); }

/* ── Lobby ── */
.lobby-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 96px);
}

.lobby-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: var(--shadow-md);
}

.lobby-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--text-dark);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.lobby-sub {
  font-size: 0.88rem;
  color: var(--text-gray);
  margin: 0;
}

.role-picker {
  display: flex;
  gap: 0.5rem;
}

.role-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  padding: 0.85rem 0.5rem;
  border: 2px solid var(--border);
  border-radius: 12px;
  background: var(--bg-light);
  color: var(--text-gray);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.role-btn i { font-size: 1.3rem; }
.role-btn.active {
  border-color: #0052cc;
  background: rgba(0,82,204,0.08);
  color: #0052cc;
}

.role-toggle {
  display: flex;
  gap: 0.25rem;
  background: var(--bg-light);
  border-radius: 8px;
  padding: 0.2rem;
  border: 1px solid var(--border);
}

.role-toggle-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  color: var(--text-gray);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.role-toggle-btn.active {
  background: #0052cc;
  color: #fff;
}

.role-hint {
  margin-left: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-gray);
  opacity: 0.7;
}

.lobby-divider {
  text-align: center;
  font-size: 0.82rem;
  color: var(--text-gray);
  position: relative;
}

.lobby-error {
  font-size: 0.83rem;
  color: #e53935;
  margin: 0;
}

.join-row {
  display: flex;
  gap: 0.5rem;
}

.join-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-light);
  color: var(--text-dark);
  font-size: 0.9rem;
}

.btn-primary {
  padding: 0.55rem 1.2rem;
  background: linear-gradient(135deg,#0052cc,#00d4ff);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: opacity 0.2s;
}
.btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Room Layout ── */
.conv-wrapper {
  display: flex;
  gap: 1.25rem;
  height: calc(100vh - 96px);
}

/* ── Camera Panel ── */
.cam-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}

.cam-top-bar {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
}

.cam-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-dark);
  flex: 1;
}

.live-badge {
  font-size: 0.72rem;
  font-weight: 700;
  color: #e53935;
  animation: pulse 1.5s infinite;
}

@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

.cam-frame {
  flex: 1;
  position: relative;
  background: #000;
  overflow: hidden;
}

.cam-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  pointer-events: none;
}

.camera-error {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1rem;
  color: #fff;
  text-align: center;
  background: rgba(0, 0, 0, 0.65);
  z-index: 2;
}

.pending-sign {
  opacity: 0.8;
}

.det-badge {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(0,0,0,0.78);
  backdrop-filter: blur(8px);
  padding: 0.5rem 1.2rem;
  border-radius: 50px;
  white-space: nowrap;
}

.det-sign { color: #fff; font-size: 1.3rem; font-weight: 700; }
.det-conf {
  background: linear-gradient(135deg,#0052cc,#00d4ff);
  color: #fff;
  padding: 0.15rem 0.6rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
}

.cam-bottom-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
}

.det-mode-toggle {
  display: flex;
  gap: 0.4rem;
  flex: 1;
  background: var(--bg-light);
  border-radius: 10px;
  padding: 0.3rem;
}

.det-btn {
  flex: 1;
  padding: 0.4rem 0.75rem;
  border: none;
  background: transparent;
  color: var(--text-gray);
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.det-btn.active {
  background: linear-gradient(135deg,#0052cc,#00d4ff);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,82,204,0.3);
}

.btn-send-sign {
  padding: 0.45rem 1rem;
  background: #0052cc;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition: background 0.2s;
}

.btn-send-sign:hover:not(:disabled) { background: #003d99; }
.btn-send-sign:disabled { opacity: 0.45; cursor: not-allowed; }

/* ── Chat Panel ── */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}

.chat-top-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
}

.chat-title {
  flex: 1;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-dark);
}

.chat-title code {
  background: var(--bg-light);
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
  font-size: 0.85rem;
  letter-spacing: 1px;
}

.btn-leave {
  padding: 0.35rem 0.8rem;
  background: #e53935;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: background 0.2s;
}
.btn-leave:hover { background: #b71c1c; }

.btn-clear {
  background: none;
  border: none;
  color: #e53935;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.btn-clear:hover { background: rgba(229,57,53,0.1); }

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  scroll-behavior: smooth;
}

.chat-empty {
  margin: auto;
  text-align: center;
  color: var(--text-gray);
  padding: 2rem;
}
.chat-empty i { font-size: 2.5rem; display: block; margin-bottom: 0.75rem; }

/* ── Bubbles ── */
.bubble {
  max-width: 78%;
  padding: 0.55rem 0.9rem;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  animation: fadeUp 0.22s ease;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.bubble-sign {
  align-self: flex-start;
  background: #e8f0fe;
  color: #1a237e;
  border-bottom-left-radius: 4px;
}

[data-theme="dark"] .bubble-sign {
  background: #1a2a4a;
  color: #90caf9;
}

.bubble-speech {
  align-self: flex-end;
  background: #0052cc;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.bubble-remote {
  align-self: flex-start;
  background: var(--bg-light);
  color: var(--text-dark);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--border);
}

.bubble-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  opacity: 0.65;
}

.bubble-text { font-size: 0.95rem; font-weight: 500; line-height: 1.4; }
.bubble-sub { font-size: 0.78rem; opacity: 0.7; }
.bubble-time { font-size: 0.68rem; opacity: 0.55; margin-top: 2px; }

.bubble-sign .bubble-time  { text-align: left; }
.bubble-speech .bubble-time { text-align: right; }

.processing { opacity: 0.7; }

/* ── Chat Input ── */
.chat-input {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
}

.rec-status {
  font-size: 0.82rem;
  color: #e53935;
  margin-bottom: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.rec-dot {
  width: 8px; height: 8px;
  background: #e53935;
  border-radius: 50%;
  animation: pulse 0.8s infinite;
  display: inline-block;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.lang-select-wrap { display: flex; align-items: center; }

.lang-select {
  padding: 0.35rem 0.5rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-light);
  color: var(--text-dark);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-mic {
  width: 44px; height: 44px;
  border-radius: 50%;
  background: #0052cc;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, transform 0.15s;
  flex-shrink: 0;
}
.btn-mic:hover { background: #003d99; }
.btn-mic.recording { background: #e53935; transform: scale(1.1); }

.input-hint {
  font-size: 0.82rem;
  color: var(--text-gray);
  flex: 1;
}

.solo-text-input {
  flex: 1;
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-light);
  color: var(--text-dark);
  font-size: 0.9rem;
}

.btn-send-text {
  width: 38px; height: 38px;
  border-radius: 50%;
  background: #0052cc;
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s;
}
.btn-send-text:hover:not(:disabled) { background: #003d99; }
.btn-send-text:disabled { opacity: 0.45; cursor: not-allowed; }

.fingerspell-row {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-top: 5px;
}
.fingerspell-row img {
  width: 42px;
  height: 42px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.25);
}

.bubble-fsl-label {
  font-size: 0.72rem;
  font-weight: 700;
  opacity: 0.75;
  margin-top: 6px;
}

.bubble-fsl-video {
  width: 100%;
  max-width: 180px;
  border-radius: 8px;
  margin-top: 4px;
}

@media (max-width: 820px) {
  .conv-wrapper { flex-direction: column; height: auto; }
  .cam-panel { flex: none; height: 360px; }
}
</style>

