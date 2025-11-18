<template>
  <div class="message ai-message">
    <div class="avatar ai-avatar">AI</div>
    <div class="message-content">
      <div class="typing-indicator">
        <div class="typing-text">AI 正在思考中</div>
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// /src/components/TypingIndicator.vue
// 这是一个纯展示性组件，不需要任何 JavaScript 逻辑。
</script>

<style scoped>
/* /src/components/TypingIndicator.vue 的局部样式 */
.message {
  display: flex;
  gap: 15px;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  background: var(--primary);
}
.message-content {
  flex: 1;
  padding: 15px;
  border-radius: 12px;
  background: #eef2ff;
}
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--dark);
}

.typing-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-dot {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

/* 为每个点设置动画延迟，形成跳动效果 */
.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }
.typing-dot:nth-child(3) { animation-delay: 0s; }

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1.0);
  }
}
</style>