/**
 * Zustand Auth Store
 * ==================
 * Single source of truth for authentication state.
 * Persists tokens to localStorage.
 */

import { create } from 'zustand';
import { authService } from '../services/authService';

const useAuthStore = create((set, get) => ({
  user:         JSON.parse(localStorage.getItem('user') || 'null'),
  isLoading:    false,
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const res = await authService.login(email, password);
      const { access_token, refresh_token, user } = res.data;
      localStorage.setItem('access_token',  access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user',          JSON.stringify(user));
      set({ user, isAuthenticated: true, isLoading: false });
      return { success: true };
    } catch (err) {
      set({ isLoading: false });
      return { success: false, error: err.response?.data?.error || 'Login failed.' };
    }
  },

  register: async (data) => {
    set({ isLoading: true });
    try {
      const res = await authService.register(data);
      set({ isLoading: false });
      return { success: true, message: res.data.message };
    } catch (err) {
      set({ isLoading: false });
      return { success: false, error: err.response?.data?.error || 'Registration failed.' };
    }
  },

  logout: async () => {
    try { await authService.logout(); } catch (_) {}
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    set({ user: null, isAuthenticated: false });
  },

  updateProfile: async (data) => {
    set({ isLoading: true });
    try {
      const res = await authService.updateProfile(data);
      const updated = res.data.user;
      localStorage.setItem('user', JSON.stringify(updated));
      set({ user: updated, isLoading: false });
      return { success: true };
    } catch (err) {
      set({ isLoading: false });
      return { success: false, error: err.response?.data?.error || 'Update failed.' };
    }
  },

  refreshProfile: async () => {
    try {
      const res = await authService.getProfile();
      const user = res.data.user;
      localStorage.setItem('user', JSON.stringify(user));
      set({ user });
    } catch (_) {}
  },

  isAdmin:       () => get().user?.role === 'admin',
  isResearcher:  () => ['admin', 'researcher'].includes(get().user?.role),
  isPolicyMaker: () => ['admin', 'policy_maker'].includes(get().user?.role),
}));

export default useAuthStore;
