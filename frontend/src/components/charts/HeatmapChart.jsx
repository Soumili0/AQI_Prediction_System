import React, { useMemo } from 'react';
import { getAQIColor } from '../../utils/aqiUtils';

/**
 * HeatmapChart
 * ------------
 * A pure-CSS heatmap grid (no heavy charting lib needed).
 * Rows = cities, Columns = months.
 *
 * Props:
 *   data    {Array}  - [{ city, month, aqi }]  or [{ city, date, aqi }]
 *   rowKey  {string} - key to use as row label (default 'city')
 *   colKey  {string} - key to use as column label (default 'month')
 *   title   {string}
 */
export default function HeatmapChart({ data = [], rowKey = 'city', colKey = 'month', title }) {
  const { rows, cols, matrix, min, max } = useMemo(() => {
    if (!data.length) return { rows: [], cols: [], matrix: {}, min: 0, max: 500 };

    const rows = [...new Set(data.map(d => d[rowKey]))].sort();
    const cols = [...new Set(data.map(d => d[colKey]))].sort();
    const matrix = {};
    data.forEach(d => {
      if (!matrix[d[rowKey]]) matrix[d[rowKey]] = {};
      matrix[d[rowKey]][d[colKey]] = d.aqi;
    });
    const values = data.map(d => d.aqi).filter(Boolean);
    return {
      rows, cols, matrix,
      min: Math.min(...values),
      max: Math.max(...values),
    };
  }, [data, rowKey, colKey]);

  if (!rows.length) {
    return (
      <div className="flex items-center justify-center text-gray-400 text-sm py-10">
        No heatmap data available
      </div>
    );
  }

  // Interpolate colour between green and red based on AQI value
  const getCellColor = (val) => {
    if (val == null) return '#f1f5f9';
    return getAQIColor(val);
  };

  const getTextColor = (val) => {
    if (val == null) return '#94a3b8';
    return val > 150 ? '#fff' : '#1e293b';
  };

  return (
    <div className="overflow-x-auto">
      {title && <h4 className="text-sm font-semibold text-gray-700 mb-3">{title}</h4>}
      <table className="text-xs border-collapse w-full">
        <thead>
          <tr>
            <th className="p-2 text-left text-gray-500 font-medium bg-gray-50 sticky left-0 z-10 min-w-[100px]">
              {rowKey.charAt(0).toUpperCase() + rowKey.slice(1)}
            </th>
            {cols.map(col => (
              <th key={col} className="p-2 text-center text-gray-500 font-medium bg-gray-50 min-w-[50px]">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row}>
              <td className="p-2 font-medium text-gray-700 bg-white sticky left-0 border-b border-gray-100">
                {row}
              </td>
              {cols.map(col => {
                const val = matrix[row]?.[col];
                return (
                  <td
                    key={col}
                    title={val != null ? `${row} / ${col}: AQI ${Number(val).toFixed(1)}` : 'No data'}
                    className="p-1 text-center border border-white transition-transform hover:scale-110 cursor-default"
                    style={{
                      backgroundColor: getCellColor(val),
                      color: getTextColor(val),
                      fontWeight: val != null ? 600 : 400,
                    }}
                  >
                    {val != null ? Number(val).toFixed(0) : '—'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="flex items-center gap-2 mt-3 flex-wrap">
        <span className="text-xs text-gray-400">AQI Scale:</span>
        {[
          { label: 'Good',      color: '#00e400', range: '0-50'   },
          { label: 'Moderate',  color: '#ffff00', range: '51-100' },
          { label: 'Unhealthy', color: '#ff7e00', range: '101-150'},
          { label: 'Bad',       color: '#ff0000', range: '151+'   },
          { label: 'Hazardous', color: '#7e0023', range: '301+'   },
        ].map(({ label, color, range }) => (
          <span key={label} className="flex items-center gap-1 text-xs text-gray-500">
            <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: color }} />
            {label} ({range})
          </span>
        ))}
      </div>
    </div>
  );
}
