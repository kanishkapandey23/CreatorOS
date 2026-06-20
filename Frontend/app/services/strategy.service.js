import { api } from '@/lib/api';

export const strategyService = {
  async getTrends(mood = 'reflective', format = 'linkedin_post') {
    const res = await api.get('/strategy/trends', { params: { mood, format } });
    return res.data;
  },
  async getRecommendations(payload) {
    const res = await api.post('/strategy/recommendations', payload);
    return res.data;
  },
  // Legacy chat endpoints (kept for compatibility)
  async listSessions() {
    const res = await api.get('/strategy/chat/sessions');
    return res.data;
  },
  async startSession(memoryId = null) {
    const res = await api.post('/strategy/chat/sessions', { memoryId });
    return res.data;
  },
  async getSessionDetails(sessionId) {
    const res = await api.get(`/strategy/chat/sessions/${sessionId}`);
    return res.data;
  },
  async sendMessage(sessionId, message) {
    const res = await api.post(`/strategy/chat/sessions/${sessionId}/message`, { message });
    return res.data;
  },
  async submitFeedback(storyId, feedback) {
    const res = await api.post(`/stories/${storyId}/feedback`, { feedback });
    return res.data;
  },
  async listMemories() {
    const res = await api.get('/memories');
    return res.data;
  },
  async getStory(storyId) {
    const res = await api.get(`/stories/${storyId}`);
    return res.data;
  },
};
