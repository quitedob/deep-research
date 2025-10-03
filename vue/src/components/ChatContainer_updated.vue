<template>
  <div class="chat-container">
    <div class="chat-header">
      <ModelSelector />
      <UserProfileMenu :current-theme="currentTheme" @toggle-theme="$emit('toggle-theme')" />
    </div>

    <div class="scroll-area" ref="chatEl">
      <div v-if="chatStore.messages.length === 0" class="welcome-message">
        <div class="welcome-title">AI 智能助手</div>
        <div class="welcome-subtitle">
          基于本地大语言模型，为您提供多种场景的专业支持
        </div>
        <div class="scenario-cards">
          <ScenarioCard
              v-for="card in scenarioCards"
              :key="card.value"
              :title="card.label"
              :description="card.description"
              @click="selectSceneFromCard(card.value)"
          />
        </div>
      </div>

      <div v-else class="messages-list">
        <div v-for="msg in chatStore.messages" :key="msg.id">
          <MessageItem
              v-if="!msg.type"
              :message="msg"
              @edit-and-send="emit('edit-and-send', $event)"
              @regenerate="emit('regenerate', $event)"
          />
          <ResearchActivities v-if="msg.type === 'activities'" :activities="msg.payload" />
          <ResearchReport v-if="msg.type === 'report'" :report="msg.payload" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { useChatStore } from '@/store';
import ScenarioCard from '@/components/ScenarioCard.vue';
import MessageItem from '@/components/MessageItem.vue';
import UserProfileMenu from './UserProfileMenu.vue';
import ModelSelector from './ModelSelector.vue';
import ResearchActivities from './ResearchActivities.vue';
import ResearchReport from './ResearchReport.vue';

defineProps({ currentTheme: String });

// Declare all events the component can emit
const emit = defineEmits([
    'toggle-theme',
    'send-message-from-container',
    'edit-and-send',
    'regenerate',
    'open-ppt-generator'
]);

const chatStore = useChatStore();
const chatEl = ref(null);

const scenarioCards = [
  { value: 'research', label: '研究报告', description: '生成专业的研究报告...' },
  { value: 'ppt', label: 'PPT生成', description: '根据主题创建完整的PPT内容...' },
  { value: 'blog', label: '博客撰写', description: '创作技术博客、行业分析...' },
  { value: 'counseling', label: '心理辅导', description: '提供情感支持、压力疏导...' }
];

const selectSceneFromCard = (scenario) => {
  if (scenario === 'ppt') {
    // 打开PPT生成器
    emit('open-ppt-generator');
  } else {
    const messageText = `你好，我想生成一份关于"${scenario}"的研究报告`;
    emit('send-message-from-container', messageText);
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatEl.value) {
      chatEl.value.scrollTop = chatEl.value.scrollHeight;
    }
  });
};

// Watch for new messages to scroll down
watch(
    () => chatStore.messages.length,
    scrollToBottom
);

// Watch the last message's content length to scroll during streaming
watch(
    () => {
        const lastMessage = chatStore.messages[chatStore.messages.length - 1];
        return lastMessage ? lastMessage.content?.length : 0;
    },
    scrollToBottom
);
</script>

<style scoped>
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--primary-bg);
  overflow: hidden;
  height: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--primary-bg);
  z-index: 10;
}

.scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 25px;
}

.welcome-message {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.welcome-title { font-size: 32px; font-weight: 700; margin-bottom: 20px; }
.welcome-subtitle { font-size: 18px; color: var(--text-secondary); margin-bottom: 40px; max-width: 600px; }

.scenario-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  width: 100%;
  max-width: 600px;
}

.messages-list {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>
