import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts';

const POLLUTANT_UNITS = {
  PM25: 'µg/m³', PM10: 'µg/m³', NO2: 'µg/m³',
  SO2:  'µg/m³', O3:  'µg/m³',  NH3: 'µg/m³',
  CO:   'mg/m³',
};

// WHO guideline limits (annual mean µg/m³)
const WHO_LIMITS = {
  PM25: 5, PM10: 15, NO2: 10, SO2: 40, O3: 60, CO: 4000,
};

const COLORS = ['#1e3a5f','#2d6a4f','#e76f51','#e9c46a','#264653','#a8dadc','#457b9d'];

/**
 * PollutantChart
 * --------------
 * Horizontal or vertical bar chart for pollutant concentrations.
 *
 * Props:
 *   data      {object} - { pm25: 85, pm10: 120, no2: 45, ... }
 *   layout    {string} - 'horizontal' | 'vertical' (default 'horizontal')
 *   height    {number} - px (default 260)
 *   showLimit {boolean}- draw WHO guideline line (default true)
 *   title     {string}
 */
export default function PollutantChart({
  data = {},
  layout = 'horizontal',
  height = 260,
  showLimit = true,
  title,
}) {
  const chartData = Object.entries(data)
    .filter(([, v]) => v != null && !isNaN(v))
    .map(([key, val]) => ({
      name:  key.toUpperCase(),
      value: parseFloat(Number(val).toFixed(2)),
      unit:  POLLUTANT_UNITS[key.toUpperCase()] ?? 'µg/m³',
      limit: WHO_LIMITS[key.toUpperCase()] ?? null,
    }))
    .sort((a, b) => b.value - a.value);

  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center text-gray-400 text-sm" style={{ height }}>
        No pollutant data
      </div>
    );
  }

  const tooltipFormatter = (value, name, props) => [
    `${value} ${props.payload.unit}`,
    props.payload.name,
  ];

  return (
    <div>
      {title && <h4 className="text-sm font-semibold text-gray-700 mb-3">{title}</h4>}
      <ResponsiveContainer width="100%" height={height}>
        {layout === 'vertical' ? (
          <BarChart data={chartData} layout="vertical"
            margin={{ top: 5, right: 40, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={45} />
            <Tooltip formatter={tooltipFormatter} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.value > (entry.limit ?? Infinity) ? '#e74c3c' : COLORS[i % COLORS.length]} />
              ))}
              <LabelList dataKey="value" position="right" style={{ fontSize: 10, fill: '#555' }} />
            </Bar>
          </BarChart>
        ) : (
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={tooltipFormatter} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.value > (entry.limit ?? Infinity) ? '#e74c3c' : COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
      {showLimit && (
        <p className="text-xs text-gray-400 mt-1 text-center">
          🔴 Red bars exceed WHO annual guideline limits
        </p>
      )}
    </div>
  );
}
