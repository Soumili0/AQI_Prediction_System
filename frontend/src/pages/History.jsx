import React, { useEffect, useState } from 'react';
import { analyticsService } from '../services/analyticsService';
import { getAQIBadgeClass, formatDate, formatAQI } from '../utils/aqiUtils';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function History() {
  const [readings, setReadings] = useState([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [pages, setPages]       = useState(1);
  const [city, setCity]         = useState('');
  const [cities, setCities]     = useState([]);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo]     = useState('');
  const [loading, setLoading]   = useState(true);
  const PER_PAGE = 50;

  useEffect(() => {
    analyticsService.getCityList().then(r => setCities(r.data.cities || []));
  }, []);

  useEffect(() => {
    setLoading(true);
    analyticsService.getHistory(city || undefined, page, PER_PAGE)
      .then(r => {
        setReadings(r.data.readings || []);
        setTotal(r.data.total || 0);
        setPages(r.data.pages || 1);
      })
      .finally(() => setLoading(false));
  }, [city, page]);

  return (
    <div className="space-y-5 animate-slide-up">
      <div className="page-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Historical Data</h2>
          <p className="text-gray-500 text-sm mt-0.5">{total.toLocaleString()} total readings</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select className="input w-auto text-sm" value={city} onChange={e => { setCity(e.target.value); setPage(1); }}>
            <option value="">All Cities</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="date" className="input w-auto text-sm" value={dateFrom}
            onChange={e => setDateFrom(e.target.value)} placeholder="From" />
          <input type="date" className="input w-auto text-sm" value={dateTo}
            onChange={e => setDateTo(e.target.value)} placeholder="To" />
        </div>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    {['City','Recorded At','PM2.5','PM10','NO₂','SO₂','CO','O₃','Temp','Humidity','AQI','Category'].map(h => (
                      <th key={h} className="table-header">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {readings.map((r, i) => (
                    <tr key={r.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50 hover:bg-gray-100'}>
                      <td className="table-cell font-medium">{r.city}</td>
                      <td className="table-cell text-xs">{formatDate(r.recorded_at)}</td>
                      <td className="table-cell">{r.pm25 ?? '—'}</td>
                      <td className="table-cell">{r.pm10 ?? '—'}</td>
                      <td className="table-cell">{r.no2 ?? '—'}</td>
                      <td className="table-cell">{r.so2 ?? '—'}</td>
                      <td className="table-cell">{r.co ?? '—'}</td>
                      <td className="table-cell">{r.o3 ?? '—'}</td>
                      <td className="table-cell">{r.temperature != null ? `${r.temperature}°` : '—'}</td>
                      <td className="table-cell">{r.humidity != null ? `${r.humidity}%` : '—'}</td>
                      <td className="table-cell font-bold">{formatAQI(r.aqi)}</td>
                      <td className="table-cell">
                        <span className={`badge ${getAQIBadgeClass(r.aqi_category)}`}>
                          {r.aqi_category || '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {readings.length === 0 && (
                    <tr><td colSpan={12} className="text-center py-10 text-gray-400">No data found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}
                className="btn-outline py-1.5 px-4 text-sm disabled:opacity-40">← Prev</button>
              <span className="text-sm text-gray-600">Page {page} of {pages}</span>
              <button onClick={() => setPage(p => Math.min(pages, p+1))} disabled={page === pages}
                className="btn-outline py-1.5 px-4 text-sm disabled:opacity-40">Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
