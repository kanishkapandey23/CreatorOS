/**
 * auth.service — placeholder implementation.
 * Replace with Supabase Auth client in the future. Keep the same surface area.
 */

const STORAGE_KEY = 'creatoros:user';

function delay(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

function read() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function write(user) {
  if (typeof window === 'undefined') return;
  if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  else localStorage.removeItem(STORAGE_KEY);
}

function mockUser(overrides = {}) {
  return {
    id: 'u_demo',
    email: overrides.email || 'maya@creatoros.app',
    name: overrides.name || 'Maya Chen',
    avatarUrl: null,
    handle: 'maya',
    plan: 'beta',
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

export const authService = {
  async getSession() {
    await delay(120);
    const user = read();
    // Return mock user if no session exists (for development/testing)
    return user || mockUser();
  },
  async signIn({ email }) {
    await delay(380);
    const user = mockUser({ email });
    write(user);
    return user;
  },
  async signUp({ email, name }) {
    await delay(420);
    const user = mockUser({ email, name });
    write(user);
    return user;
  },
  async signInWithOAuth(provider) {
    await delay(420);
    const user = mockUser({ name: provider === 'github' ? 'Maya Chen' : 'Maya Chen' });
    write(user);
    return user;
  },
  async requestPasswordReset(_email) {
    await delay(300);
    return { ok: true };
  },
  async signOut() {
    await delay(150);
    write(null);
    return { ok: true };
  },
};
