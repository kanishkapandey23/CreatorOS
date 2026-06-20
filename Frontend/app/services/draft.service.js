import { api } from '@/lib/api';

export const DRAFT_FORMATS = [
  { id: 'linkedin_post', label: 'LinkedIn Post' },
  { id: 'instagram_reel', label: 'Instagram Reel' },
  { id: 'carousel', label: 'Carousel' },
  { id: 'twitter_thread', label: 'Twitter Thread' },
];

export const draftService = {
  async listByStory(storyId) {
    const res = await api.get(`/stories/${storyId}/drafts`);
    return res.data;
  },
  async get(draftId) {
    const res = await api.get(`/drafts/${draftId}`);
    return res.data;
  },
  async create(storyId, format) {
    const res = await api.post(`/stories/${storyId}/drafts`, { format });
    return res.data;
  },
  async update(draftId, payload) {
    const res = await api.patch(`/drafts/${draftId}`, payload);
    return res.data;
  },
  async save(draftId, sections) {
    const res = await api.post(`/drafts/${draftId}/save`, { sections });
    return res.data;
  },
  async remove(draftId) {
    const res = await api.delete(`/drafts/${draftId}`);
    return res.data;
  },
};
