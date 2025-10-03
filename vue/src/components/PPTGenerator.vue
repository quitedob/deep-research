<template>
  <div class="ppt-generator">
    <div class="ppt-header">
      <h2>AI PPT 生成器</h2>
      <button @click="$emit('close')" class="close-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>

    <div class="ppt-content">
      <!-- 步骤指示器 -->
      <div class="steps-indicator">
        <div :class="['step', { active: currentStep === 1, completed: currentStep > 1 }]">
          <div class="step-number">1</div>
          <div class="step-label">基本信息</div>
        </div>
        <div class="step-line"></div>
        <div :class="['step', { active: currentStep === 2, completed: currentStep > 2 }]">
          <div class="step-number">2</div>
          <div class="step-label">内容设置</div>
        </div>
        <div class="step-line"></div>
        <div :class="['step', { active: currentStep === 3 }]">
          <div class="step-number">3</div>
          <div class="step-label">生成预览</div>
        </div>
      </div>

      <!-- 步骤1: 基本信息 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="form-group">
          <label>PPT标题 *</label>
          <input 
            v-model="formData.title" 
            type="text" 
            placeholder="例如：人工智能技术发展趋势"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label>主题描述</label>
          <textarea 
            v-model="formData.topic" 
            placeholder="简要描述PPT的主题内容（可选，如果不填写大纲则必填）"
            class="form-textarea"
            rows="3"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>幻灯片数量</label>
            <input 
              v-model.number="formData.n_slides" 
              type="number" 
              min="3" 
              max="50"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label>语言</label>
            <select v-model="formData.language" class="form-select">
              <option value="Chinese">中文</option>
              <option value="English">英文</option>
            </select>
          </div>

          <div class="form-group">
            <label>风格</label>
            <select v-model="formData.tone" class="form-select">
              <option value="professional">专业</option>
              <option value="casual">轻松</option>
              <option value="creative">创意</option>
            </select>
          </div>
        </div>

        <div class="step-actions">
          <button @click="nextStep" class="btn-primary" :disabled="!formData.title">
            下一步
          </button>
        </div>
      </div>

      <!-- 步骤2: 内容设置 -->
      <div v-if="currentStep === 2" class="step-content">
        <div class="form-group">
          <label>
            PPT大纲
            <span class="label-hint">（每行一个要点，留空则自动生成）</span>
          </label>
          <div class="outline-editor">
            <div 
              v-for="(item, index) in formData.outline" 
              :key="index" 
              class="outline-item"
            >
              <span class="outline-number">{{ index + 1 }}</span>
              <input 
                v-model="formData.outline[index]" 
                type="text" 
                placeholder="输入大纲要点"
                class="outline-input"
                @keydown.enter="addOutlineItem"
              />
              <button 
                @click="removeOutlineItem(index)" 
                class="btn-remove"
                v-if="formData.outline.length > 1"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
          <button @click="addOutlineItem" class="btn-add-outline">
            + 添加大纲项
          </button>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="btn-secondary">
            上一步
          </button>
          <button @click="generatePPT" class="btn-primary" :disabled="isGenerating">
            {{ isGenerating ? '生成中...' : '开始生成' }}
          </button>
        </div>
      </div>

      <!-- 步骤3: 生成预览 -->
      <div v-if="currentStep === 3" class="step-content">
        <div v-if="isGenerating" class="generating-status">
          <div class="spinner"></div>
          <p>正在生成PPT，请稍候...</p>
          <p class="status-detail">{{ generatingStatus }}</p>
        </div>

        <div v-else-if="generatedResult" class="result-success">
          <div class="success-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h3>PPT生成成功！</h3>
          <div class="result-info">
            <p><strong>标题：</strong>{{ generatedResult.title }}</p>
            <p><strong>幻灯片数量：</strong>{{ generatedResult.slides_count }}</p>
            <p><strong>生成时间：</strong>{{ formatDate(generatedResult.created_at) }}</p>
          </div>
          <div class="result-actions">
            <a 
              :href="getDownloadUrl(generatedResult.path)" 
              download 
              class="btn-download"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              下载PPT
            </a>
            <button @click="resetForm" class="btn-secondary">
              生成新的PPT
            </button>
          </div>
        </div>

        <div v-else-if="error" class="result-error">
          <div class="error-icon">⚠️</div>
          <h3>生成失败</h3>
          <p class="error-message">{{ error }}</p>
          <div class="error-actions">
            <button @click="retryGenerate" class="btn-primary">
              重试
            </button>
            <button @click="prevStep" class="btn-secondary">
              返回修改
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { apiRequest } from '@/services/api';

