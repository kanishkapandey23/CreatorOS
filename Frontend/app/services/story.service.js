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
  async create(payload) {
    const res = await api.post('/stories', payload);
    return res.data;
  },
};
