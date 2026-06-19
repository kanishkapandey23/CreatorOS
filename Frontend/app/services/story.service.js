import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export const storyService = {
  async list() {
    const res = await axios.get(`${API_BASE}/stories`);
    return res.data;
  },
  async get(id) {
    const res = await axios.get(`${API_BASE}/stories/${id}`);
    return res.data;
  },
  async create(payload) {
    const res = await axios.post(`${API_BASE}/stories`, payload);
    return res.data;
  },
};
