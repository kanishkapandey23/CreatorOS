import { api } from '@/lib/api';

export const reflectionService = {
  async getActiveSession() {
    const res = await api.get('/reflections/active');
    return res.data;
  },
  async startWithVibe({ mood, goal }) {
    const res = await api.post('/reflections/start', { mood, goal });
    return res.data;
  },
  async saveAnswer({ promptId, promptTitle, value }) {
    const res = await api.post('/reflections/answer', {
      promptId,
      promptTitle,
      value,
    });
    return res.data;
  },
  async complete(sessionId) {
    const res = await api.post(`/reflections/complete/${sessionId}`);
    return res.data;
  },
  async extractStories(sessionId) {
    const res = await api.post(`/reflections/${sessionId}/extract-stories`);
    return res.data;
  },
  async saveStories(sessionId, stories) {
    const res = await api.post(`/reflections/${sessionId}/save-stories`, { stories });
    return res.data;
  },
};
