<template>
  <div>
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, 'mobile-open': mobileOpen }">
      <div class="sidebar-brand">
        <i class="fas fa-sign-language"></i>
        <span class="brand-text">Signease</span>
      </div>

      <nav class="sidebar-menu">
        <router-link to="/dashboard" class="menu-item" active-class="active">
          <i class="fas fa-home" style="color:#0052cc"></i>
          <span class="menu-text">Dashboard</span>
        </router-link>
        <router-link to="/learn" class="menu-item" active-class="active">
          <i class="fas fa-graduation-cap" style="color:#28a745"></i>
          <span class="menu-text">Learn</span>
        </router-link>
        <router-link to="/profile" class="menu-item" active-class="active">
          <i class="fas fa-user" style="color:#fd7e14"></i>
          <span class="menu-text">Profile</span>
        </router-link>
        <router-link to="/history" class="menu-item" active-class="active">
          <i class="fas fa-history" style="color:#6f42c1"></i>
          <span class="menu-text">History</span>
        </router-link>
        <router-link v-if="isAdmin" to="/admin" class="menu-item" active-class="active">
          <i class="fas fa-cog" style="color:#6c757d"></i>
          <span class="menu-text">Admin</span>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <a @click="logout" class="menu-item">
          <i class="fas fa-sign-out-alt"></i>
          <span class="menu-text">Logout</span>
        </a>
      </div>
    </aside>

    <div class="main-wrapper" :class="{ expanded: sidebarCollapsed }">
      <header class="top-header">
        <div class="header-left">
          <button class="toggle-btn" @click="toggleSidebar">
            <i class="fas fa-bars"></i>
          </button>
          <slot name="header">
            <span style="font-weight:600; font-size:1rem; color:var(--text-dark);">Signease</span>
          </slot>
        </div>
        <div class="header-right">
          <div class="gamification-stats">
            <div class="stat-item" style="color:#f7971e">
              <i class="fas fa-fire"></i>
              <span>{{ streak }}</span>
            </div>
            <div class="stat-item" style="color:#0052cc">
              <i class="fas fa-star"></i>
              <span>{{ xp }} XP</span>
            </div>
            <div class="stat-item" style="color:#28a745">
              <i class="fas fa-trophy"></i>
              <span>Lv {{ level }}</span>
            </div>
          </div>
          <button class="theme-toggle" @click="toggleTheme">
            <i :class="isDark ? 'fas fa-sun' : 'fas fa-moon'"></i>
          </button>
        </div>
      </header>

      <main class="content-area">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const sidebarCollapsed = ref(false)
const mobileOpen = ref(false)
const isDark = ref(false)
const streak = ref(0)
const xp = ref(0)
const level = ref(1)
const isAdmin = computed(() => localStorage.getItem('isAdmin') === 'true')

const toggleSidebar = () => {
  if (window.innerWidth <= 768) {
    mobileOpen.value = !mobileOpen.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('theme', theme)
}

const logout = async () => {
  try { await api.logout() } catch {}
  localStorage.removeItem('isAuthenticated')
  localStorage.removeItem('isAdmin')
  router.push('/login')
}

onMounted(() => {
  const theme = localStorage.getItem('theme') || 'light'
  isDark.value = theme === 'dark'
  
  const savedXp = localStorage.getItem('xp') || 0
  const savedStreak = localStorage.getItem('streak') || 0
  const savedLevel = localStorage.getItem('level') || 1
  xp.value = parseInt(savedXp)
  streak.value = parseInt(savedStreak)
  level.value = parseInt(savedLevel)
  
  // Listen for storage changes to update XP in real-time
  window.addEventListener('storage', updateStats)
  window.addEventListener('xpUpdated', updateStats)
  window.addEventListener('streakUpdated', updateStats)
})

onUnmounted(() => {
  window.removeEventListener('storage', updateStats)
  window.removeEventListener('xpUpdated', updateStats)
  window.removeEventListener('streakUpdated', updateStats)
})

const updateStats = () => {
  const savedXp = localStorage.getItem('xp') || 0
  const savedStreak = localStorage.getItem('streak') || 0
  const savedLevel = localStorage.getItem('level') || 1
  xp.value = parseInt(savedXp)
  streak.value = parseInt(savedStreak)
  level.value = parseInt(savedLevel)
}
</script>
