import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  MdDashboard, MdOutlineAir, MdBarChart, MdHistory,
  MdDescription, MdAdminPanelSettings, MdPerson,
  MdSettings, MdLogout, MdClose,
} from 'react-icons/md';
import useAuthStore from '../../store/authStore';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/dashboard',  icon: MdDashboard,          label: 'Dashboard' },
  { to: '/prediction', icon: MdOutlineAir,          label: 'Predict AQI' },
  { to: '/analytics',  icon: MdBarChart,            label: 'Analytics' },
  { to: '/history',    icon: MdHistory,             label: 'History' },
  { to: '/reports',    icon: MdDescription,         label: 'Reports' },
];

const BOTTOM_ITEMS = [
  { to: '/profile',  icon: MdPerson,   label: 'Profile' },
  { to: '/settings', icon: MdSettings, label: 'Settings' },
];

export default function Sidebar({ open, onClose }) {
  const { user, logout, isAdmin } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const linkClass = ({ isActive }) =>
    clsx(
      'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
      isActive
        ? 'bg-white/15 text-white shadow-sm'
        : 'text-blue-100 hover:bg-white/10 hover:text-white'
    );

  return (
    <aside
      className={clsx(
        'fixed lg:static inset-y-0 left-0 z-30 w-64 flex flex-col',
        'bg-gradient-to-b from-primary to-primary-700 text-white',
        'transform transition-transform duration-300 ease-in-out',
        open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <div className="text-lg font-bold tracking-tight">🌍 AQI Predict</div>
          <div className="text-xs text-blue-200 mt-0.5">Environmental Analytics</div>
        </div>
        <button onClick={onClose} className="lg:hidden text-white/70 hover:text-white">
          <MdClose size={20} />
        </button>
      </div>

      {/* User chip */}
      <div className="mx-3 mt-4 mb-2 p-3 rounded-lg bg-white/10">
        <div className="text-sm font-semibold truncate">{user?.first_name || user?.username}</div>
        <div className="text-xs text-blue-200 capitalize">{user?.role?.replace('_', ' ')}</div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={linkClass} onClick={onClose}>
            <Icon size={18} /> {label}
          </NavLink>
        ))}

        {isAdmin() && (
          <>
            <div className="pt-3 pb-1 px-4 text-xs font-semibold text-blue-300 uppercase tracking-wider">
              Admin
            </div>
            <NavLink to="/admin" className={linkClass} onClick={onClose}>
              <MdAdminPanelSettings size={18} /> Admin Panel
            </NavLink>
          </>
        )}
      </nav>

      {/* Bottom actions */}
      <div className="px-3 py-3 border-t border-white/10 space-y-0.5">
        {BOTTOM_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={linkClass} onClick={onClose}>
            <Icon size={18} /> {label}
          </NavLink>
        ))}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium
                     text-blue-100 hover:bg-red-500/20 hover:text-white transition-all"
        >
          <MdLogout size={18} /> Sign Out
        </button>
      </div>
    </aside>
  );
}
