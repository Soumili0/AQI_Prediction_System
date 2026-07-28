import api from './api';

export const authService = {
  register:       (data)          => api.post('/auth/register', data),
  login:          (email, password) => api.post('/auth/login', { email, password }),
  logout:         ()              => api.post('/auth/logout'),
  refresh:        ()              => api.post('/auth/refresh'),
  verifyEmail:    (token)         => api.post('/auth/verify-email', { token }),
  forgotPassword: (email)         => api.post('/auth/forgot-password', { email }),
  resetPassword:  (token, newPassword) => api.post('/auth/reset-password', { token, new_password: newPassword }),
  getProfile:     ()              => api.get('/auth/me'),
  updateProfile:  (data)          => api.put('/auth/me', data),
  changePassword: (currentPassword, newPassword) =>
    api.put('/auth/me/change-password', { current_password: currentPassword, new_password: newPassword }),
};
