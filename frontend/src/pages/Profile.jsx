import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import useAuthStore from '../store/authStore';
import { authService } from '../services/authService';

export default function Profile() {
  const { user, updateProfile } = useAuthStore();
  const [pwLoading, setPwLoading] = useState(false);
  const [tab, setTab] = useState('profile');

  const { register: regProfile, handleSubmit: handleProfile, formState: { errors: errP, isDirty } } = useForm({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name:  user?.last_name  || '',
      username:   user?.username   || '',
      phone:      user?.phone      || '',
      organization: user?.organization || '',
      city:       user?.city       || '',
      country:    user?.country    || '',
    },
  });

  const { register: regPw, handleSubmit: handlePw, reset: resetPw, formState: { errors: errPw } } = useForm();

  const onProfileSubmit = async (data) => {
    const result = await updateProfile(data);
    if (result.success) toast.success('Profile updated!');
    else toast.error(result.error);
  };

  const onPasswordSubmit = async (data) => {
    if (data.new_password !== data.confirm) { toast.error('Passwords do not match.'); return; }
    setPwLoading(true);
    try {
      await authService.changePassword(data.current_password, data.new_password);
      toast.success('Password changed successfully!');
      resetPw();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Password change failed.');
    } finally {
      setPwLoading(false);
    }
  };

  const tabs = [{ id: 'profile', label: 'Profile Info' }, { id: 'password', label: 'Change Password' }];

  return (
    <div className="space-y-5 animate-slide-up max-w-3xl">
      <h2 className="text-2xl font-bold text-gray-900">My Profile</h2>

      {/* Avatar area */}
      <div className="card flex items-center gap-5">
        <div className="w-16 h-16 rounded-full bg-primary text-white flex items-center justify-center text-2xl font-bold shrink-0">
          {(user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase()}
        </div>
        <div>
          <h3 className="text-lg font-semibold">{user?.first_name} {user?.last_name}</h3>
          <p className="text-sm text-gray-500">@{user?.username} · <span className="capitalize">{user?.role?.replace('_', ' ')}</span></p>
          <p className="text-xs text-gray-400 mt-0.5">{user?.email}</p>
        </div>
        <div className="ml-auto">
          <span className={`badge ${user?.is_verified ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
            {user?.is_verified ? '✓ Verified' : '! Unverified'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'profile' && (
        <div className="card">
          <form onSubmit={handleProfile(onProfileSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { name: 'first_name', label: 'First Name' },
                { name: 'last_name',  label: 'Last Name' },
                { name: 'username',   label: 'Username' },
                { name: 'phone',      label: 'Phone' },
                { name: 'organization', label: 'Organization' },
                { name: 'city',       label: 'City' },
                { name: 'country',    label: 'Country' },
              ].map(({ name, label }) => (
                <div key={name}>
                  <label className="label">{label}</label>
                  <input className="input" {...regProfile(name)} />
                  {errP[name] && <p className="text-red-500 text-xs mt-1">{errP[name].message}</p>}
                </div>
              ))}
            </div>
            <button type="submit" disabled={!isDirty} className="btn-primary disabled:opacity-50">
              Save Changes
            </button>
          </form>
        </div>
      )}

      {tab === 'password' && (
        <div className="card max-w-md">
          <form onSubmit={handlePw(onPasswordSubmit)} className="space-y-4">
            {[
              { name: 'current_password', label: 'Current Password' },
              { name: 'new_password',     label: 'New Password' },
              { name: 'confirm',          label: 'Confirm New Password' },
            ].map(({ name, label }) => (
              <div key={name}>
                <label className="label">{label}</label>
                <input type="password" className="input"
                  {...regPw(name, { required: `${label} is required` })} />
                {errPw[name] && <p className="text-red-500 text-xs mt-1">{errPw[name].message}</p>}
              </div>
            ))}
            <button type="submit" disabled={pwLoading} className="btn-primary">
              {pwLoading ? 'Updating…' : 'Change Password'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
