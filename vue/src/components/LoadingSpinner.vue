<template>
  <div class="loading-spinner" :class="containerClass">
    <div class="spinner-wrapper" :style="wrapperStyle">
      <div class="spinner" :class="spinnerClass" :style="spinnerStyle">
        <div v-if="type === 'dots'" class="dots-spinner">
          <div class="dot" :style="dotStyle"></div>
          <div class="dot" :style="dotStyle"></div>
          <div class="dot" :style="dotStyle"></div>
        </div>
        <div v-else-if="type === 'pulse'" class="pulse-spinner" :style="pulseStyle"></div>
        <div v-else-if="type === 'bars'" class="bars-spinner">
          <div class="bar" v-for="i in 5" :key="i" :style="barStyle(i)"></div>
        </div>
        <div v-else-if="type === 'ripple'" class="ripple-spinner">
          <div class="ripple" v-for="i in 3" :key="i" :style="rippleStyle(i)"></div>
        </div>
        <div v-else class="default-spinner">
          <div class="spinner-circle"></div>
        </div>
      </div>
      <div v-if="message" class="loading-message" :style="messageStyle">
        {{ message }}
      </div>
      <div v-if="showProgress" class="progress-info">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'dots', 'pulse', 'bars', 'ripple'].includes(value)
  },
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  color: {
    type: String,
    default: '#667eea'
  },
  message: {
    type: String,
    default: ''
  },
  showMessage: {
    type: Boolean,
    default: true
  },
  center: {
    type: Boolean,
    default: true
  },
  overlay: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0,
    validator: (value) => value >= 0 && value <= 100
  },
  showProgress: {
    type: Boolean,
    default: false
  },
  speed: {
    type: String,
    default: 'normal',
    validator: (value) => ['slow', 'normal', 'fast'].includes(value)
  }
})

// 计算容器样式
const containerClass = computed(() => ({
  'loading-overlay': props.overlay,
  'loading-centered': props.center && !props.overlay
}))

// 计算包装器样式
const wrapperStyle = computed(() => {
  const sizeMap = {
    small: '40px',
    medium: '60px',
    large: '80px'
  }

  return {
    width: sizeMap[props.size],
    height: sizeMap[props.size]
  }
})

// 计算spinner样式
const spinnerClass = computed(() => `spinner-${props.type}`)

const spinnerStyle = computed(() => {
  const durationMap = {
    slow: '1.5s',
    normal: '1s',
    fast: '0.7s'
  }

  return {
    '--spinner-color': props.color,
    '--animation-duration': durationMap[props.speed]
  }
})

// 计算消息样式
const messageStyle = computed(() => ({
  color: props.color,
  marginTop: props.size === 'small' ? '0.5rem' : '1rem'
}))

// 计算点样式
const dotStyle = computed(() => ({
  backgroundColor: props.color
}))

// 计算脉冲样式
const pulseStyle = computed(() => ({
  backgroundColor: props.color
}))

// 计算条形样式
const barStyle = (index) => ({
  backgroundColor: props.color,
  animationDelay: `${index * 0.1}s`
}))

// 计算涟漪样式
const rippleStyle = (index) => ({
  borderColor: props.color,
  animationDelay: `${index * 0.3}s`
}))
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.loading-centered {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.spinner-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-message {
  font-size: 0.9rem;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
}

.progress-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  width: 120px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--spinner-color);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: var(--spinner-color);
  font-weight: 600;
  min-width: 35px;
}

/* 默认spinner */
.default-spinner {
  position: relative;
  width: 100%;
  height: 100%;
}

.spinner-circle {
  width: 100%;
  height: 100%;
  border: 3px solid #f3f3f3;
  border-top: 3px solid var(--spinner-color);
  border-radius: 50%;
  animation: spin var(--animation-duration, 1s) linear infinite;
}

/* 点状spinner */
.dots-spinner {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: dot-bounce var(--animation-duration, 1s) ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 脉冲spinner */
.pulse-spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  animation: pulse var(--animation-duration, 1s) ease-in-out infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

/* 条形spinner */
.bars-spinner {
  display: flex;
  gap: 3px;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.bar {
  width: 4px;
  height: 20px;
  border-radius: 2px;
  animation: bar-stretch var(--animation-duration, 1s) ease-in-out infinite;
}

@keyframes bar-stretch {
  0%, 40%, 100% {
    transform: scaleY(0.5);
  }
  20% {
    transform: scaleY(1);
  }
}

/* 涟漪spinner */
.ripple-spinner {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ripple {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid;
  border-radius: 50%;
  animation: ripple-expand var(--animation-duration, 1s) ease-out infinite;
}

.ripple:nth-child(1) { animation-delay: 0s; }
.ripple:nth-child(2) { animation-delay: 0.3s; }
.ripple:nth-child(3) { animation-delay: 0.6s; }

@keyframes ripple-expand {
  0% {
    transform: scale(0.3);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式调整 */
@media (max-width: 480px) {
  .loading-message {
    font-size: 0.8rem;
  }

  .progress-info {
    width: 100px;
  }

  .progress-text {
    font-size: 0.7rem;
    min-width: 30px;
  }
}
</style>