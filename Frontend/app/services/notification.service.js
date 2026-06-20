import { api } from '@/lib/api';

export const notificationService = {
  async list() {
    const res = await api.get('/notifications');
    return res.data;
  },
  async markRead(id) {
    const res = await api.post(`/notifications/${id}/read`);
    return res.data;
  },
  async dismiss(id) {
    const res = await api.post(`/notifications/${id}/dismiss`);
    return res.data;
  },
  async markComplete(id) {
    const res = await api.post(`/notifications/${id}/complete`);
    return res.data;
  },
  async getDigest() {
    const res = await api.get('/notifications/digest');
    return res.data;
  },
  async getChannels() {
    const res = await api.get('/notifications/channels');
    return res.data;
  },
};
