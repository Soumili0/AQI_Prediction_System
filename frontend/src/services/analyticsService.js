import api from './api';

export const analyticsService = {
  getOverview:     (city, days = 30)             => api.get('/analytics/overview', { params: { city, days } }),
  getTrend:        (city, granularity = 'daily', days = 90) => api.get('/analytics/trend', { params: { city, granularity, days } }),
  getCities:       ()                            => api.get('/analytics/cities'),
  getPollutants:   (city, days = 30)             => api.get('/analytics/pollutants', { params: { city, days } }),
  getModels:       ()                            => api.get('/analytics/models'),
  getPredStats:    (days = 30)                   => api.get('/analytics/prediction-stats', { params: { days } }),
  getHistory:      (city, page = 1, per = 50)    => api.get('/history/', { params: { city, page, per_page: per } }),
  getCityList:     ()                            => api.get('/history/cities'),
};
