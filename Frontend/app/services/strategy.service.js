import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export const strategyService = {
  async listSessions() {
    const res = await axios.get(`${API_BASE}/strategy/chat/sessions`);
    return res.data;
  },
  async startSession(memoryId = null) {
    const res = await axios.post(`${API_BASE}/strategy/chat/sessions`, {
      memoryId,
    });
    return res.data;
  },
  async getSessionDetails(sessionId) {
    const res = await axios.get(`${API_BASE}/strategy/chat/sessions/${sessionId}`);
    return res.data;
  },
  async sendMessage(sessionId, message) {
    const res = await axios.post(`${API_BASE}/strategy/chat/sessions/${sessionId}/message`, {
      message,
    });
    return res.data;
  },
  async submitFeedback(storyId, feedback) {
    const res = await axios.post(`${API_BASE}/stories/${storyId}/feedback`, {
      feedback,
    });
    return res.data;
  },
};
