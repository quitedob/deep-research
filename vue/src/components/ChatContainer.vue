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
              :conversation-id="chatStore.activeSessionId"
              :is-research-mode="chatStore.isResearchMode"
              :research-session-id="chatStore.researchSessionId"
              @edit-and-send="emit('edit-and-send', $event)"
              @regenerate="emit('regenerate', $event)"
              @evidence-updated="emit('evidence-updated', $event)"
          />
          <ResearchActivities v-if="msg.type === 'activities'" :activities="msg.payload" />
          <ResearchReport v-if="msg.type === 'report'" :report="msg.payload" />
        </div>
        <!-- The TypingIndicator component is no longer needed here as it's handled inside MessageItem -->
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
    'evidence-updated',
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
  padding: var(--spacing-md) var(--spacing-lg);
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--secondary-bg);
  z-index: 10;
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
}

.scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  scroll-behavior: smooth;
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
  padding: var(--spacing-xl) var(--spacing-lg);
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
  letter-spacing: -0.032em;
  background: var(--gradient-blue);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xl);
  max-width: 600px;
  line-height: 1.5;
  font-weight: 400;
}

.scenario-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
  width: 100%;
  max-width: 600px;
}

.messages-list {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Responsive Design */
@media (max-width: 768px) {
  .chat-header {
    padding: var(--spacing-sm) var(--spacing-md);
  }

  .scroll-area {
    padding: var(--spacing-md);
  }

  .welcome-title {
    font-size: 28px;
  }

  .welcome-subtitle {
    font-size: 16px;
  }

  .scenario-cards {
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }
}

@media (max-width: 480px) {
  .scroll-area {
    padding: var(--spacing-sm);
  }

  .welcome-message {
    padding: var(--spacing-lg) var(--spacing-md);
  }

  .welcome-title {
    font-size: 24px;
  }

  .welcome-subtitle {
    font-size: 14px;
  }
}
</style>