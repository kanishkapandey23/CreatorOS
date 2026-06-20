export const WORKSPACE_SECTION_IDS = ['hook', 'experience', 'conflict', 'lesson', 'cta', 'caption', 'hashtags'];

const SECTION_ALIASES = {
  hook: 'hook',
  experience: 'experience',
  conflict: 'conflict',
  lesson: 'lesson',
  cta: 'cta',
  caption: 'caption',
  hashtags: 'hashtags',
  context: 'experience',
  problem: 'conflict',
  realization: 'lesson',
  insight: 'lesson',
  takeaway: 'lesson',
  tension: 'conflict',
  story: 'experience',
  narrative: 'experience',
  call_to_action: 'cta',
  calltoaction: 'cta',
};

export function emptySections() {
  return { hook: '', experience: '', conflict: '', lesson: '', cta: '', caption: '', hashtags: '' };
}

export function normalizeSections(raw) {
  const normalized = emptySections();
  if (!raw || typeof raw !== 'object') return normalized;

  for (const [key, value] of Object.entries(raw)) {
    const text = typeof value === 'string' ? value.trim() : '';
    if (!text) continue;

    const alias = SECTION_ALIASES[key.toLowerCase()];
    const target = alias || (WORKSPACE_SECTION_IDS.includes(key) ? key : 'experience');

    normalized[target] = normalized[target] ? `${normalized[target]}\n\n${text}` : text;
  }

  return normalized;
}
