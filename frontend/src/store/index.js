import { healthAPI, getProviders } from '@/services/api.js';
// src/store/index.js
import { defineStore } from 'pinia';
import { getAuthGeneration } from '@/api/client.js';
import { notificationManager as notifications } from '@/composables/useNotifications.js';
import { chatAPI } from '@/api/index';

export const useChatStore = defineStore('chat', {
    state: () => ({
        currentModel: 'deepseek-flash', // 默认视觉语言模型
        messages: [],
        historyList: [],
        activeSessionId: null,
        isTyping: false,
        isSettingsModalOpen: false,
        currentRequestController: null,
        historyRequestToken: null,
        systemStatus: null,
        systemHealth: null,
        systemPerformance: null,
        documentStats: null,
        evidenceStats: null,
        availableProviders: {},
        availableAgents: {},
        connectionStatus: 'disconnected',
        isResearchMode: false, // 是否处于深度研究模式
        researchSessionId: null, // 深度研究会话ID
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
            const messageWithId = { ...message, id: Date.now() + Math.random(), duration: null, persisted: false };
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
            this.historyRequestToken = null;
            if (this.currentRequestController) {
                this.currentRequestController.abort();
                this.currentRequestController = null;
            }
            for (const message of this.messages) {
                if (message.role === 'assistant' && message.content === null) message.content = '已停止生成';
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
            this.historyRequestToken = null;
            this.abortCurrentRequest();
            this.messages = [];
            this.isTyping = false;
            this.activeSessionId = null;
            this.setResearchMode(false);
        },
        startNewChat() {
            // 清空当前聊天
            this.clearChat();
            console.log('开始新对话');
        },
        setResearchMode(isResearch, sessionId = null) {
            this.isResearchMode = isResearch;
            this.researchSessionId = sessionId;
            console.log('研究模式:', isResearch, '会话ID:', sessionId);
        },
        openSettingsModal() { this.isSettingsModalOpen = true; },
        closeSettingsModal() { this.isSettingsModalOpen = false; },
        savePersonalizationSettings(settings) {
            this.personalizationSettings = { ...this.personalizationSettings, ...settings };
            console.log('个性化设置已保存:', this.personalizationSettings);
        },
        updateMessageContent({ messageId, contentChunk, keepThinking = false, metadata = null }) {
            if (!keepThinking && typeof contentChunk !== 'string') throw new TypeError('消息内容必须为文本');
            const message = this.messages.find(m => m.id === messageId);
            if (message) {
                // 如果 keepThinking 为 true，保持 content 为 null 以继续显示动画
                if (keepThinking) {
                    // 不更新 content，保持为 null
                    // 但可以更新 metadata
                    if (metadata) {
                        message.metadata = { ...message.metadata, ...metadata };
                    }
                } else {
                    // 正常更新内容
                    if (message.content === null) {
                        message.content = '';
                    }
                    message.content += contentChunk;
                    
                    // 更新 metadata
                    if (metadata) {
                        message.metadata = { ...message.metadata, ...metadata };
                    }
                }
            }
        },
        async fetchHistoryList() {
            const generation = getAuthGeneration();
            try {
                const sessions = await chatAPI.getSessions();
                if (generation !== getAuthGeneration()) return;
                this.historyList = sessions.map(session => ({
                    id: session.id,
                    title: session.title || '新对话',
                    last_message: session.last_message || '',
                    message_count: session.message_count || 0,
                    updated_at: session.updated_at ? new Date(session.updated_at) : new Date(),
                    created_at: session.created_at ? new Date(session.created_at) : new Date(),
                    pinned: false // 可以后续从后端获取
                }));
                console.log('历史列表加载成功:', this.historyList.length, '个会话');
            } catch (error) {
                console.error("获取历史列表失败:", error);
                if (generation === getAuthGeneration()) {
                    this.historyList = [];
                    notifications.error(`加载历史失败：${error.message}`);
                }
            }
        },
        async loadHistory(sessionId) {
            const generation = getAuthGeneration();
            const requestToken = Symbol('history request');
            this.abortCurrentRequest();
            this.historyRequestToken = requestToken;
            const isCurrent = () => generation === getAuthGeneration() && this.historyRequestToken === requestToken;
            this.isTyping = true;
            try {
                const messages = await chatAPI.getMessages(sessionId);
                if (!isCurrent()) return;
                this.messages = messages.map(m => ({
                    ...m,
                    id: m.id || (Math.random() + Date.now()), // Use existing ID or generate one
                    role: m.role.toLowerCase(),
                }));
                this.activeSessionId = sessionId;
            } catch (error) {
                console.error("加载历史消息失败:", error);
                if (!isCurrent()) return;
                this.addMessage({ role: 'assistant', content: `加载会话失败: ${error.message}` });
            } finally {
                if (isCurrent()) this.isTyping = false;
            }
        },
        async deleteAllHistories(generation = getAuthGeneration()) {
            // Always request the first page again as deletion changes offsets.
            const isCurrent = () => generation === getAuthGeneration();
            if (!isCurrent()) return false;
            this.abortCurrentRequest();
            let sessions;
            try {
                while (isCurrent()) {
                    sessions = await chatAPI.getSessions(100);
                    if (!isCurrent()) return false;
                    if (!sessions.length) break;
                    await Promise.all(sessions.map(session => chatAPI.deleteSession(session.id)));
                    if (!isCurrent()) return false;
                }
                if (!isCurrent()) return false;
                this.historyList = [];
                this.clearChat();
                return true;
            } catch (error) {
                if (!isCurrent()) return false;
                await this.fetchHistoryList();
                if (!isCurrent()) return false;
                throw error;
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
