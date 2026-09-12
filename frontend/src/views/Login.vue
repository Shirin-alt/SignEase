<template>
  <div class="auth-page">
    <!-- Animated background blobs -->
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>

    <div class="auth-wrapper">
      <!-- Logo -->
      <div class="brand">
        <div class="brand-icon"><i class="fas fa-sign-language"></i></div>
        <span>Signease</span>
      </div>

      <!-- Glass Card -->
      <div class="glass-card">
        <h2>Welcome back</h2>
        <p class="subtitle">Sign in to continue your FSL journey</p>

        <form @submit.prevent="handleLogin">
          <div class="field-group">
            <label>Username</label>
            <div class="input-wrap">
              <i class="fas fa-user"></i>
              <input v-model="username" type="text" class="glass-input" placeholder="Enter your username" required>
            </div>
          </div>

          <div class="field-group">
            <label>Password</label>
            <div class="input-wrap">
              <i class="fas fa-lock"></i>
              <input v-model="password" :type="showPw ? 'text' : 'password'" class="glass-input" placeholder="Enter your password" required>
              <button type="button" class="eye-btn" @click="showPw = !showPw">
                <i :class="showPw ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
              </button>
            </div>
          </div>

          <div class="remember-row">
            <label class="check-label">
              <input v-model="remember" type="checkbox">
              <span>Remember me</span>
            </label>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="!loading"><i class="fas fa-sign-in-alt"></i> Sign In</span>
            <span v-else><i class="fas fa-spinner fa-spin"></i> Signing in...</span>
          </button>
        </form>

        <div class="divider"><span>or</span></div>

        <button @click="googleLogin" class="google-btn">
          <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
            <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
            <path d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" fill="#FBBC05"/>
            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </button>

        <div v-if="error" class="alert-error">
          <i class="fas fa-exclamation-circle"></i> {{ error }}
        </div>

        <p class="bottom-link">
          Don't have an account?
          <router-link to="/register">Create one free</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const remember = ref(false)
const error = ref('')
const loading = ref(false)
const showPw = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.login(username.value, password.value, remember.value)
    if (data.status === 'success') {
      localStorage.setItem('isAuthenticated', 'true')
      localStorage.setItem('isAdmin', data.user.is_admin)
      localStorage.setItem('username', data.user.username)
      localStorage.setItem('email', data.user.email)
      localStorage.setItem('xp', data.user.xp)
      localStorage.setItem('streak', data.user.streak)
      router.push('/dashboard')
    }
  } catch (requestError) {
    error.value = requestError.code === 'ECONNABORTED'
      ? 'The server took too long to respond. Please try again.'
      : requestError.response?.data?.message || 'Invalid username or password'
  } finally {
    loading.value = false
  }
}

const googleLogin = () => api.googleLogin()
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

/* Animated blobs */
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

/* Wrapper */
.auth-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

/* Brand */
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

/* Glass Card */
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

/* Fields */
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

.remember-row {
  margin-bottom: 1.5rem;
}

.check-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255,255,255,0.6);
  font-size: 0.875rem;
  cursor: pointer;
}

.check-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #00d4ff;
}

/* Submit */
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
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(0, 82, 204, 0.6);
}

.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

/* Divider */
.divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
  color: rgba(255,255,255,0.3);
  font-size: 0.8rem;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255,255,255,0.12);
}

/* Google */
.google-btn {
  width: 100%;
  height: 50px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 12px;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
}

.google-btn:hover {
  background: rgba(255,255,255,0.14);
  border-color: rgba(255,255,255,0.3);
  transform: translateY(-1px);
}

/* Alert */
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

/* Bottom link */
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
</style>
