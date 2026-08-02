import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, LineChart, Line,
} from 'recharts';
import { analyticsService } from '../services/analyticsService';
import LoadingSpinner from '../components/common/LoadingSpinner';

const POLLUTANT_UNITS = {
  PM25: 'µg/m³', PM10: 'µg/m³', NO2: 'µg/m³',
  SO2: 'µg/m³',  CO:  'mg/m³',  O3:  'µg/m³', NH3: 'µg/m³',
};

const fmt = (v, digits = 1) =>
  v == null ? '—' : Number(v).toFixed(digits);

export default function Analytics() {
  const [cities, setCities]           = useState([]);
  const [city, setCity]               = useState('');
  const [granularity, setGranularity] = useState('monthly');
  const [days, setDays]               = useState(0);          // 0 = all data
  const [trend, setTrend]             = useState([]);
  const [cityData, setCityData]       = useState([]);
  const [pollutants, setPollutants]   = useState({});
  const [models, setModels]           = useState([]);
  const [overview, setOverview]       = useState(null);
  const [loading, setLoading]         = useState(true);

  // load city list once
  useEffect(() => {
    analyticsService.getCityList()
      .then(r => setCities(r.data.cities || []))
      .catch(() => {});
  }, []);

  // reload on filter change
  useEffect(() => {
    setLoading(true);
    const effectiveDays = days === 0 ? 3650 : days;   // 0 → 10 years ≈ all
    Promise.allSettled([
      analyticsService.getTrend(city || undefined, granularity, effectiveDays),
      analyticsService.getCities(),
      analyticsService.getPollutants(city || undefined, effectiveDays),
      analyticsService.getModels(),
      analyticsService.getOverview(city || undefined, effectiveDays),
    ]).then(([t, c, p, m, ov]) => {
      if (t.status  === 'fulfilled') setTrend(t.value.data.trend || []);
      if (c.status  === 'fulfilled') setCityData(c.value.data.cities || []);
      if (p.status  === 'fulfilled') setPollutants(p.value.data.pollutants || {});
      if (m.status  === 'fulfilled') setModels(m.value.data.models || []);
      if (ov.status === 'fulfilled') setOverview(ov.value.data);
    }).finally(() => setLoading(false));
  }, [city, granularity, days]);

  // pollutant bar data
  const pollutantBarData = Object.entries(pollutants)
    .filter(([, v]) => v != null)
    .map(([k, v]) => ({
      name: k.toUpperCase(),
      value: parseFloat(parseFloat(v).toFixed(3)),
      unit: POLLUTANT_UNITS[k.toUpperCase()] || 'µg/m³',
    }));

  // category pie data from overview
  const categoryData = overview?.category_breakdown
    ? Object.entries(overview.category_breakdown)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
    : [];

  if (loading) return <LoadingSpinner text="Loading analytics…" />;

  return (
    <div className="space-y-6 animate-slide-up">

      {/* ── Header + Filters ── */}
      <div className="page-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
          <p className="text-gray-500 text-sm mt-0.5">
            Interactive environmental data visualisation — Historical dataset (2015–2024)
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {/* Location filter */}
          <select className="input w-auto text-sm" value={city}
            onChange={e => setCity(e.target.value)}>
            <option value="">All Locations</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          {/* Granularity */}
          <select className="input w-auto text-sm" value={granularity}
            onChange={e => setGranularity(e.target.value)}>
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>

          {/* Time range */}
          <select className="input w-auto text-sm" value={days}
            onChange={e => setDays(Number(e.target.value))}>
            <option value={0}>All Data (2015–2024)</option>
            <option value={365}>Last 1 Year</option>
            <option value={180}>Last 6 Months</option>
            <option value={90}>Last 90 Days</option>
            <option value={30}>Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* ── Overview stat cards ── */}
      {overview && !overview.message && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Mean AQI',     value: fmt(overview.mean_aqi) },
            { label: 'Max AQI',      value: fmt(overview.max_aqi) },
            { label: 'Min AQI',      value: fmt(overview.min_aqi) },
            { label: 'Total Readings', value: overview.total_readings?.toLocaleString() },
          ].map(({ label, value }) => (
            <div key={label} className="card text-center py-4">
              <p className="text-xs text-gray-500 mb-1">{label}</p>
              <p className="text-2xl font-bold text-gray-800">{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* ── AQI Trend ── */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-800 mb-4">
          AQI Trend ({granularity})
          {days === 0 ? ' — All Data' : ` — Last ${days} days`}
        </h3>
        {trend.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trend}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#1e3a5f" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#1e3a5f" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }}
                tickFormatter={d =>
                  granularity === 'daily' ? d?.slice(5) :
                  granularity === 'monthly' ? d?.slice(0, 7) : d
                }
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v, n) => [fmt(v), n]} labelFormatter={l => `Date: ${l}`} />
              <Legend />
              <Area type="monotone" dataKey="mean" stroke="#1e3a5f"
                fill="url(#grad)" strokeWidth={2} name="Mean AQI" />
              <Area type="monotone" dataKey="max" stroke="#e74c3c"
                fill="none" strokeWidth={1.5} strokeDasharray="5 3" name="Max AQI" />
              <Area type="monotone" dataKey="min" stroke="#27ae60"
                fill="none" strokeWidth={1.5} strokeDasharray="3 3" name="Min AQI" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-60 flex items-center justify-center text-gray-400">
            No trend data — try selecting "All Data"
          </div>
        )}
      </div>

      {/* ── Pollutants + Category ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Pollutant bar chart */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">
            Average Pollutant Concentrations
          </h3>
          {pollutantBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={pollutantBarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v, n, props) => [
                    `${v} ${props.payload?.unit || 'µg/m³'}`, 'Avg'
                  ]}
                />
                <Bar dataKey="value" fill="#e76f51" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400">
              No pollutant data
            </div>
          )}
        </div>

        {/* AQI Category breakdown bar */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">
            AQI Category Breakdown
          </h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={categoryData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={90} />
                <Tooltip formatter={(v) => [v.toLocaleString(), 'Readings']} />
                <Bar dataKey="count" fill="#2d6a4f" radius={[0, 4, 4, 0]} name="Readings" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400">
              No category data
            </div>
          )}
        </div>
      </div>

      {/* ── Location Stats + ML Model Table ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Location AQI stats */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">
            Location AQI Statistics
          </h3>
          {cityData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr>
                    {['Location', 'Mean AQI', 'Min AQI', 'Max AQI', 'Readings'].map(h => (
                      <th key={h} className="table-header">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cityData.map((row, i) => (
                    <tr key={row.city} className={i % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                      <td className="table-cell font-medium">{row.city}</td>
                      <td className="table-cell">{fmt(row.mean_aqi)}</td>
                      <td className="table-cell">{fmt(row.min_aqi)}</td>
                      <td className="table-cell">{fmt(row.max_aqi)}</td>
                      <td className="table-cell">{row.count?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">No location data</p>
          )}
        </div>

        {/* ML Model comparison table */}
        <div className="card overflow-x-auto">
          <h3 className="text-base font-semibold text-gray-800 mb-4">ML Model Performance</h3>
          {models.length > 0 ? (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  {['Model', 'Algorithm', 'MAE', 'RMSE', 'R²', 'Status'].map(h => (
                    <th key={h} className="table-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {models.map((m, i) => (
                  <tr key={m.id} className={i % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                    <td className="table-cell font-medium">{m.name}</td>
                    <td className="table-cell text-gray-500">{m.algorithm?.replace('_', ' ')}</td>
                    <td className="table-cell">
                      {m.metrics?.mae != null ? m.metrics.mae.toFixed(3) : '—'}
                    </td>
                    <td className="table-cell">
                      {m.metrics?.rmse != null ? m.metrics.rmse.toFixed(3) : '—'}
                    </td>
                    <td className="table-cell font-semibold text-green-700">
                      {m.metrics?.r2_score != null ? m.metrics.r2_score.toFixed(4) : '—'}
                    </td>
                    <td className="table-cell">
                      {m.is_active
                        ? <span className="badge bg-green-100 text-green-700">Active</span>
                        : <span className="badge bg-gray-100 text-gray-500">Inactive</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">No models registered</p>
          )}
        </div>
      </div>

      {/* ── Yearly AQI trend (always show full history) ── */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-800 mb-4">
          Yearly AQI Summary (Full Dataset)
        </h3>
        <YearlyChart city={city} />
      </div>

    </div>
  );
}

// Separate component for yearly chart — always loads full data
function YearlyChart({ city }) {
  const [data, setData] = useState([]);
  useEffect(() => {
    analyticsService.getTrend(city || undefined, 'yearly', 3650)
      .then(r => setData(r.data.trend || []))
      .catch(() => {});
  }, [city]);

  if (!data.length) return (
    <div className="h-48 flex items-center justify-center text-gray-400">No data</div>
  );

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip formatter={(v, n) => [Number(v).toFixed(1), n]} />
        <Legend />
        <Bar dataKey="mean" fill="#1e3a5f" name="Mean AQI" radius={[4, 4, 0, 0]} />
        <Bar dataKey="max"  fill="#e74c3c" name="Max AQI"  radius={[4, 4, 0, 0]} />
        <Bar dataKey="min"  fill="#27ae60" name="Min AQI"  radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
