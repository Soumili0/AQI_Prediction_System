import React from 'react';
import { getAQIColor, getAQIBadgeClass, getAQICategory, formatAQI } from '../../utils/aqiUtils';
import clsx from 'clsx';

/**
 * AQICard — large hero card showing current / predicted AQI with colour ring.
 *
 * Props:
 *   aqi        {number}
 *   label      {string}  — title above the value (default "Current AQI")
 *   city       {string}  — optional city name
 *   timestamp  {string}  — ISO date string
 *   size       {'sm'|'md'|'lg'}
 */
export default function AQICard({ aqi, label = 'Current AQI', city, timestamp, size = 'md' }) {
  const cat   = getAQICategory(aqi);
  const color = getAQIColor(aqi);

  const sizeMap = {
    sm: { number: 'text-4xl', ring: 'w-24 h-24', badge: 'text-xs', title: 'text-xs' },
    md: { number: 'text-6xl', ring: 'w-36 h-36', badge: 'text-sm', title: 'text-sm' },
    lg: { number: 'text-8xl', ring: 'w-48 h-48', badge: 'text-base', title: 'text-base' },
  };
  const s = sizeMap[size];

  return (
    <div className="card flex flex-col items-center text-center py-6">
      <p className={clsx('font-medium text-gray-500 mb-4', s.title)}>{label}</p>

      {/* Colour ring */}
      <div
        className={clsx('rounded-full flex items-center justify-center mb-4', s.ring)}
        style={{ border: `6px solid ${color}`, boxShadow: `0 0 24px ${color}55` }}
      >
        <span className={clsx('font-black leading-none', s.number)} style={{ color }}>
          {aqi != null ? formatAQI(aqi) : '—'}
        </span>
      </div>

      {/* Category badge */}
      {cat && (
        <span className={clsx('badge px-3 py-1 font-semibold mb-3', s.badge, getAQIBadgeClass(cat.label))}>
          {cat.label}
        </span>
      )}

      {/* Advisory */}
      {cat && (
        <p className="text-xs text-gray-500 max-w-[220px] leading-relaxed">{cat.text}</p>
      )}

      {/* Meta */}
      {(city || timestamp) && (
        <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
          {city && <span>📍 {city}</span>}
          {timestamp && (
            <span>
              🕒 {new Date(timestamp).toLocaleString('en-IN', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
              })}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
