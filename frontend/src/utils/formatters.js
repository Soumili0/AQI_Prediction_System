/**
 * formatters.js
 * =============
 * Shared formatting utilities used across the frontend.
 */

/**
 * Format a number with thousand separators.
 * formatNumber(1234567) → "1,234,567"
 */
export function formatNumber(value, decimals = 0) {
  if (value == null || isNaN(value)) return '—';
  return Number(value).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Format a float to fixed decimal places.
 * formatFloat(85.5678, 2) → "85.57"
 */
export function formatFloat(value, decimals = 2) {
  if (value == null || isNaN(value)) return '—';
  return Number(value).toFixed(decimals);
}

/**
 * Format a date string to a human-readable format.
 * formatDate("2024-01-15T12:30:00") → "Jan 15, 2024, 12:30 PM"
 */
export function formatDate(dateStr, options = {}) {
  if (!dateStr) return '—';
  const defaults = {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  };
  return new Date(dateStr).toLocaleString('en-IN', { ...defaults, ...options });
}

/**
 * Format only the date part.
 * formatDateOnly("2024-01-15T12:30:00") → "Jan 15, 2024"
 */
export function formatDateOnly(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

/**
 * Format relative time from now.
 * formatRelativeTime("2024-01-15T12:30:00") → "3 hours ago"
 */
export function formatRelativeTime(dateStr) {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr).getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours   = Math.floor(minutes / 60);
  const days    = Math.floor(hours / 24);

  if (days > 30)    return formatDateOnly(dateStr);
  if (days > 0)     return `${days}d ago`;
  if (hours > 0)    return `${hours}h ago`;
  if (minutes > 0)  return `${minutes}m ago`;
  return 'just now';
}

/**
 * Format bytes to human-readable size.
 * formatBytes(1048576) → "1.0 MB"
 */
export function formatBytes(bytes) {
  if (bytes == null || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

/**
 * Capitalise first letter of each word.
 * titleCase("hello world") → "Hello World"
 */
export function titleCase(str) {
  if (!str) return '';
  return str.replace(/\b\w/g, l => l.toUpperCase()).replace(/_/g, ' ');
}

/**
 * Truncate a string with ellipsis.
 * truncate("Hello World", 8) → "Hello..."
 */
export function truncate(str, maxLength = 50) {
  if (!str) return '';
  return str.length > maxLength ? str.slice(0, maxLength - 3) + '...' : str;
}

/**
 * Format a pollutant name for display.
 * formatPollutant("pm25") → "PM2.5"
 */
export function formatPollutant(key) {
  const map = {
    pm25: 'PM2.5', pm10: 'PM10', no2: 'NO₂',
    so2: 'SO₂', co: 'CO', o3: 'O₃', nh3: 'NH₃',
  };
  return map[key?.toLowerCase()] || key?.toUpperCase() || key;
}

/**
 * Format a pollutant value with its unit.
 * formatPollutantValue("pm25", 85.5) → "85.5 µg/m³"
 */
export function formatPollutantValue(key, value) {
  if (value == null) return '—';
  const units = {
    pm25: 'µg/m³', pm10: 'µg/m³', no2: 'µg/m³',
    so2: 'µg/m³',  o3: 'µg/m³',   nh3: 'µg/m³',
    co: 'mg/m³',
    temperature: '°C', humidity: '%', wind_speed: 'm/s',
    wind_direction: '°', pressure: 'hPa',
  };
  const unit = units[key?.toLowerCase()] || '';
  return `${Number(value).toFixed(2)} ${unit}`.trim();
}
