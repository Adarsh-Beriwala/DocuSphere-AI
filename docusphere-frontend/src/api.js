import axios from 'axios';

export const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const api = axios.create({ baseURL: API_URL, timeout: 90000 });

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('docusphere_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function errorMessage(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((row) => row.msg).join(', ');
  if (error.code === 'ECONNABORTED') return 'Request timed out. Try again.';
  return 'Unable to connect. Is the FastAPI backend running?';
}
export default api;
