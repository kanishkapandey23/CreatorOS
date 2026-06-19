import { api } from '@/lib/api';

export const workspaceService = {
  async getHome() {
    const res = await api.get('/workspace');
    return res.data;
  },
  async getDraft(storyId) {
    const res = await api.get(`/stories/${storyId}/draft`);
    return res.data;
  },
  async saveDraft(payload) {
    const res = await api.post('/stories/draft', payload);
    return res.data;
  },
  async getPolishedPreview(storyId, sections) {
    const res = await api.post(`/stories/${storyId}/preview`, { sections });
    return res.data;
  },
  async getSuggestions(storyId) {
    const res = await api.get(`/stories/${storyId}/suggestions`);
    return res.data;
  },
};
