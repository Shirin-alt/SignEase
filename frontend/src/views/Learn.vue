<template>
  <Layout>
    <!-- Lesson List -->
    <div v-if="!currentLesson">
      <div class="page-hero">
        <div class="hero-icon"><i class="fas fa-graduation-cap"></i></div>
        <div>
          <h2>Learn Sign Language</h2>
          <p>Complete lessons to earn XP and master FSL!</p>
        </div>
      </div>

      <div class="lessons-grid">
        <div v-for="lesson in lessons" :key="lesson.id" class="lesson-card" :class="{ locked: lesson.locked }">
          <div class="lesson-icon-wrap" :style="lesson.locked ? 'background:linear-gradient(135deg,#adb5bd,#6c757d)' : 'background:linear-gradient(135deg,#0052cc,#00d4ff)'">
            <i :class="lesson.locked ? 'fas fa-lock' : 'fas fa-graduation-cap'"></i>
          </div>
          <h3>{{ lesson.title }}</h3>
          <p>{{ lesson.description }}</p>
          <div class="lesson-xp"><i class="fas fa-star"></i> +{{ lesson.xp }} XP</div>
          <button v-if="!lesson.locked" @click="startLesson(lesson.id)" class="btn btn-primary" style="width:100%">
            Start Lesson
          </button>
          <button v-else class="btn btn-secondary" style="width:100%" disabled>
            🔒 Coming Soon
          </button>
        </div>
      </div>
    </div>

    <!-- Lesson Content (Study) -->
    <div v-else-if="!showPractice">
      <button @click="currentLesson = null" class="btn btn-secondary back-btn">
        <i class="fas fa-arrow-left"></i> Back to Lessons
      </button>
      <div class="panel">
        <div class="panel-header">
          <span><i class="fas fa-book-open"></i> {{ currentLesson.title }}</span>
        </div>
        <div class="panel-body">
          <div class="signs-display">
            <div v-for="(sign, idx) in currentLesson.content" :key="idx" class="sign-item">
              <video v-if="sign.video" :src="sign.video" class="sign-video" controls muted playsinline></video>
              <div v-else-if="sign.emoji" class="sign-emoji">{{ sign.emoji }}</div>
              <img v-else :src="`${BACKEND_URL}/static/images/${sign.image}`" :alt="sign.name" class="sign-img">
              <h4>{{ sign.name }}</h4>
              <p>{{ sign.description }}</p>
            </div>
          </div>
          <button @click="startPractice" class="btn btn-primary" style="margin-top:2rem;width:100%">
            <i class="fas fa-camera"></i> Start Camera Practice
          </button>
        </div>
      </div>
    </div>

    <!-- Camera Practice Mode -->
    <div v-else>
      <button @click="exitPractice" class="btn btn-secondary back-btn">
        <i class="fas fa-arrow-left"></i> Back to Lesson
      </button>

      <div v-if="!practiceComplete" class="practice-layout">
        <!-- Left: Target sign prompt -->
        <div class="target-panel">
          <div class="target-label">Show this sign:</div>

          <!-- Feedback flash -->
          <transition name="feedback-pop">
            <div v-if="feedbackVisible" class="feedback-flash" :class="feedbackType">
              {{ feedbackType === 'correct' ? '✓ Correct!' : '✗ Try again' }}
            </div>
          </transition>

          <div class="target-sign-wrap" :class="{ 'pulse-correct': feedbackType === 'correct' && feedbackVisible }">
            <video v-if="currentTarget.video" :src="currentTarget.video" class="target-video" autoplay loop muted playsinline></video>
            <div v-else-if="currentTarget.emoji" class="target-emoji">{{ currentTarget.emoji }}</div>
            <img v-else :src="`${BACKEND_URL}/static/images/${currentTarget.image}`" class="target-img">
            <div class="target-name">{{ currentTarget.name }}</div>
            <div v-if="currentTarget.description" class="target-desc">{{ currentTarget.description }}</div>
          </div>

          <div class="progress-bar-wrap">
            <div class="progress-fill" :style="{ width: (practiceIndex / practiceTargets.length * 100) + '%' }"></div>
          </div>
          <div class="progress-label">{{ practiceIndex }} / {{ practiceTargets.length }} signs completed</div>

          <!-- Detected sign display -->
          <div class="detected-box" :class="{ 'detected-match': isMatch }">
            <span class="detected-label">Detected:</span>
            <span class="detected-value">{{ detectedDisplay || '—' }}</span>
            <span v-if="detectedConf" class="detected-conf">{{ Math.round(detectedConf * 100) }}%</span>
          </div>
        </div>

        <!-- Right: Camera feed -->
        <div class="camera-panel">
          <canvas ref="camCanvas" class="video-feed" width="640" height="480"></canvas>
          <div class="camera-hint"><i class="fas fa-hand-paper"></i> Hold your sign steady in front of the camera</div>
        </div>
      </div>

      <!-- Practice Complete -->
      <div v-else class="quiz-result">
        <div class="result-icon">🎉</div>
        <h2>Lesson Complete!</h2>
        <div class="result-score">{{ practiceTargets.length }} / {{ practiceTargets.length }}</div>
        <p v-if="earnedXP > 0" class="result-xp"><i class="fas fa-star"></i> +{{ earnedXP }} XP Earned!</p>
        <button @click="resetLesson" class="btn btn-primary" style="margin-top:1.5rem">
          Back to Lessons
        </button>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Layout from '../components/Layout.vue'
