import React from 'react';
import { Link } from 'react-router-dom';
import { MdMenu, MdNotifications, MdPerson } from 'react-icons/md';
import useAuthStore from '../../store/authStore';

export default function Navbar({ onMenuClick }) {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 md:px-6 shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100"
          aria-label="Open menu"
        >
          <MdMenu size={22} />
        </button>
        <div className="hidden sm:block">
          <h2 className="text-base font-semibold text-gray-800">
            AI AQI Prediction System
          </h2>
          <p className="text-xs text-gray-400">Explainable Environmental Analytics</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Notification bell (placeholder) */}
        <button className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 relative">
          <MdNotifications size={22} />
        </button>

        {/* User avatar */}
        <Link
          to="/profile"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-semibold">
            {(user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase()}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-sm font-medium text-gray-700 leading-none">
              {user?.first_name || user?.username}
            </div>
            <div className="text-xs text-gray-400 capitalize mt-0.5">
              {user?.role?.replace('_', ' ')}
            </div>
          </div>
        </Link>
      </div>
    </header>
  );
}
