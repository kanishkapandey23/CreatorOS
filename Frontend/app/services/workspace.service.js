import { MOCK_STORIES } from '@/lib/mock-data';

function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }

export const workspaceService = {
  async getHome() {
    await delay(120);
    return {
      continueReflection: {
        id: 'ref_001',
        title: 'Tuesday Reflection',
        progress: 3,
        total: 6,
      },
      recentStories: MOCK_STORIES.slice(0, 3),
      weeklyPlan: [
        { day: 'Mon', title: 'Founder coffee story', status: 'draft' },
        { day: 'Wed', title: 'Lessons from 0→1', status: 'scheduled' },
        { day: 'Fri', title: 'Why I quit my job', status: 'idea' },
      ],
      balance: { story: 60, lesson: 25, opinion: 15 },
    };
  },
  async getDraft(storyId) {
    await delay(120);
    return {
      storyId,
      sections: {
        hook: 'I almost shut down the company on a Tuesday morning.',
        experience: '',
        conflict: '',
        lesson: '',
        cta: '',
      },
      updatedAt: new Date().toISOString(),
    };
  },
  async saveDraft(_payload) {
    await delay(100);
    return { ok: true, savedAt: new Date().toISOString() };
  },
};
