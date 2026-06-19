import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export const reflectionService = {
  async getActiveSession() {
    const res = await axios.get(`${API_BASE}/reflections/active`);
    return res.data;
  },
  async saveAnswer({ promptId, promptTitle, value }) {
    const res = await axios.post(`${API_BASE}/reflections/answer`, {
      promptId,
      promptTitle,
      value,
    });
    return res.data;
  },
  async complete(sessionId) {
    const res = await axios.post(`${API_BASE}/reflections/complete/${sessionId}`);
    return res.data;
  },
};
