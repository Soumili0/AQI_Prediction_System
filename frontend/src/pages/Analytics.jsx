import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { analyticsService } from '../services/analyticsService';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Analytics() {
  const [cities, setCities]       = useState([]);
  const [city, setCity]           = useState('');
  const [granularity, setGranularity] = useState('daily');
  const [days, setDays]           = useState(90);
  const [trend, setTrend]         = useState([]);
  const [cityData, setCityData]   = useState([]);
  const [pollutants, setPollutants] = useState({});
  const [models, setModels]       = useState([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    analyticsService.getCityList().then(r => setCities(r.data.cities || []));
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      analyticsService.getTrend(city || undefined, granularity, days),
      analyticsService.getCities(),
      analyticsService.getPollutants(city || undefined, days),
      analyticsService.getModels(),
    ]).then(([t, c, p, m]) => {
      if (t.status === 'fulfilled') setTrend(t.value.data.trend || []);
      if (c.status === 'fulfilled') setCityData(c.value.data.cities || []);
      if (p.status === 'fulfilled') setPollutants(p.value.data.pollutants || {});
      if (m.status === 'fulfilled') setModels(m.value.data.models || []);
    }).finally(() => setLoading(false));
  }, [city, granularity, days]);

  const pollutantBarData = Object.entries(pollutants)
    .filter(([, v]) => v != null)
    .map(([k, v]) => ({ name: k.toUpperCase(), value: parseFloat(v).toFixed(2) }));

  const radarData = cityData.slice(0, 6).map(c => ({
    city: c.city, AQI: c.mean_aqi,
  }));

  if (loading) return <LoadingSpinner text="Loading analytics…" />;

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="page-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
          <p className="text-gray-500 text-sm mt-0.5">Interactive environmental data visualisation</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select className="input w-auto text-sm" value={city} onChange={e => setCity(e.target.value)}>
            <option value="">All Cities</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="input w-auto text-sm" value={granularity} onChange={e => setGranularity(e.target.value)}>
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
          <select className="input w-auto text-sm" value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
            <option value={365}>1 year</option>
          </select>
        </div>
      </div>

      {/* AQI Trend — Area Chart */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-800 mb-4">AQI Trend ({granularity})</h3>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={trend}>
            <defs>
              <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#1e3a5f" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#1e3a5f" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => granularity === 'daily' ? d?.slice(5) : d} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => [Number(v).toFixed(1), 'AQI']} />
            <Legend />
            <Area type="monotone" dataKey="mean" stroke="#1e3a5f" fill="url(#areaGrad)" strokeWidth={2} name="Mean AQI" />
            <Area type="monotone" dataKey="max"  stroke="#e74c3c" fill="none" strokeWidth={1.5} strokeDasharray="5 3" name="Max AQI" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* City comparison */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">City AQI Comparison</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={cityData.slice(0, 10)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="city" type="category" tick={{ fontSize: 11 }} width={80} />
              <Tooltip formatter={(v) => [Number(v).toFixed(1), 'Mean AQI']} />
              <Bar dataKey="mean_aqi" fill="#2d6a4f" radius={[0, 4, 4, 0]} name="Mean AQI" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pollutant levels */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">Average Pollutant Concentrations</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={pollutantBarData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [`${v}`, 'Avg Conc.']} />
              <Bar dataKey="value" fill="#e76f51" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Radar + Model comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">City AQI Radar</h3>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="city" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={{ fontSize: 9 }} />
              <Radar dataKey="AQI" stroke="#1e3a5f" fill="#1e3a5f" fillOpacity={0.3} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Model metrics table */}
        <div className="card overflow-x-auto">
          <h3 className="text-base font-semibold text-gray-800 mb-4">ML Model Comparison</h3>
          {models.length > 0 ? (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  {['Model', 'MAE', 'RMSE', 'R²', 'Active'].map(h => (
                    <th key={h} className="table-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {models.map((m, i) => (
                  <tr key={m.id} className={i % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                    <td className="table-cell font-medium">{m.name}</td>
                    <td className="table-cell">{m.metrics?.mae?.toFixed(3) ?? '—'}</td>
                    <td className="table-cell">{m.metrics?.rmse?.toFixed(3) ?? '—'}</td>
                    <td className="table-cell">{m.metrics?.r2_score?.toFixed(4) ?? '—'}</td>
                    <td className="table-cell">
                      {m.is_active
                        ? <span className="badge bg-green-100 text-green-700">Active</span>
                        : <span className="badge bg-gray-100 text-gray-500">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">No models trained yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
