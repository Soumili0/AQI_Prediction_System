import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { getAQICategory, formatAQI } from '../../utils/aqiUtils';

/**
 * AQIGauge
 * --------
 * Semi-circle gauge that visually represents a single AQI value
 * with colour coding matching the US EPA scale.
 *
 * Props:
 *   value   {number}  - AQI value (0-500)
 *   size    {number}  - container height in px (default 200)
 *   label   {string}  - optional subtitle label
 */
export default function AQIGauge({ value, size = 200, label = 'AQI' }) {
  const cat = getAQICategory(value);
  const clamped = Math.min(Math.max(value ?? 0, 0), 500);

  // Build a half-ring: filled arc + empty arc
  const filled = (clamped / 500) * 180;  // degrees out of 180
  const empty  = 180 - filled;

  const data = [
    { value: filled, color: cat?.color ?? '#94a3b8' },
    { value: empty,  color: '#e2e8f0' },
  ];

  return (
    <div className="flex flex-col items-center" style={{ height: size }}>
      <div style={{ width: size, height: size / 2 + 20, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius="60%"
              outerRadius="85%"
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Centre text */}
        <div
          className="absolute inset-x-0 bottom-0 flex flex-col items-center pb-1"
          style={{ pointerEvents: 'none' }}
        >
          <span className="text-3xl font-black leading-none" style={{ color: cat?.color ?? '#64748b' }}>
            {value != null ? formatAQI(value) : '—'}
          </span>
          <span className="text-xs font-semibold text-gray-500 mt-0.5">{label}</span>
        </div>
      </div>

      {/* Category badge */}
      {cat && (
        <div
          className="mt-2 px-3 py-1 rounded-full text-xs font-semibold"
          style={{ backgroundColor: cat.color + '22', color: cat.color, border: `1px solid ${cat.color}44` }}
        >
          {cat.label}
        </div>
      )}
    </div>
  );
}
