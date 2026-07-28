import api from './api';

export const predictionService = {
  predict:     (features)         => api.post('/predictions/', features),
  predictBatch:(records)          => api.post('/predictions/batch', { records }),
  getHistory:  (page = 1, per = 20) => api.get(`/predictions/history?page=${page}&per_page=${per}`),
  getById:     (id)               => api.get(`/predictions/${id}`),
  explain:     (features, methods) => api.post('/predictions/explain', { features, methods }),
};
