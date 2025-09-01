<template>
  <div class="settings-section personalization-section">
    <h3>个性化</h3>
    <p class="description">介绍自己，以获得更好、更个性化的回复。</p>

    <div class="form-group">
      <label for="userNickname">DeepSeek 应该怎么称呼您？</label>
      <input type="text" id="userNickname" v-model="settings.userNickname" placeholder="帅哥">
    </div>

    <div class="form-group">
      <label for="userProfession">您是做什么的？</label>
      <input type="text" id="userProfession" v-model="settings.userProfession" placeholder="金融行业从业者、画家、学生...">
    </div>

    <div class="form-group">
      <label for="chatGptCharacteristics">您希望 DeepSeek 具备哪些特征？（例如：健谈、严谨等）</label>
      <textarea id="chatGptCharacteristics" v-model="settings.chatGptCharacteristics" rows="4" placeholder="请详细描述您期望的AI交流风格、知识领域偏好等..."></textarea>
    </div>

    <div class="form-group">
      <label for="additionalInfo">还需要了解的其他信息吗？（例如：兴趣、价值观或偏好）</label>
      <textarea id="additionalInfo" v-model="settings.additionalInfo" rows="3" placeholder="需要记住的兴趣、价值观或偏好"></textarea>
    </div>

    <div class="form-actions">
      <button class="save-button" @click="saveSettings">保存</button>
      <button class="cancel-button" @click="cancelSettings">取消</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useChatStore } from '@/store';

const chatStore = useChatStore();
const settings = ref({
  userNickname: '',
  userProfession: '',
  chatGptCharacteristics: '',
  additionalInfo: '',
});

// 组件挂载时，加载已保存的设置
onMounted(() => {
  settings.value = { ...chatStore.personalizationSettings };
});

const saveSettings = () => {
  chatStore.savePersonalizationSettings(settings.value);
  // 可以选择保存后关闭弹窗
  // chatStore.closeSettingsModal();
};

const cancelSettings = () => {
  // 重置为 Pinia store 中的值
  settings.value = { ...chatStore.personalizationSettings };
  // 或直接关闭弹窗
  // chatStore.closeSettingsModal();
};
</script>

<style scoped>
.personalization-section h3 { font-size: 18px; margin-bottom: 8px; }
.personalization-section .description { font-size: 14px; color: var(--text-secondary); margin-bottom: 25px;}

.form-group { margin-bottom: 20px; }
.form-group label {
  display: block;
  font-size: 15px;
  margin-bottom: 8px;
  color: var(--text-primary);
}
.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  box-sizing: border-box;
}
.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
}
.form-actions button {
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  font-size: 15px;
  cursor: pointer;
}
.save-button {
  background-color: var(--button-bg);
  color: var(--button-text);
}
.cancel-button {
  background-color: var(--secondary-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
</style>