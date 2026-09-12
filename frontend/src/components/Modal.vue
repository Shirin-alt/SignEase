<template>
  <Transition name="modal">
    <div v-if="show" class="modal-overlay" @click="onCancel">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <i :class="icon" :style="{ color: iconColor }"></i>
          <h3>{{ title }}</h3>
        </div>
        <div class="modal-body">
          <p>{{ message }}</p>
        </div>
        <div class="modal-footer">
          <button @click="onCancel" class="btn btn-secondary">
            <i class="fas fa-times"></i> Cancel
          </button>
          <button @click="onConfirm" class="btn" :class="confirmClass">
            <i :class="confirmIcon"></i> {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: 'Confirm Action' },
  message: { type: String, required: true },
  type: { type: String, default: 'warning' },
  confirmText: { type: String, default: 'Confirm' },
  confirmIcon: { type: String, default: 'fas fa-check' }
})

const emit = defineEmits(['confirm', 'cancel'])

const icon = computed(() => {
  return {
    warning: 'fas fa-exclamation-triangle',
    danger: 'fas fa-trash-alt',
    info: 'fas fa-info-circle',
    success: 'fas fa-check-circle'
  }[props.type]
})

const iconColor = computed(() => {
  return {
    warning: '#f39c12',
    danger: '#e74c3c',
    info: '#3498db',
    success: '#2ecc71'
  }[props.type]
})

const confirmClass = computed(() => {
  return {
    warning: 'btn-warning',
    danger: 'btn-danger',
    info: 'btn-primary',
    success: 'btn-success'
  }[props.type]
})

const onConfirm = () => {
  emit('confirm')
}

const onCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.modal-header i {
  font-size: 2.5rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-body {
  margin-bottom: 1.5rem;
}

.modal-body p {
  margin: 0;
  font-size: 1rem;
  color: #555;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content {
  transform: scale(0.9);
}

.modal-leave-to .modal-content {
  transform: scale(0.9);
}
</style>
