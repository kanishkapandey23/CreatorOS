import { api } from '@/lib/api';

export const storyService = {
  async list() {
    const res = await api.get('/stories');
    return res.data;
  },
  async get(id) {
    const res = await api.get(`/stories/${id}`);
    return res.data;
  },
  async create(payload = {}) {
    const res = await api.post('/stories', {
      title: payload.title || 'Untitled story',
      summary: payload.summary || '',
      category: payload.category || 'General',
      emotion: payload.emotion || 'Growth',
      potential: payload.potential ?? 75,
      tags: payload.tags || [],
      suggestedFormats: payload.suggestedFormats || ['Linkedin post'],
      lesson: payload.lesson || '',
    });
    return res.data;
  },
  async update(id, payload) {
    const res = await api.patch(`/stories/${id}`, payload);
    return res.data;
  },
  async remove(id) {
    const res = await api.delete(`/stories/${id}`);
    return res.data;
  },
};
