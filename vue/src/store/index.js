// src/store/index.js
import { defineStore } from 'pinia';
import { fetchHistories, fetchHistoryMessages, deleteAllHistories } from '@/services/api.js';

export const useChatStore = defineStore('chat', {
    state: () => ({
        currentModel: 'ollama', // 默认使用ollama提供者
        messages: [],
        historyList: [],
        activeSessionId: null,
        isTyping: false,
        isSettingsModalOpen: false,
        currentRequestController: null,
        systemStatus: null,
        availableProviders: {},
        availableAgents: {},
        connectionStatus: 'disconnected',
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
            const messageWithId = { ...message, id: Date.now() + Math.random(), duration: null };
            this.messages.push(messageWithId);
            return messageWithId.id;
        },
        setMessageDuration(messageId, duration) {
            const message = this.messages.find(m => m.id === messageId);
            if (message) {
                message.duration = duration;
            }
        },
        setCurrentRequestController(controller) {
            this.currentRequestController = controller;
        },
        abortCurrentRequest() {
            if (this.currentRequestController) {
                this.currentRequestController.abort();
                this.currentRequestController = null;
            }
            this.setTypingStatus(false);
        },
        replaceMessagesFromIndex(startIndex, newMessages = []) {
            this.messages.splice(startIndex);
            if (Array.isArray(newMessages) && newMessages.length > 0) {
                this.messages.push(...newMessages);
            }
        },
        setTypingStatus(status) { this.isTyping = status; },
        clearChat() {
            this.abortCurrentRequest();
            this.messages = [];
            this.isTyping = false;
            this.activeSessionId = null;
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
                if (message.content === null) {
                    message.content = '';
                }
                message.content += contentChunk;
            }
        },
        async fetchHistoryList() {
            const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
            try {
                const histories = await fetchHistories(token);
                this.historyList = histories.map(h => ({
                    id: h.session_id,
                    title: h.title,
                    // icon and active state will be managed dynamically
                }));
            } catch (error) {
                console.error("获取历史列表失败:", error);
                this.historyList = [];
            }
        },
        async loadHistory(sessionId) {
            this.abortCurrentRequest();
            this.isTyping = true;
            const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
            try {
                const messages = await fetchHistoryMessages(sessionId, token);
                this.messages = messages.map(m => ({
                    ...m,
                    id: Math.random() + Date.now(), // Assign a transient ID
                    role: m.role.toLowerCase(),
                }));
                this.activeSessionId = sessionId;
            } catch (error) {
                console.error("加载历史消息失败:", error);
                this.addMessage({ role: 'assistant', content: `加载会话失败: ${error.message}` });
            } finally {
                this.isTyping = false;
            }
        },
        async deleteAllHistories() {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                alert("请先登录");
                return;
            }
            try {
                await deleteAllHistories(token);
                this.historyList = [];
                if (this.activeSessionId) {
                    this.clearChat();
                }
            } catch (error) {
                console.error("删除所有历史记录失败:", error);
                alert(`删除失败: ${error.message}`);
            }
        },
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
        // 系统监控相关状态
        systemHealth: null,
        systemPerformance: null,
        documentStats: null,
        evidenceStats: null,

        setSystemHealth(health) {
            this.systemHealth = health;
        },
        setSystemPerformance(performance) {
            this.systemPerformance = performance;
        },
        setDocumentStats(stats) {
            this.documentStats = stats;
        },
        setEvidenceStats(stats) {
            this.evidenceStats = stats;
        },

        async checkConnection() {
            this.setConnectionStatus('connecting');
            try {
                // 检查健康状态
                const { healthAPI } = await import('@/services/api.js');
                const healthResult = await healthAPI.checkHealth();

                this.setSystemStatus(healthResult);
                this.setSystemHealth(healthResult);
                this.setConnectionStatus('connected');

                // 获取性能统计
                try {
                    const performanceResult = await healthAPI.getPerformanceStats();
                    this.setSystemPerformance(performanceResult);
                } catch (error) {
                    console.warn('获取性能统计失败:', error);
                }

                return true;
            } catch (error) {
                console.error('连接检查失败:', error);
                this.setConnectionStatus('error');
                return false;
            }
        },
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
