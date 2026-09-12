<template>
  <div class="auth-page">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>

    <div class="auth-wrapper">
      <!-- Brand -->
      <div class="brand">
        <div class="brand-icon"><i class="fas fa-sign-language"></i></div>
        <span>Signease</span>
      </div>

      <!-- Glass Card -->
      <div class="glass-card">
        <h2>Create account</h2>
        <p class="subtitle">Start your FSL learning journey today — it's free</p>

        <form @submit.prevent="handleRegister">
          <div class="field-row">
            <div class="field-group">
              <label>Username</label>
              <div class="input-wrap">
                <i class="fas fa-user"></i>
                <input v-model="username" type="text" class="glass-input" placeholder="Min. 4 chars" required minlength="4">
              </div>
            </div>
            <div class="field-group">
              <label>Email</label>
              <div class="input-wrap">
                <i class="fas fa-envelope"></i>
                <input v-model="email" type="email" class="glass-input" placeholder="you@email.com" required>
              </div>
            </div>
          </div>

          <div class="field-group">
            <label>Password</label>
            <div class="input-wrap">
              <i class="fas fa-lock"></i>
              <input v-model="password" :type="showPw ? 'text' : 'password'" class="glass-input" placeholder="Min. 8 characters" required minlength="8">
              <button type="button" class="eye-btn" @click="showPw = !showPw">
                <i :class="showPw ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
            </div>
            <div class="pw-strength" v-if="password">
              <div class="pw-bar">
                <div class="pw-fill" :style="{ width: pwStrength.pct + '%', background: pwStrength.color }"></div>
              </div>
              <span :style="{ color: pwStrength.color }">{{ pwStrength.label }}</span>
            </div>
          </div>

          <div class="field-group">
            <label>Confirm Password</label>
            <div class="input-wrap">
              <i class="fas fa-lock"></i>
              <input v-model="confirmPassword" :type="showConfirm ? 'text' : 'password'" class="glass-input" placeholder="Repeat password" required>
              <button type="button" class="eye-btn" @click="showConfirm = !showConfirm">
                <i :class="showConfirm ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
            </div>
            <p v-if="confirmPassword && password !== confirmPassword" class="field-error">
              <i class="fas fa-times-circle"></i> Passwords do not match
            </p>
            <p v-if="confirmPassword && password === confirmPassword" class="field-ok">
              <i class="fas fa-check-circle"></i> Passwords match
            </p>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading || (!!confirmPassword && password !== confirmPassword)">
            <span v-if="!loading"><i class="fas fa-user-plus"></i> Create Account</span>
            <span v-else><i class="fas fa-spinner fa-spin"></i> Creating...</span>
          </button>
        </form>

        <div v-if="error" class="alert-error">
          <i class="fas fa-exclamation-circle"></i> {{ error }}
        </div>
        <div v-if="success" class="alert-success">
          <i class="fas fa-check-circle"></i> {{ success }}
        </div>

        <p class="bottom-link">
          Already have an account?
          <router-link to="/login">Sign In</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const showPw = ref(false)
const showConfirm = ref(false)

const pwStrength = computed(() => {
  const p = password.value
  if (!p) return { pct: 0, color: '#555', label: '' }
  let score = 0
  if (p.length >= 8) score++
  if (p.length >= 12) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  if (score <= 1) return { pct: 25, color: '#e74c3c', label: 'Weak' }
  if (score <= 2) return { pct: 50, color: '#f7971e', label: 'Fair' }
  if (score <= 3) return { pct: 75, color: '#00d4ff', label: 'Good' }
  return { pct: 100, color: '#28a745', label: 'Strong' }
})

const handleRegister = async () => {
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await api.register(username.value, email.value, password.value)
    success.value = 'Account created! Redirecting to login...'
    setTimeout(() => router.push('/login'), 2000)
  } catch (err) {
    error.value = err.response?.data?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #0a0f2e 0%, #0d1b4b 35%, #0a2a6e 65%, #0d3b8e 100%);
  position: relative;
  overflow: hidden;
  padding: 2rem 1rem;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: blobMove 10s ease-in-out infinite alternate;
}

.blob-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #0052cc, #00d4ff);
  top: -150px; left: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #6f42c1, #0052cc);
  bottom: -100px; right: -80px;
  animation-delay: 3s;
}

.blob-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #00d4ff, #28a745);
  top: 50%; left: 60%;
  animation-delay: 6s;
}

@keyframes blobMove {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(40px, 30px) scale(1.1); }
}

.auth-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: white;
}

.brand-icon {
  width: 44px;
  height: 44px;
  background: rgba(255,255,255,0.15);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
}

.brand span {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.glass-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  padding: 2.5rem;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255,255,255,0.1);
}

.glass-card h2 {
  color: white;
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0 0 0.375rem;
}

.subtitle {
  color: rgba(255,255,255,0.6);
  font-size: 0.875rem;
  margin: 0 0 2rem;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field-group {
  margin-bottom: 1.25rem;
}

.field-group label {
  display: block;
  color: rgba(255,255,255,0.75);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.5rem;
}

.input-wrap {
  position: relative;
}

.input-wrap > i:first-child {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255,255,255,0.4);
  font-size: 0.875rem;
  pointer-events: none;
}

.glass-input {
  width: 100%;
  height: 50px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 12px;
  color: white;
  font-size: 0.9rem;
  padding: 0 2.75rem;
  transition: all 0.2s;
  outline: none;
}

.glass-input::placeholder { color: rgba(255,255,255,0.3); }

.glass-input:focus {
  background: rgba(255,255,255,0.12);
  border-color: rgba(0, 212, 255, 0.6);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15);
}

.eye-btn {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: rgba(255,255,255,0.4);
  cursor: pointer;
  padding: 0;
  font-size: 0.875rem;
  transition: color 0.2s;
}

.eye-btn:hover { color: rgba(255,255,255,0.8); }

.pw-strength {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.pw-bar {
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
  overflow: hidden;
}

.pw-fill {
  height: 100%;
  border-radius: 4px;
  transition: all 0.3s;
}

.pw-strength span {
  font-size: 0.75rem;
  font-weight: 700;
  width: 48px;
}

.field-error {
  margin: 0.4rem 0 0;
  font-size: 0.78rem;
  color: #ff6b7a;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.field-ok {
  margin: 0.4rem 0 0;
  font-size: 0.78rem;
  color: #5eff9e;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.submit-btn {
  width: 100%;
  height: 50px;
  background: linear-gradient(135deg, #0052cc, #00d4ff);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 0 4px 20px rgba(0, 82, 204, 0.5);
  letter-spacing: 0.02em;
  margin-top: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 82, 204, 0.6);
}

.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

.alert-error {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(220, 53, 69, 0.15);
  border: 1px solid rgba(220, 53, 69, 0.4);
  border-radius: 10px;
  color: #ff6b7a;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.alert-success {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(40, 167, 69, 0.15);
  border: 1px solid rgba(40, 167, 69, 0.4);
  border-radius: 10px;
  color: #5eff9e;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bottom-link {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.875rem;
  color: rgba(255,255,255,0.5);
}

.bottom-link a {
  color: #00d4ff;
  font-weight: 700;
  text-decoration: none;
}

.bottom-link a:hover { text-decoration: underline; }

@media (max-width: 480px) {
  .field-row { grid-template-columns: 1fr; }
  .glass-card { padding: 2rem 1.5rem; }
}
</style>
