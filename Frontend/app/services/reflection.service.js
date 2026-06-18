import { REFLECTION_PROMPTS } from '@/lib/mock-data';

function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }

export const reflectionService = {
  async getActiveSession() {
    await delay(120);
    return {
      id: 'ref_001',
      title: 'Weekly Reflection Nudge',
      prompts: REFLECTION_PROMPTS,
    };
  },
  async saveAnswer({ promptId, value }) {
    await delay(100);
    return { success: true };
  },
  async complete(sessionId) {
    await delay(200);
    return { success: true, storiesDiscovered: 3 };
  },
};
