import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { MdDownload, MdPictureAsPdf, MdTableChart } from 'react-icons/md';
import api from '../services/api';

const REPORT_TYPES = [
  {
    id: 'prediction-history',
    title: 'Prediction History',
    desc:  'Download all your AQI prediction records with input features and results.',
    icon:  '🎯',
  },
  {
    id: 'analytics',
    title: 'Analytics Report',
    desc:  'City-wise AQI summary, pollutant averages, and category breakdown.',
    icon:  '📊',
  },
];

export default function Reports() {
  const [loading, setLoading] = useState({});
  const [city, setCity]       = useState('');
  const [days, setDays]       = useState(30);

  const download = async (endpoint, params, filename) => {
    setLoading(l => ({ ...l, [filename]: true }));
    try {
      const res = await api.post(`/reports/${endpoint}`, params, { responseType: 'blob' });
      const url  = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href  = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${filename} downloaded successfully!`);
    } catch {
      toast.error('Failed to generate report. Please try again.');
    } finally {
      setLoading(l => ({ ...l, [filename]: false }));
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="page-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Reports</h2>
          <p className="text-gray-500 text-sm mt-0.5">Generate and download PDF or CSV reports</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap items-end gap-4">
        <div>
          <label className="label">Filter by City</label>
          <input type="text" placeholder="e.g. Delhi" className="input w-48"
            value={city} onChange={e => setCity(e.target.value)} />
        </div>
        <div>
          <label className="label">Period (days)</label>
          <select className="input w-32" value={days} onChange={e => setDays(Number(e.target.value))}>
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>1 year</option>
          </select>
        </div>
      </div>

      {/* Report cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {REPORT_TYPES.map(({ id, title, desc, icon }) => (
          <div key={id} className="card hover:shadow-hover transition-shadow">
            <div className="flex items-start gap-4">
              <div className="text-3xl">{icon}</div>
              <div className="flex-1">
                <h3 className="text-base font-semibold text-gray-800 mb-1">{title}</h3>
                <p className="text-sm text-gray-500 mb-5">{desc}</p>

                <div className="flex flex-wrap gap-3">
                  {/* PDF */}
                  <button
                    onClick={() => download(
                      id,
                      { format: 'pdf', city: city || undefined, days },
                      `${id}_${Date.now()}.pdf`
                    )}
                    disabled={loading[`${id}_${Date.now()}.pdf`]}
                    className="btn-primary py-2 px-4 text-sm"
                  >
                    <MdPictureAsPdf size={16} />
                    {loading[`${id}.pdf`] ? 'Generating…' : 'Download PDF'}
                  </button>

                  {/* CSV */}
                  <button
                    onClick={() => download(
                      id,
                      { format: 'csv', city: city || undefined, days },
                      `${id}_${Date.now()}.csv`
                    )}
                    disabled={loading[`${id}.csv`]}
                    className="btn-outline py-2 px-4 text-sm"
                  >
                    <MdTableChart size={16} />
                    {loading[`${id}.csv`] ? 'Generating…' : 'Download CSV'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="card bg-blue-50 border-blue-100">
        <div className="flex items-start gap-3">
          <span className="text-2xl">ℹ️</span>
          <div>
            <h4 className="text-sm font-semibold text-blue-800 mb-1">Report Notes</h4>
            <ul className="text-xs text-blue-700 space-y-1 list-disc list-inside">
              <li>PDF reports are limited to the most recent 500 records.</li>
              <li>CSV exports include up to 10,000 records for analytics and 50,000 for historical data.</li>
              <li>City filter is optional — leave blank for all cities.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
