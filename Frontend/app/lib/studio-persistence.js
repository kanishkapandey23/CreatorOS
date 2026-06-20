const LAST_STUDIO_KEY = 'creatoros:lastStudio';

export function saveLastStudio(storyId, draftId) {
  if (typeof window === 'undefined' || !storyId || !draftId) return;
  localStorage.setItem(LAST_STUDIO_KEY, JSON.stringify({ storyId, draftId, path: `/stories/${storyId}/studio/${draftId}` }));
}

export function getLastStudio() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(LAST_STUDIO_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearLastStudio(storyId) {
  if (typeof window === 'undefined') return;
  const last = getLastStudio();
  if (last?.storyId === storyId) {
    localStorage.removeItem(LAST_STUDIO_KEY);
  }
}

// Legacy aliases during migration
export const saveLastWorkspace = (storyId) => saveLastStudio(storyId, null);
export const getLastWorkspace = () => {
  const s = getLastStudio();
  if (!s) return null;
  return { storyId: s.storyId, path: s.path || `/stories/${s.storyId}/studio` };
};
export const clearLastWorkspace = clearLastStudio;
