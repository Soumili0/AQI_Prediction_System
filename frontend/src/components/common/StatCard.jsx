import React from 'react';
import clsx from 'clsx';

export default function StatCard({ title, value, subtitle, icon: Icon, color = 'blue', trend }) {
  const colorMap = {
    blue:   'bg-blue-50 text-blue-600',
    green:  'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    red:    'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="card flex items-start justify-between gap-4 hover:shadow-hover transition-shadow">
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
        <p className="text-2xl font-bold text-gray-900 truncate">{value ?? '—'}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
        {trend && (
          <p className={clsx('text-xs mt-1 font-medium', trend > 0 ? 'text-red-500' : 'text-green-500')}>
            {trend > 0 ? '▲' : '▼'} {Math.abs(trend)}% vs last period
          </p>
        )}
      </div>
      {Icon && (
        <div className={clsx('p-3 rounded-xl shrink-0', colorMap[color])}>
          <Icon size={22} />
        </div>
      )}
    </div>
  );
}
