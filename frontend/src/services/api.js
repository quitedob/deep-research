import { request } from '@/api/client.js';
import { chatAPI } from '@/api/index.js';

export const uploadSingleFile = (file) => {
  const form = new FormData();
  form.append('file', file);
  return request('/api/rag/upload-document', { method: 'POST', body: form });
};

export const feedbackAPI = {
  submitFeedback: (messageId, rating, feedbackType = 'rating', context = {}) => request('/api/feedback/submit', {
    method: 'POST', body: JSON.stringify({ message_id: messageId, rating, feedback_type: feedbackType, context })
  }),
  getMessageFeedback: messageId => request(`/api/feedback/message/${messageId}`),
  deleteFeedback: messageId => request(`/api/feedback/message/${messageId}`, { method: 'DELETE' })
};

export const evidenceAPI = {
  getConversationEvidence: (id, limit = 50, offset = 0) => request(`/api/evidence/conversation/${id}`, { params: { limit, offset } }),
  getResearchEvidence: (id, limit = 50, offset = 0) => request(`/api/evidence/research/${id}`, { params: { limit, offset } }),
  markEvidenceUsed: (id, used) => request(`/api/evidence/${id}/mark_used`, { method: 'PUT', body: JSON.stringify({ used }) }),
  verifyEvidence: (id, verified) => request(`/api/evidence/${id}/verify`, { method: 'PUT', body: JSON.stringify({ verified }) }),
  getEvidenceStats: () => request('/api/evidence/stats')
};

export const healthAPI = {
  checkHealth: () => request('/health'),
  getDetailedHealth: () => request('/health'),
  getPerformanceStats: () => request('/health')
};
export const getProviders = () => chatAPI.getModels();
