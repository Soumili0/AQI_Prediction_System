/**
 * constants.js
 * ============
 * Application-wide constants used across frontend components.
 */

// AQI category definitions with colour coding
export const AQI_CATEGORIES = [
  { min: 0,   max: 50,  label: 'Good',                          color: '#00e400', bg: '#00e40022', textClass: 'text-green-700'  },
  { min: 51,  max: 100, label: 'Moderate',                      color: '#e8c800', bg: '#e8c80022', textClass: 'text-yellow-700' },
  { min: 101, max: 150, label: 'Unhealthy for Sensitive Groups', color: '#ff7e00', bg: '#ff7e0022', textClass: 'text-orange-700' },
  { min: 151, max: 200, label: 'Unhealthy',                     color: '#ff0000', bg: '#ff000022', textClass: 'text-red-700'    },
  { min: 201, max: 300, label: 'Very Unhealthy',                color: '#8f3f97', bg: '#8f3f9722', textClass: 'text-purple-700' },
  { min: 301, max: 500, label: 'Hazardous',                     color: '#7e0023', bg: '#7e002322', textClass: 'text-rose-900'   },
];

// Pollutant metadata
export const POLLUTANTS = [
  { key: 'pm25', label: 'PM2.5',      unit: 'µg/m³', who_limit: 5,    description: 'Fine particulate matter (≤2.5µm)' },
  { key: 'pm10', label: 'PM10',       unit: 'µg/m³', who_limit: 15,   description: 'Coarse particulate matter (≤10µm)' },
  { key: 'no2',  label: 'NO₂',        unit: 'µg/m³', who_limit: 10,   description: 'Nitrogen dioxide' },
  { key: 'so2',  label: 'SO₂',        unit: 'µg/m³', who_limit: 40,   description: 'Sulphur dioxide' },
  { key: 'co',   label: 'CO',         unit: 'mg/m³', who_limit: 4,    description: 'Carbon monoxide' },
  { key: 'o3',   label: 'O₃',         unit: 'µg/m³', who_limit: 60,   description: 'Ground-level ozone' },
  { key: 'nh3',  label: 'NH₃',        unit: 'µg/m³', who_limit: null, description: 'Ammonia' },
];

// Weather parameters
export const WEATHER_PARAMS = [
  { key: 'temperature',    label: 'Temperature',   unit: '°C'  },
  { key: 'humidity',       label: 'Humidity',      unit: '%'   },
  { key: 'wind_speed',     label: 'Wind Speed',    unit: 'm/s' },
  { key: 'wind_direction', label: 'Wind Direction',unit: '°'   },
  { key: 'pressure',       label: 'Pressure',      unit: 'hPa' },
];

// User roles
export const ROLES = [
  { value: 'citizen',      label: 'Citizen',      desc: 'Basic prediction and dashboard access' },
  { value: 'researcher',   label: 'Researcher',   desc: 'Dataset management, model metrics, XAI reports' },
  { value: 'policy_maker', label: 'Policy Maker', desc: 'Analytics, reports, and prediction history' },
  { value: 'admin',        label: 'Admin',        desc: 'Full system access including admin panel' },
];

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// Chart colours palette
export const CHART_COLORS = [
  '#1e3a5f', '#2d6a4f', '#e76f51', '#e9c46a',
  '#264653', '#a8dadc', '#457b9d', '#95d5b2',
  '#f4a261', '#e63946',
];

// Seasons
export const SEASONS = {
  0: 'Winter', 1: 'Spring', 2: 'Summer', 3: 'Autumn',
};

// API endpoints base (resolved in api.js via env var)
export const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';
