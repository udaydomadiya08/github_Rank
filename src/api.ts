import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const apiService = {
  getStatus: () => api.get('/status').then(res => res.data),
  
  getRankings: (category: string, timeframe: string = '24h') => 
    api.get(`/rankings/${category}`, { params: { tf: timeframe } }).then(res => res.data),
};

export default api;
