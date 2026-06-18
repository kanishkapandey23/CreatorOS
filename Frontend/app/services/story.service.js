import { MOCK_STORIES } from '@/lib/mock-data';

function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }

export const storyService = {
  async list() {
    await delay(120);
    return [...MOCK_STORIES];
  },
  async get(id) {
    await delay(120);
    return MOCK_STORIES.find((s) => s.id === id) || null;
  },
  async create(_payload) {
    await delay(200);
    return { id: 'new', ...(_payload || {}) };
  },
};
