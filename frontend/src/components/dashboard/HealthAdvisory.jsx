import React from 'react';
import { getAQICategory, getAQIColor } from '../../utils/aqiUtils';

const ICONS = {
  'Good':                           '😊',
  'Moderate':                       '😐',
  'Unhealthy for Sensitive Groups': '😷',
  'Unhealthy':                      '🤧',
  'Very Unhealthy':                 '🚨',
  'Hazardous':                      '☠️',
};

const TIPS = {
  'Good': [
    'Great day for outdoor activities.',
    'Air quality poses little or no risk.',
    'Enjoy outdoor exercise freely.',
  ],
  'Moderate': [
    'Unusually sensitive people should consider limiting prolonged outdoor exertion.',
    'Most people are unlikely to be affected.',
    'Keep windows open for fresh air.',
  ],
  'Unhealthy for Sensitive Groups': [
    'People with heart or lung disease, older adults, and children should reduce prolonged outdoor exertion.',
    'Everyone else can continue normal outdoor activities.',
    'Consider wearing an N95 mask outdoors.',
  ],
  'Unhealthy': [
    'Everyone should reduce prolonged or heavy outdoor exertion.',
    'People with heart or lung disease, older adults, and children should avoid prolonged outdoor exertion.',
    'Keep windows and doors closed.',
    'Use air purifiers indoors if available.',
  ],
  'Very Unhealthy': [
    'Everyone should avoid prolonged outdoor exertion.',
    'People with respiratory conditions should stay indoors.',
    'Wear N95 masks if going outside is necessary.',
    'Run air purifiers at high setting.',
  ],
  'Hazardous': [
    'Avoid all outdoor activities.',
    'Stay indoors with windows and doors closed.',
    'Wear N95/P100 respirator if you must go outside.',
    'Seek medical attention if you experience symptoms.',
    'Emergency conditions — check local health advisories.',
  ],
};

/**
 * HealthAdvisory — displays contextual health tips for a given AQI value.
 *
 * Props:
 *   aqi      {number}
 *   compact  {boolean} — show fewer tips (default false)
 */
export default function HealthAdvisory({ aqi, compact = false }) {
  const cat   = getAQICategory(aqi);
  const color = getAQIColor(aqi);
  if (!cat) return null;

  const tips  = TIPS[cat.label] ?? [];
  const shown = compact ? tips.slice(0, 2) : tips;

  return (
    <div
      className="rounded-xl p-4 border"
      style={{ backgroundColor: color + '12', borderColor: color + '44' }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl" role="img" aria-label={cat.label}>
          {ICONS[cat.label] ?? '🌫️'}
        </span>
        <div>
          <p className="text-sm font-bold" style={{ color }}>
            {cat.label}
          </p>
          <p className="text-xs text-gray-500">Health Advisory</p>
        </div>
      </div>

      <ul className="space-y-1.5">
        {shown.map((tip, i) => (
          <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
            <span className="text-green-500 mt-0.5 shrink-0">✓</span>
            {tip}
          </li>
        ))}
      </ul>

      {compact && tips.length > 2 && (
        <p className="text-xs text-gray-400 mt-2">+{tips.length - 2} more tips</p>
      )}
    </div>
  );
}
