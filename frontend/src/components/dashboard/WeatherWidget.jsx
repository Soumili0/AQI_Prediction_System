import React from 'react';
import {
  MdThermostat, MdWaterDrop, MdAir, MdCompress, MdExplore,
} from 'react-icons/md';

const METRICS = [
  { key: 'temperature',  label: 'Temp',      unit: '°C',  icon: MdThermostat, color: 'text-orange-500' },
  { key: 'humidity',     label: 'Humidity',  unit: '%',   icon: MdWaterDrop,  color: 'text-blue-500'   },
  { key: 'wind_speed',   label: 'Wind',      unit: 'm/s', icon: MdAir,        color: 'text-teal-500'   },
  { key: 'wind_direction',label: 'Dir',      unit: '°',   icon: MdExplore,    color: 'text-purple-500' },
  { key: 'pressure',     label: 'Pressure',  unit: 'hPa', icon: MdCompress,   color: 'text-gray-500'   },
];

/**
 * WeatherWidget — compact panel showing weather parameters from a reading.
 *
 * Props:
 *   data   {object} — { temperature, humidity, wind_speed, wind_direction, pressure }
 *   title  {string}
 */
export default function WeatherWidget({ data = {}, title = 'Weather Conditions' }) {
  const hasData = METRICS.some(({ key }) => data[key] != null);

  return (
    <div className="card">
      <h4 className="text-sm font-semibold text-gray-700 mb-4">⛅ {title}</h4>

      {!hasData ? (
        <p className="text-xs text-gray-400 text-center py-4">No weather data available</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {METRICS.map(({ key, label, unit, icon: Icon, color }) => {
            const val = data[key];
            return (
              <div key={key}
                className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                <Icon size={20} className={color} />
                <div>
                  <p className="text-xs text-gray-400 leading-none">{label}</p>
                  <p className="text-sm font-semibold text-gray-800 mt-0.5">
                    {val != null ? `${Number(val).toFixed(1)} ${unit}` : '—'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
