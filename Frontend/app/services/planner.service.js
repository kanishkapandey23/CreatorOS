import { api } from '@/lib/api';

export const plannerService = {
  async getWeek(offset = 0) {
    const res = await api.get('/planner/week', { params: { offset } });
    return res.data;
  },
  async scheduleDraft(draftId, { scheduledAt, scheduledDay, dayIso, reminderEnabled, reminderOffsets, reminderChannels }) {
    const res = await api.post(`/drafts/${draftId}/schedule`, {
      scheduledAt, scheduledDay, dayIso, reminderEnabled, reminderOffsets, reminderChannels,
    });
    return res.data;
  },
  async updateReminders(draftId, payload) {
    const res = await api.patch(`/drafts/${draftId}/reminders`, payload);
    return res.data;
  },
};