import api from '../api'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:5000`

const lessons = ref([
  {
    id: 1, title: 'Lesson 1: Greetings', xp: 50, locked: false,
    description: 'Learn: Hi, Good Morning, Good Afternoon, Good Evening',
    detectorMode: 'phrase',
    content: [
      { name: 'Hi', video: `${BACKEND_URL}/static/videos/hi.mp4`, description: 'Wave your dominant hand side to side at shoulder level.', target: 'hi' },
      { name: 'Good Morning', video: `${BACKEND_URL}/static/videos/magandang umaga.mp4`, description: 'Place one hand on your forearm, then raise it upward like the rising sun.', target: 'good_morning' },
      { name: 'Good Afternoon', video: `${BACKEND_URL}/static/videos/magandang hapon.mp4`, description: 'Rest one arm flat, then angle the other arm downward from elbow.', target: 'good_afternoon' },
      { name: 'Good Evening', video: `${BACKEND_URL}/static/videos/magandang gabi.mp4`, description: 'Rest one arm flat, then lower the other arm downward.', target: 'good_evening' },
    ]
  },
  {
    id: 2, title: 'Lesson 2: Conversations', xp: 50, locked: false,
    description: 'Learn: How are you?, I am fine, I am not fine',
    detectorMode: 'phrase',
    content: [
      { name: 'How are you?', video: `${BACKEND_URL}/static/videos/how_are_you.mp4`, description: 'Point to the other person, then show a questioning expression with both hands open.', target: 'how_are_you' },
      { name: 'I am fine', video: `${BACKEND_URL}/static/videos/i_am_fine.mp4`, description: 'Point to yourself, then give a thumbs up or open flat hand moving forward.', target: 'i_am_fine' },
      { name: 'I am not fine', video: `${BACKEND_URL}/static/videos/i_am_not_fine.mp4`, description: 'Point to yourself, then shake head while showing a downward or crossed hand motion.', target: 'i_am_not_fine' },
    ]
  },
  {
    id: 3, title: 'Lesson 3: Introductions', xp: 100, locked: false,
    description: 'Learn: What is your name?, My name is..., Sorry, Thank You',
    detectorMode: 'phrase',
    content: [
      { name: 'What is your name?', video: `${BACKEND_URL}/static/videos/whats_your_name.mp4`, description: 'Point to the other person, then tap two fingers on your chin twice.', target: 'whats_your_name' },
      { name: 'My name is...', video: `${BACKEND_URL}/static/videos/my_name_is.mp4`, description: 'Point to yourself, then tap two fingers on your chin.', target: 'my_name_is' },
      { name: 'Sorry', video: `${BACKEND_URL}/static/videos/sorry.mp4`, description: 'Make a fist and rub it in a circular motion over your chest.', target: 'sorry' },
      { name: 'Thank You', video: `${BACKEND_URL}/static/videos/thank_you.mp4`, description: 'Touch your chin with fingertips, then move your hand forward.', target: 'thank_you' },
    ]
  },
  {
    id: 4, title: 'Lesson 4: Alphabet A-M', xp: 100, locked: true,
    description: 'Learn: Letters A through M',
    detectorMode: 'alphabet',
    content: [
      { name: 'Letter A', image: 'a.jpeg', description: 'First letter of the alphabet', target: 'a' },
      { name: 'Letter B', image: 'b.jpeg', description: 'Second letter of the alphabet', target: 'b' },
      { name: 'Letter C', image: 'c.jpeg', description: 'Third letter of the alphabet', target: 'c' },
      { name: 'Letter D', image: 'd.jpeg', description: 'Fourth letter of the alphabet', target: 'd' },
      { name: 'Letter E', image: 'e.jpeg', description: 'Fifth letter of the alphabet', target: 'e' },
      { name: 'Letter F', image: 'f.jpeg', description: 'Sixth letter of the alphabet', target: 'f' },
      { name: 'Letter G', image: 'g.jpeg', description: 'Seventh letter', target: 'g' },
      { name: 'Letter H', image: 'h.jpeg', description: 'Eighth letter', target: 'h' },
      { name: 'Letter I', image: 'i.jpeg', description: 'Ninth letter', target: 'i' },
      { name: 'Letter J', image: 'j.jpeg', description: 'Tenth letter', target: 'j' },
      { name: 'Letter K', image: 'k.jpeg', description: 'Eleventh letter', target: 'k' },
      { name: 'Letter L', image: 'l.jpeg', description: 'Twelfth letter', target: 'l' },
      { name: 'Letter M', image: 'm.jpeg', description: 'Thirteenth letter', target: 'm' },
    ]
  },
  {
    id: 5, title: 'Lesson 5: Alphabet N-Z', xp: 100, locked: true,
    description: 'Learn: Letters N through Z',
    detectorMode: 'alphabet',
    content: [
      { name: 'Letter N', image: 'n.jpeg', description: 'Fourteenth letter', target: 'n' },
      { name: 'Letter O', image: 'o.jpeg', description: 'Fifteenth letter', target: 'o' },
      { name: 'Letter P', image: 'p.jpeg', description: 'Sixteenth letter', target: 'p' },
      { name: 'Letter R', image: 'r.jpeg', description: 'Eighteenth letter', target: 'r' },
      { name: 'Letter S', image: 's.jpeg', description: 'Nineteenth letter', target: 's' },
      { name: 'Letter T', image: 't.jpeg', description: 'Twentieth letter', target: 't' },
      { name: 'Letter U', image: 'u.jpeg', description: 'Twenty-first letter', target: 'u' },
      { name: 'Letter V', image: 'v.jpeg', description: 'Twenty-second letter', target: 'v' },
      { name: 'Letter W', image: 'w.jpeg', description: 'Twenty-third letter', target: 'w' },
      { name: 'Letter X', image: 'x.jpeg', description: 'Twenty-fourth letter', target: 'x' },
      { name: 'Letter Y', image: 'y.jpeg', description: 'Twenty-fifth letter', target: 'y' },
      { name: 'Letter Z', image: 'z.jpeg', description: 'Twenty-sixth letter', target: 'z' },
    ]
  }
])

const currentLesson = ref(null)
const showPractice = ref(false)
const practiceTargets = ref([])
const practiceIndex = ref(0)
const practiceComplete = ref(false)
const earnedXP = ref(0)

// Detection state
const detectedSign = ref(null)
const detectedDisplay = ref(null)
const detectedConf = ref(0)
const feedbackVisible = ref(false)
const feedbackType = ref('correct')
const camCanvas = ref(null)
let pollTimer = null
let frameTimer = null
let advanceTimeout = null
let lastPracticeTimestamp = null

const currentTarget = computed(() => practiceTargets.value[practiceIndex.value] || {})
const isMatch = computed(() => detectedSign.value && detectedSign.value === currentTarget.value?.target)

const checkLessonStatus = async () => {
  try {
    const response = await fetch('/api/learn', { headers: { 'Accept': 'application/json' }, credentials: 'include' })
    const data = await response.json()
    if (data.unlocked_lessons) {
      lessons.value[3].locked = !data.unlocked_lessons[4]
      lessons.value[4].locked = !data.unlocked_lessons[5]
    }
  } catch {}
}

const startLesson = (id) => {
  currentLesson.value = lessons.value.find(l => l.id === id)
  showPractice.value = false
  practiceComplete.value = false
  earnedXP.value = 0
}

const startPractice = async () => {
  practiceTargets.value = [...currentLesson.value.content]
  practiceIndex.value = 0
  practiceComplete.value = false
  feedbackVisible.value = false
  detectedSign.value = null
  detectedDisplay.value = null
  detectedConf.value = 0
  showPractice.value = true
  try {
    await fetch('/api/set_mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ mode: currentLesson.value.detectorMode })
    })
  } catch {}
  startPolling()
}

const startPolling = () => {
  stopPolling()
  lastPracticeTimestamp = null
  pollTimer = setInterval(pollDetection, 600)
  frameTimer = setInterval(fetchFrame, 100)
}

const stopPolling = () => {
  clearInterval(pollTimer)
  clearInterval(frameTimer)
  clearTimeout(advanceTimeout)
  pollTimer = null
  frameTimer = null
}

const fetchFrame = async () => {
  if (!camCanvas.value) return
  try {
    const res = await fetch('/test_frame', { credentials: 'include' })
    if (!res.ok) return
    const ct = res.headers.get('content-type')
    if (!ct?.includes('image')) return
    const blob = await res.blob()
    if (!blob.size) return
    const img = new Image()
    img.onload = () => {
      const ctx = camCanvas.value?.getContext('2d')
      if (ctx) ctx.drawImage(img, 0, 0, 640, 480)
    }
    img.src = URL.createObjectURL(blob)
  } catch {}
}

const pollDetection = async () => {
  if (practiceComplete.value || feedbackVisible.value) return
  try {
    const res = await fetch('/api/latest', { credentials: 'include' })
    const data = await res.json()

    // Ignore if detector mode doesn't match lesson mode
    if (data.mode && data.mode !== currentLesson.value?.detectorMode) return

    detectedSign.value = data.sign || null
    detectedDisplay.value = data.display || (data.sign ? data.sign.toUpperCase() : null)
    detectedConf.value = data.conf || 0

    // Only trigger on a new detection event (timestamp changed)
    if (data.sign && data.conf >= 0.70 && data.sign === currentTarget.value?.target) {
      const ts = data.timestamp ?? null
      if (ts && ts !== lastPracticeTimestamp) {
        lastPracticeTimestamp = ts
        onCorrect()
      }
    }
  } catch {}
}

const onCorrect = () => {
  feedbackType.value = 'correct'
  feedbackVisible.value = true
  earnedXP.value += 10
  stopPolling()

  advanceTimeout = setTimeout(() => {
    feedbackVisible.value = false
    detectedSign.value = null
    detectedDisplay.value = null
    detectedConf.value = 0
    const next = practiceIndex.value + 1
    if (next >= practiceTargets.value.length) {
      practiceComplete.value = true
      awardXP(earnedXP.value)
    } else {
      practiceIndex.value = next
      startPolling()
    }
  }, 1500)
}

const exitPractice = async () => {
  stopPolling()
  showPractice.value = false
  // Reset detector to alphabet mode (default)
  try {
    await fetch('/api/set_mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ mode: 'alphabet' })
    })
  } catch {}
}

const resetLesson = () => {
  stopPolling()
  currentLesson.value = null
  showPractice.value = false
  practiceComplete.value = false
}

const awardXP = async (xp) => {
  try {
    const currentXP = parseInt(localStorage.getItem('xp') || '0')
    const currentLevel = parseInt(localStorage.getItem('level') || '1')
    const newXP = currentXP + xp
    localStorage.setItem('xp', newXP.toString())
    window.dispatchEvent(new Event('xpUpdated'))
    await api.syncProgress({ xp: newXP, level: currentLevel })
    if (newXP >= 100 && currentXP < 100) await checkLessonStatus()
  } catch {}
}

onMounted(checkLessonStatus)
onUnmounted(stopPolling)
</script>

<style scoped>
.page-hero {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  background: linear-gradient(135deg, #0052cc, #00d4ff);
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

.lessons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.lesson-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  transition: transform 0.2s, box-shadow 0.2s;
}

.lesson-card:hover:not(.locked) {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,82,204,0.15);
}

.lesson-card.locked { opacity: 0.6; }

.lesson-icon-wrap {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  margin: 0 auto 1rem;
}

.lesson-card h3 { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 700; color: var(--text-dark); }
.lesson-card p { font-size: 0.875rem; color: var(--text-gray); margin-bottom: 1rem; }

.lesson-xp {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: linear-gradient(135deg, #f7971e22, #ffd20022);
  color: #f7971e;
  font-weight: 700;
  font-size: 0.875rem;
  padding: 0.3rem 0.75rem;
  border-radius: 20px;
  margin-bottom: 1rem;
}

.back-btn {
  margin-bottom: 1.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.panel {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  overflow: hidden;
  border: 1px solid var(--border);
  margin-bottom: 1.5rem;
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
.panel-body { padding: 1.5rem; }

.signs-display {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.25rem;
}

.sign-item {
  text-align: center;
  padding: 1.25rem 1rem;
  background: var(--bg-light);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.sign-video {
  width: 100%;
  max-height: 200px;
  border-radius: 10px;
  margin-bottom: 0.75rem;
  background: #000;
}

.sign-emoji { font-size: 4.5rem; line-height: 1; margin-bottom: 0.75rem; }
.sign-item h4 { margin: 0 0 0.4rem; font-size: 1rem; color: var(--text-dark); }
.sign-item p { font-size: 0.8rem; color: var(--text-gray); margin: 0; }

.sign-img {
  width: 130px;
  height: 130px;
  object-fit: cover;
  border-radius: 10px;
  margin-bottom: 0.75rem;
}

/* --- Practice Layout --- */
.practice-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 768px) {
  .practice-layout { grid-template-columns: 1fr; }
}

.target-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2rem;
  text-align: center;
  position: relative;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

.target-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-gray);
  margin-bottom: 1rem;
}

.feedback-flash {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.5rem 1.5rem;
  border-radius: 30px;
  font-weight: 700;
  font-size: 1rem;
  z-index: 10;
  white-space: nowrap;
}

.feedback-flash.correct { background: #d4edda; color: #155724; border: 1.5px solid #c3e6cb; }
.feedback-flash.wrong { background: #f8d7da; color: #721c24; border: 1.5px solid #f5c6cb; }

.feedback-pop-enter-active, .feedback-pop-leave-active { transition: all 0.25s ease; }
.feedback-pop-enter-from, .feedback-pop-leave-to { opacity: 0; transform: translateX(-50%) scale(0.8); }

.target-sign-wrap {
  padding: 1.5rem 1rem;
  border-radius: 16px;
  background: var(--bg-light);
  border: 2px solid var(--border);
  margin-bottom: 1.5rem;
  transition: border-color 0.3s;
}

.target-sign-wrap.pulse-correct { border-color: #28a745; background: rgba(40,167,69,0.06); }

.target-emoji { font-size: 6rem; line-height: 1; margin-bottom: 0.75rem; }

.target-video {
  width: 100%;
  max-height: 220px;
  border-radius: 12px;
  margin-bottom: 0.75rem;
  background: #000;
  object-fit: cover;
}

.target-img {
  width: 180px;
  height: 180px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 0.75rem;
}

.target-name { font-size: 1.4rem; font-weight: 800; color: var(--text-dark); margin-bottom: 0.4rem; }
.target-desc { font-size: 0.82rem; color: var(--text-gray); }

.progress-bar-wrap {
  background: var(--border);
  border-radius: 10px;
  height: 8px;
  overflow: hidden;
  margin-bottom: 0.4rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #0052cc, #00d4ff);
  border-radius: 10px;
  transition: width 0.4s ease;
}

.progress-label { font-size: 0.8rem; color: var(--text-gray); margin-bottom: 1rem; }

.detected-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: var(--bg-light);
  border: 2px solid var(--border);
  transition: border-color 0.3s, background 0.3s;
}

.detected-box.detected-match {
  border-color: #28a745;
  background: rgba(40,167,69,0.08);
}

.detected-label { font-size: 0.78rem; color: var(--text-gray); font-weight: 600; }
.detected-value { font-size: 1.1rem; font-weight: 800; color: var(--text-dark); }
.detected-conf {
  font-size: 0.75rem;
  background: rgba(0,82,204,0.1);
  color: #0052cc;
  padding: 0.1rem 0.5rem;
  border-radius: 20px;
  font-weight: 700;
}

.camera-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

.video-feed {
  width: 100%;
  display: block;
  border-radius: 20px 20px 0 0;
}

.camera-hint {
  padding: 0.75rem 1rem;
  text-align: center;
  font-size: 0.82rem;
  color: var(--text-gray);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}

/* Quiz result (reused for practice complete) */
.quiz-result {
  text-align: center;
  padding: 2rem 1rem;
  background: var(--bg-card);
  border-radius: 20px;
  border: 1px solid var(--border);
}

.result-icon { font-size: 4rem; margin-bottom: 0.75rem; }
.quiz-result h2 { margin: 0 0 1rem; font-size: 1.5rem; color: var(--text-dark); }

.result-score {
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #0052cc, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.75rem;
}

.result-xp {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: #f7971e;
  font-size: 1.25rem;
  font-weight: 700;
}

.btn-secondary {
  background: var(--bg-light);
  border: 1px solid var(--border);
  color: var(--text-dark);
}

.btn-secondary:hover { background: var(--border); }
</style>
