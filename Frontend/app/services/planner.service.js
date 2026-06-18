import { MOCK_PLANNER_WEEK } from '@/lib/mock-data';

function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }

export const plannerService = {
  async getWeek(_offset = 0) {
    await delay(100);
    return MOCK_PLANNER_WEEK;
  },
};
