// src/store/index.js
import { defineStore } from 'pinia';
export const useChatStore = defineStore('chat', {
    state: () => ({
        currentModel: 'ollama', // 默认使用ollama提供者
        // messages 数组现在可以包含不同类型的消息对象
        messages: [],
        isTyping: false,
        isSettingsModalOpen: false,
        // (新增) 用于中止请求的控制器
        currentRequestController: null,
        // 系统状态
        systemStatus: null,
        availableProviders: {},
        availableAgents: {},
        connectionStatus: 'disconnected', // disconnected, connecting, connected, error
        personalizationSettings: {
            userNickname: '',
            userProfession: '',
            chatGptCharacteristics: '',
            additionalInfo: '',
            enableForNewChats: true,
        },
    }),
    actions: {
        setModel(modelName) { this.currentModel = modelName; },
        addMessage(message) {
            // 为每个消息添加一个唯一ID和初始时长
            const messageWithId = { ...message, id: Date.now() + Math.random(), duration: null };
            this.messages.push(messageWithId);
            return messageWithId.id;
        },
        // (新增) 为特定消息设置时长
        setMessageDuration(messageId, duration) {
            const message = this.messages.find(m => m.id === messageId);
            if (message) {
                message.duration = duration;
            }
        },
        // (新增) 设置当前请求的 AbortController
        setCurrentRequestController(controller) {
            this.currentRequestController = controller;
        },
        // (新增) 中止当前请求
        abortCurrentRequest() {
            if (this.currentRequestController) {
                this.currentRequestController.abort();
                this.currentRequestController = null;
            }
            this.setTypingStatus(false);
        },
        // (新增) 从指定索引处替换消息历史
        replaceMessagesFromIndex(startIndex, newMessages = []) {
            this.messages.splice(startIndex);
            if (Array.isArray(newMessages) && newMessages.length > 0) {
                this.messages.push(...newMessages);
            }
        },
        setTypingStatus(status) { this.isTyping = status; },
        clearChat() {
            this.abortCurrentRequest(); // 清空时也中止正在进行的请求
            this.messages = [];
            this.isTyping = false;
        },
        openSettingsModal() { this.isSettingsModalOpen = true; },
        closeSettingsModal() { this.isSettingsModalOpen = false; },
        savePersonalizationSettings(settings) {
            this.personalizationSettings = { ...this.personalizationSettings, ...settings };
            console.log('个性化设置已保存:', this.personalizationSettings);
        },
        updateMessageContent({ messageId, contentChunk }) {
            const message = this.messages.find(m => m.id === messageId);
            if (message) {
                if (message.content === null) { // 第一次接收到数据块
                    message.content = '';
                }
                message.content += contentChunk;
            }
        },
        // 系统状态管理
        setConnectionStatus(status) {
            this.connectionStatus = status;
        },
        setSystemStatus(status) {
            this.systemStatus = status;
        },
        setAvailableProviders(providers) {
            this.availableProviders = providers;
        },
        setAvailableAgents(agents) {
            this.availableAgents = agents;
        },
        // 检查系统连接状态
        async checkConnection() {
            this.setConnectionStatus('connecting');
            try {
                const { getSystemStatus } = await import('@/services/api.js');
                const status = await getSystemStatus();
                this.setSystemStatus(status);
                this.setAvailableProviders(status.providers || {});
                this.setAvailableAgents(status.agents || {});
                this.setConnectionStatus('connected');
                return true;
            } catch (error) {
                console.error('连接检查失败:', error);
                this.setConnectionStatus('error');
                return false;
            }
        },
        // 获取可用的提供者列表
        async fetchProviders() {
            try {
                const { getProviders } = await import('@/services/api.js');
                const providers = await getProviders();
                this.setAvailableProviders(providers);
                return providers;
            } catch (error) {
                console.error('获取提供者列表失败:', error);
                throw error;
            }
        }
    }
});