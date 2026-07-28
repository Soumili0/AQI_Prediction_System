import api from './api';

export const adminService = {
  getStats:        ()                    => api.get('/admin/stats'),
  getUsers:        (params)              => api.get('/admin/users', { params }),
  getUser:         (id)                  => api.get(`/admin/users/${id}`),
  updateUser:      (id, data)            => api.put(`/admin/users/${id}`, data),
  deleteUser:      (id)                  => api.delete(`/admin/users/${id}`),
  getDatasets:     (params)              => api.get('/admin/datasets', { params }),
  deleteDataset:   (id)                  => api.delete(`/admin/datasets/${id}`),
  getPredictions:  (params)              => api.get('/admin/predictions', { params }),
  getModels:       ()                    => api.get('/admin/models'),
  activateModel:   (id)                  => api.put(`/admin/models/${id}/activate`),
  getAuditLogs:    (params)              => api.get('/admin/audit-logs', { params }),
};
