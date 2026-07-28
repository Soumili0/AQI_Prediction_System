/**
 * AQI utility functions shared across the frontend
 */

export const AQI_CATEGORIES = [
  { range: [0,   50],  label: 'Good',                         color: '#00e400', bg: 'aqi-good',      text: 'Air quality is satisfactory and poses little or no risk.' },
  { range: [51,  100], label: 'Moderate',                     color: '#ffff00', bg: 'aqi-moderate',  text: 'Acceptable quality; may affect very sensitive individuals.' },
  { range: [101, 150], label: 'Unhealthy for Sensitive Groups',color: '#ff7e00', bg: 'aqi-sensitive', text: 'Sensitive groups may experience health effects.' },
  { range: [151, 200], label: 'Unhealthy',                    color: '#ff0000', bg: 'aqi-unhealthy', text: 'Everyone may begin to experience health effects.' },
  { range: [201, 300], label: 'Very Unhealthy',               color: '#8f3f97', bg: 'aqi-very',      text: 'Health alert: risk of health effects is increased for everyone.' },
  { range: [301, 500], label: 'Hazardous',                    color: '#7e0023', bg: 'aqi-hazardous', text: 'Health warning of emergency conditions.' },
];

export function getAQICategory(value) {
  if (value == null || isNaN(value)) return null;
  return AQI_CATEGORIES.find(({ range }) => value >= range[0] && value <= range[1]) || AQI_CATEGORIES[5];
}

export function getAQIColor(value) {
  return getAQICategory(value)?.color || '#gray';
}

export function getAQIBadgeClass(category) {
  const map = {
    'Good':                          'bg-green-100 text-green-800',
    'Moderate':                      'bg-yellow-100 text-yellow-800',
    'Unhealthy for Sensitive Groups':'bg-orange-100 text-orange-800',
    'Unhealthy':                     'bg-red-100 text-red-800',
    'Very Unhealthy':                'bg-purple-100 text-purple-800',
    'Hazardous':                     'bg-rose-100 text-rose-900',
  };
  return map[category] || 'bg-gray-100 text-gray-700';
}

export function formatAQI(value) {
  if (value == null) return '—';
  return Number(value).toFixed(1);
}

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('en-IN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}