const emit = defineEmits(['close']);

const currentStep = ref(1);
const isGenerating = ref(false);
const generatingStatus = ref('');
const generatedResult = ref(null);
const error = ref(null);

const formData = reactive({
  title: '',
  topic: '',
  outline: [''],
  n_slides: 10,
  language: 'Chinese',
  tone: 'professional'
});

const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++;
  }
};

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
};

const addOutlineItem = () => {
  formData.outline.push('');
};

const removeOutlineItem = (index) => {
  if (formData.outline.length > 1) {
    formData.outline.splice(index, 1);
  }
};

const generatePPT = async () => {
  isGenerating.value = true;
  error.value = null;
  currentStep.value = 3;
  generatingStatus.value = '正在准备生成...';

  try {
    // 过滤空的大纲项
    const outline = formData.outline.filter(item => item.trim());
    
    const payload = {
      title: formData.title,
      n_slides: formData.n_slides,
      language: formData.language,
      tone: formData.tone
    };

    // 如果有大纲则使用大纲，否则使用主题
    if (outline.length > 0) {
      payload.outline = outline;
    } else if (formData.topic) {
      payload.topic = formData.topic;
    } else {
      payload.topic = formData.title;
    }

    generatingStatus.value = '正在调用AI生成PPT...';

    const response = await apiRequest('/ppt/presentation/create', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    generatedResult.value = response;
    generatingStatus.value = '生成完成！';
  } catch (err) {
    console.error('PPT生成失败:', err);
    error.value = err.message || '生成失败，请重试';
  } finally {
    isGenerating.value = false;
  }
};

const retryGenerate = () => {
  error.value = null;
  generatePPT();
};

const resetForm = () => {
  currentStep.value = 1;
  formData.title = '';
  formData.topic = '';
  formData.outline = [''];
  formData.n_slides = 10;
  formData.language = 'Chinese';
  formData.tone = 'professional';
  generatedResult.value = null;
  error.value = null;
};

const getDownloadUrl = (path) => {
  // 构建下载URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  return `${baseUrl}/files/${path.split('/').pop()}`;
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN');
};
</script>

<style scoped>
.ppt-generator {
  background: var(--primary-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ppt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.ppt-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.ppt-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--border-color);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s;
}

.step.active .step-number {
  background: var(--accent-color);
  color: white;
}

.step.completed .step-number {
  background: var(--success-color);
  color: white;
}

.step-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.step.active .step-label {
  color: var(--text-primary);
  font-weight: 500;
}

.step-line {
  width: 80px;
  height: 2px;
  background: var(--border-color);
  margin: 0 16px;
}

/* 表单样式 */
.step-content {
  max-width: 600px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-primary);
}

.label-hint {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: normal;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--secondary-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--accent-color);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

/* 大纲编辑器 */
.outline-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.outline-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.outline-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.outline-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--secondary-bg);
  color: var(--text-primary);
  font-size: 14px;
}

.btn-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.btn-remove:hover {
  color: var(--error-color);
}

.btn-add-outline {
  padding: 8px 16px;
  background: var(--secondary-bg);
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-add-outline:hover {
  border-color: var(--accent-color);
  color: var(--accent-color);
}

/* 按钮样式 */
.step-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
}

.btn-primary,
.btn-secondary,
.btn-download {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: var(--accent-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--secondary-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--border-color);
}

.btn-download {
  background: var(--success-color);
  color: white;
  text-decoration: none;
}

.btn-download:hover {
  background: #27ae60;
}

/* 生成状态 */
.generating-status {
  text-align: center;
  padding: 48px 24px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 24px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-detail {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 8px;
}

/* 结果显示 */
.result-success,
.result-error {
  text-align: center;
  padding: 48px 24px;
}

.success-icon {
  color: var(--success-color);
  margin-bottom: 24px;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 24px;
}

.result-info {
  background: var(--secondary-bg);
  border-radius: 8px;
  padding: 20px;
  margin: 24px 0;
  text-align: left;
}

.result-info p {
  margin: 8px 0;
  color: var(--text-primary);
}

.error-message {
  color: var(--error-color);
  margin: 16px 0;
}

.result-actions,
.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}
</style>
