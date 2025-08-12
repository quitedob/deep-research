<template>
  <div class="settings-modal-overlay" @click.self="closeModal">
    <div class="settings-modal-content">
      <button class="close-button" @click="closeModal">×</button>
      <div class="settings-layout">
        <aside class="settings-sidebar">
          <h2>设置</h2>
          <ul>
            <li
                v-for="section in sections"
                :key="section.id"
                :class="{ active: currentSection === section.id }"
                @click="currentSection = section.id"
            >
              {{ section.name }}
            </li>
          </ul>
        </aside>

        <main class="settings-main-content">
          <GeneralSettings v-if="currentSection === 'general'" :current-theme="currentTheme" @toggle-theme="$emit('toggle-theme')" />
          <DataManagementSettings v-if="currentSection === 'data'" />
          <PersonalizationSettings v-if="currentSection === 'personalization'" />
          <SubscriptionSettings v-if="currentSection === 'subscription'" />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useChatStore } from '@/store';
import GeneralSettings from './settings/GeneralSettings.vue';
import DataManagementSettings from './settings/DataManagementSettings.vue';
import PersonalizationSettings from './settings/PersonalizationSettings.vue';
import SubscriptionSettings from './settings/SubscriptionSettings.vue';

// Props 和 Emits 用于主题切换
const props = defineProps({
  currentTheme: String
});
const emit = defineEmits(['toggle-theme']);

const chatStore = useChatStore();
const currentSection = ref('general'); // 默认显示通用设置

const sections = ref([
  { id: 'general', name: '通用设置' },
  { id: 'data', name: '数据管理' },
  { id: 'personalization', name: '个性化' },
  { id: 'subscription', name: '订阅' },
]);

const closeModal = () => {
  chatStore.closeSettingsModal();
};
</script>

<style scoped>
.settings-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.settings-modal-content {
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  border-radius: 12px;
  width: 90%;
  max-width: 960px;
  height: 80%;
  max-height: 700px;
  box-shadow: 0 5px 25px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  position: relative;
}

.close-button {
  position: absolute;
  top: 15px;
  right: 20px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 28px;
  cursor: pointer;
}

.settings-layout {
  display: flex;
  flex-grow: 1;
  overflow: hidden; /* 重要：防止内部滚动条影响布局 */
}

.settings-sidebar {
  width: 240px;
  flex-shrink: 0;
  background-color: var(--primary-bg); /* 稍深一层背景 */
  padding: 20px;
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}
.settings-sidebar h2 {
  font-size: 20px;
  margin-top: 10px;
  margin-bottom: 30px;
  padding-left: 10px;
}
.settings-sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.settings-sidebar li {
  padding: 12px 15px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  font-size: 15px;
}
.settings-sidebar li:hover {
  background-color: var(--hover-bg);
}
.settings-sidebar li.active {
  background-color: var(--button-bg);
  color: var(--button-text);
  font-weight: 500;
}

.settings-main-content {
  flex-grow: 1;
  padding: 30px 40px;
  overflow-y: auto;
}
</style>