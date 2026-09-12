<template>
  <Transition name="notification">
    <div v-if="show" class="notification" :class="type">
      <i :class="icon"></i>
      <span>{{ message }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  message: String,
  type: { type: String, default: 'success' },
  duration: { type: Number, default: 3000 }
})

const show = ref(false)

const icon = {
  success: 'fas fa-check-circle',
  error: 'fas fa-exclamation-circle',
  warning: 'fas fa-exclamation-triangle',
  info: 'fas fa-info-circle'
}[props.type]

watch(() => props.message, (newVal) => {
  if (newVal) {
    show.value = true
    setTimeout(() => {
      show.value = false
    }, props.duration)
  }
})
</script>

<style scoped>
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  min-width: 300px;
}

.notification.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.notification.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.notification.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.notification.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.notification i {
  font-size: 1.25rem;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}
</style>
