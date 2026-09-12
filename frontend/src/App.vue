<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  const theme = localStorage.getItem('theme') || 'light'
  document.documentElement.setAttribute('data-theme', theme)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

:root {
  --primary: #0052cc;
  --primary-dark: #0041a6;
  --primary-light: #4a90e2;
  --bg-light: #f5f7fa;
  --bg-card: #ffffff;
  --text-dark: #1a1a1a;
  --text-gray: #6c757d;
  --border: #e1e4e8;
  --sidebar-width: 260px;
  --sidebar-collapsed: 70px;
  --header-height: 80px;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);
}

[data-theme="dark"] {
  --bg-light: #1a1d23;
  --bg-card: #242830;
  --text-dark: #e4e6eb;
  --text-gray: #b0b3b8;
  --border: #3a3f4b;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-light);
  color: var(--text-dark);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>
