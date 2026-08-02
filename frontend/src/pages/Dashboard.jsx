import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MdOutlineAir, MdBarChart, MdHistory, MdWarning, MdRefresh } from 'react-icons/md';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell,
} from 'recharts';
import toast from 'react-hot-toast';
import { analyticsService } from '../services/analyticsService';
import { predictionService } from '../services/predictionService';
import useAuthStore from '../store/authStore';
import StatCard from '../components/common/StatCard';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { getAQIColor, getAQIBadgeClass, formatAQI, formatDate } from '../utils/aqiUtils';

const PIE_COLORS = ['#00e400','#ffff00','#ff7e00','#ff0000','#8f3f97','#7e0023'];

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const [overview, setOverview]         = useState(null);
  const [trend, setTrend]               = useState([]);
  const [pollutants, setPollutants]     = useState({});
  const [recentPreds, setRecentPreds]   = useState([]);
  const [selectedCity, setSelectedCity] = useState('');
  const [cities, setCities]             = useState([]);
  const [loading, setLoading]           = useState(true);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [ovRes, trendRes, pollRes, predRes, cityRes] = await Promise.allSettled([
        analyticsService.getOverview(selectedCity || undefined, 30),
        analyticsService.getTrend(selectedCity || undefined, 'daily', 30),
        analyticsService.getPollutants(selectedCity || undefined, 30),
        predictionService.getHistory(1, 5),
        analyticsService.getCityList(),
      ]);

      if (ovRes.status === 'fulfilled')    setOverview(ovRes.value.data);
      if (trendRes.status === 'fulfilled') setTrend(trendRes.value.data.trend || []);
      if (pollRes.status === 'fulfilled')  setPollutants(pollRes.value.data.pollutants || {});
      if (predRes.status === 'fulfilled')  setRecentPreds(predRes.value.data?.predictions || []);
      if (cityRes.status === 'fulfilled')  setCities(cityRes.value.data.cities || []);
    } catch {
      toast.error('Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, [selectedCity]);

  const categoryData = overview?.category_breakdown
    ? Object.entries(overview.category_breakdown).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const pollutantData = Object.entries(pollutants)
    .filter(([, v]) => v != null)
    .map(([k, v]) => ({ name: k.toUpperCase(), value: parseFloat(v).toFixed(2) }));

  if (loading) return <LoadingSpinner text="Loading dashboard…" />;

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.first_name || user?.username} 👋
          </h2>
          <p className="text-gray-500 text-sm mt-0.5">Here's the current air quality overview</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            className="input w-auto text-sm"
            value={selectedCity}
            onChange={e => setSelectedCity(e.target.value)}
          >
            <option value="">All Cities</option>
            {cities.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
            ))}
          </select>
          <button onClick={fetchAll} className="btn-outline py-2 px-3">
            <MdRefresh size={18} />
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card col-span-1 sm:col-span-2 lg:col-span-1 flex flex-col items-center justify-center text-center bg-gradient-to-br from-primary to-primary-700 text-white border-0">
          <p className="text-sm font-medium text-blue-200 mb-1">Current AQI</p>
          <p className="text-6xl font-black mb-2"
            style={{ color: getAQIColor(overview?.current_aqi) }}>
            {formatAQI(overview?.current_aqi)}
          </p>
          <span className={`badge text-sm px-3 py-1 ${getAQIBadgeClass(overview?.aqi_category)}`}>
            {overview?.aqi_category || '—'}
          </span>
          <p className="text-xs text-blue-200 mt-3 max-w-[180px]">
            {overview?.health_advisory || 'Monitor air quality regularly'}
          </p>
        </div>

        <StatCard title="Mean AQI (30d)"      value={overview?.mean_aqi}    icon={MdOutlineAir} color="blue"   />
        <StatCard title="Max AQI (30d)"       value={overview?.max_aqi}     icon={MdWarning}    color="orange" />
        <StatCard title="Total Readings"      value={overview?.total_readings?.toLocaleString()} icon={MdHistory} color="green" />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AQI trend line chart */}
        <div className="card lg:col-span-2">
          <h3 className="text-base font-semibold text-gray-800 mb-4">AQI Trend (Last 30 Days)</h3>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }}
                  tickFormatter={d => d?.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v) => [Number(v).toFixed(1), 'AQI']}
                  labelFormatter={l => `Date: ${l}`}
                />
                <Line type="monotone" dataKey="mean" stroke="#1e3a5f" strokeWidth={2} dot={false} name="Mean AQI" />
                <Line type="monotone" dataKey="max"  stroke="#e74c3c" strokeWidth={1.5} dot={false} name="Max AQI" strokeDasharray="5 3" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400">No trend data available</div>
          )}
        </div>

        {/* Category pie */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">AQI Category Breakdown</h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={categoryData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                  dataKey="value" label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                  labelLine={false}>
                  {categoryData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v, n) => [v, n]} />
                <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400">No data</div>
          )}
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pollutant bar */}
        <div className="card">
          <h3 className="text-base font-semibold text-gray-800 mb-4">Average Pollutant Levels</h3>
          {pollutantData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={pollutantData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={45} />
                <Tooltip formatter={(v) => [`${v} µg/m³`, 'Avg']} />
                <Bar dataKey="value" fill="#2d6a4f" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-gray-400">No data</div>
          )}
        </div>

        {/* Recent predictions */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-800">Recent Predictions</h3>
            <Link to="/history" className="text-xs text-primary hover:underline">View all →</Link>
          </div>
          {recentPreds.length > 0 ? (
            <div className="space-y-2.5">
              {recentPreds.map((p) => (
                <div key={p.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{p.city || 'Unknown'}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDate(p.requested_at)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold" style={{ color: getAQIColor(p.predicted_aqi) }}>
                      {formatAQI(p.predicted_aqi)}
                    </p>
                    <span className={`badge text-xs ${getAQIBadgeClass(p.aqi_category)}`}>
                      {p.aqi_category || '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-40 flex flex-col items-center justify-center text-gray-400 gap-3">
              <p className="text-sm">No predictions yet</p>
              <Link to="/prediction" className="btn-primary text-xs py-1.5 px-3">
                Make your first prediction →
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { to: '/prediction', label: 'Predict AQI',  icon: '🎯', color: 'from-blue-500 to-blue-700' },
          { to: '/analytics',  label: 'View Analytics',icon: '📊', color: 'from-green-500 to-green-700' },
          { to: '/history',    label: 'History',       icon: '📅', color: 'from-orange-500 to-orange-700' },
          { to: '/reports',    label: 'Reports',       icon: '📄', color: 'from-purple-500 to-purple-700' },
        ].map(({ to, label, icon, color }) => (
          <Link key={to} to={to}
            className={`bg-gradient-to-br ${color} text-white rounded-xl p-4 text-center hover:opacity-90 transition-opacity`}>
            <div className="text-2xl mb-1">{icon}</div>
            <div className="text-sm font-semibold">{label}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
