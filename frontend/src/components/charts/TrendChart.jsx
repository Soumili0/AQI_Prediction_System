import React from 'react';
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';

/**
 * TrendChart
 * ----------
 * Flexible line/area chart for AQI trend data.
 *
 * Props:
 *   data        {Array}   - [{date, mean, min, max, count}]
 *   type        {string}  - 'area' | 'line' (default 'area')
 *   height      {number}  - chart height px (default 260)
 *   showMinMax  {boolean} - show min/max lines (default true)
 *   title       {string}  - optional chart title
 *   granularity {string}  - 'daily'|'monthly'|'yearly' for label formatting
 */
export default function TrendChart({
  data = [],
  type = 'area',
  height = 260,
  showMinMax = true,
  title,
  granularity = 'daily',
}) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center text-gray-400 text-sm" style={{ height }}>
        No trend data available
      </div>
    );
  }

  const formatLabel = (d) => {
    if (!d) return '';
    if (granularity === 'daily')   return d.toString().slice(5);   // MM-DD
    if (granularity === 'monthly') return d.toString().slice(0, 7); // YYYY-MM
    return d.toString();
  };

  const customTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-xs">
        <p className="font-semibold text-gray-600 mb-1">{label}</p>
        {payload.map((p) => (
          <p key={p.dataKey} style={{ color: p.color }}>
            {p.name}: <strong>{Number(p.value).toFixed(1)}</strong>
          </p>
        ))}
      </div>
    );
  };

  const commonProps = {
    data,
    margin: { top: 5, right: 20, left: 0, bottom: 5 },
  };

  const axes = (
    <>
      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
      <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={formatLabel} />
      <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
      <Tooltip content={customTooltip} />
      <Legend iconType="circle" iconSize={9} wrapperStyle={{ fontSize: 11 }} />
      <ReferenceLine y={100} stroke="#ffcc00" strokeDasharray="4 2" strokeWidth={1} label={{ value: 'Moderate', fontSize: 9, fill: '#b8a000' }} />
      <ReferenceLine y={200} stroke="#ff4444" strokeDasharray="4 2" strokeWidth={1} label={{ value: 'Unhealthy', fontSize: 9, fill: '#cc0000' }} />
    </>
  );

  return (
    <div>
      {title && <h4 className="text-sm font-semibold text-gray-700 mb-3">{title}</h4>}
      <ResponsiveContainer width="100%" height={height}>
        {type === 'area' ? (
          <AreaChart {...commonProps}>
            <defs>
              <linearGradient id="meanGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#1e3a5f" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#1e3a5f" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            {axes}
            <Area type="monotone" dataKey="mean" stroke="#1e3a5f" fill="url(#meanGrad)"
              strokeWidth={2} name="Mean AQI" dot={false} activeDot={{ r: 4 }} />
            {showMinMax && (
              <>
                <Line type="monotone" dataKey="max" stroke="#e74c3c" strokeWidth={1.5}
                  strokeDasharray="5 3" name="Max AQI" dot={false} />
                <Line type="monotone" dataKey="min" stroke="#27ae60" strokeWidth={1.5}
                  strokeDasharray="5 3" name="Min AQI" dot={false} />
              </>
            )}
          </AreaChart>
        ) : (
          <LineChart {...commonProps}>
            {axes}
            <Line type="monotone" dataKey="mean" stroke="#1e3a5f" strokeWidth={2}
              name="Mean AQI" dot={false} activeDot={{ r: 4 }} />
            {showMinMax && (
              <>
                <Line type="monotone" dataKey="max" stroke="#e74c3c" strokeWidth={1.5}
                  strokeDasharray="5 3" name="Max AQI" dot={false} />
                <Line type="monotone" dataKey="min" stroke="#27ae60" strokeWidth={1.5}
                  strokeDasharray="5 3" name="Min AQI" dot={false} />
              </>
            )}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
