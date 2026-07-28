import React from 'react';
import clsx from 'clsx';
import { getAQIBadgeClass } from '../../utils/aqiUtils';

/**
 * Badge — versatile status/category badge component.
 *
 * Props:
 *   label    {string}
 *   variant  {string}  - 'aqi' | 'success' | 'warning' | 'error' | 'info' | 'default'
 *   aqi      {string}  - AQI category string (only when variant='aqi')
 *   size     {string}  - 'sm' | 'md' (default 'md')
 */
export default function Badge({ label, variant = 'default', aqi, size = 'md' }) {
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1';

  const variantClass = {
    aqi:     aqi ? getAQIBadgeClass(aqi) : 'bg-gray-100 text-gray-600',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    error:   'bg-red-100 text-red-700',
    info:    'bg-blue-100 text-blue-700',
    purple:  'bg-purple-100 text-purple-700',
    default: 'bg-gray-100 text-gray-600',
  }[variant] || 'bg-gray-100 text-gray-600';

  return (
    <span className={clsx('inline-flex items-center rounded-full font-medium', sizeClass, variantClass)}>
      {label}
    </span>
  );
}
