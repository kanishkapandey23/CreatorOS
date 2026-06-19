import { api } from '@/lib/api';

const TOKEN_KEY = 'creatoros:token';
const USER_KEY = 'creatoros:user';

function apiOrigin() {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';
  return base.replace(/\/api\/?$/, '');
}

function readUser() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeUser(user) {
  if (typeof window === 'undefined') return;
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
}

function writeToken(token) {
  if (typeof window === 'undefined') return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function toClientUser(profile) {
  return {
    id: profile.id,
    email: profile.email,
    name: profile.name || profile.email.split('@')[0],
    avatarUrl: null,
    handle: (profile.name || profile.email).split('@')[0].toLowerCase().replace(/\s+/g, ''),
    plan: 'beta',
    createdAt: profile.created_at,
    niche: profile.niche,
  };
}

async function fetchAndStoreProfile() {
  const res = await api.get('/auth/me');
  const user = toClientUser(res.data);
  writeUser(user);
  return user;
}

export const authService = {
  async getSession() {
    const token = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
    if (!token) return null;
    try {
      return await fetchAndStoreProfile();
    } catch {
      writeToken(null);
      writeUser(null);
      return null;
    }
  },

  async signIn({ email, password }) {
    const res = await api.post('/auth/login', { email, password });
    writeToken(res.data.access_token);
    return fetchAndStoreProfile();
  },

  async signUp({ email, password, name }) {
    const res = await api.post('/auth/register', { email, password, name });
    writeToken(res.data.access_token);
    return fetchAndStoreProfile();
  },

  async getOAuthProviders() {
    const res = await api.get('/auth/oauth/providers');
    return res.data.providers || [];
  },

  signInWithOAuth(provider) {
    window.location.assign(`${apiOrigin()}/api/auth/oauth/${provider}`);
  },

  async requestPasswordReset(_email) {
    throw new Error('Password reset is not configured yet.');
  },

  async signOut() {
    writeToken(null);
    writeUser(null);
    return { ok: true };
  },
};
