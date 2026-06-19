import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export const workspaceService = {
  async getHome() {
    const res = await axios.get(`${API_BASE}/workspace`);
    return res.data;
  },
  async getDraft(storyId) {
    const res = await axios.get(`${API_BASE}/stories/${storyId}/draft`);
    return res.data;
  },
  async saveDraft(payload) {
    const res = await axios.post(`${API_BASE}/stories/draft`, payload);
    return res.data;
  },
  async getPolishedPreview(storyId, sections) {
    const res = await axios.post(`${API_BASE}/stories/${storyId}/preview`, { sections });
    return res.data;
  },
  async getSuggestions(storyId) {
    const res = await axios.get(`${API_BASE}/stories/${storyId}/suggestions`);
    return res.data;
  },
};
