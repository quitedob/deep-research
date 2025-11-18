// src/store/index.js
import { defineStore } from 'pinia';
import { chatAPI } from '@/api/index';

export const useChatStore = defineStore('chat', {
    state: () => ({
        currentModel: 'glm-4-plus', // 默认使用智谱 GLM-4-Plus 模型
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
            try {
                const sessions = await chatAPI.getSessions();
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
                this.historyList = [];
            }
        },
        async loadHistory(sessionId) {
            this.abortCurrentRequest();
            this.isTyping = true;
            try {
                const messages = await chatAPI.getMessages(sessionId);
                this.messages = messages.map(m => ({
                    ...m,
                    id: m.id || (Math.random() + Date.now()), // Use existing ID or generate one
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
                // 删除所有会话
                const sessions = await chatAPI.getSessions();
                await Promise.all(sessions.map(session => chatAPI.deleteSession(session.id)));
                
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
