import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { predictionService } from '../../services/predictionService';
import { getAQIColor, getAQIBadgeClass, formatAQI, formatDate } from '../../utils/aqiUtils';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * RecentPredictions — shows the last N predictions for the current user.
 *
 * Props:
 *   limit  {number} — how many to show (default 5)
 *   showLink {boolean} — show "View all" link (default true)
 */
export default function RecentPredictions({ limit = 5, showLink = true }) {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading]         = useState(true);

  useEffect(() => {
    predictionService.getHistory(1, limit)
      .then(r => setPredictions(r.data.predictions || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [limit]);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-gray-700">🎯 Recent Predictions</h4>
        {showLink && (
          <Link to="/history" className="text-xs text-primary hover:underline">
            View all →
          </Link>
        )}
      </div>

      {loading ? (
        <LoadingSpinner size="sm" />
      ) : predictions.length === 0 ? (
        <div className="text-center py-6">
          <p className="text-gray-400 text-sm mb-3">No predictions yet</p>
          <Link to="/prediction" className="btn-primary text-xs py-1.5 px-4">
            Make a prediction →
          </Link>
        </div>
      ) : (
        <div className="space-y-2.5">
          {predictions.map(p => (
            <div key={p.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {p.city || 'Unknown location'}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {formatDate(p.requested_at)}
                </p>
              </div>
              <div className="text-right ml-3 shrink-0">
                <p className="text-xl font-black leading-none"
                  style={{ color: getAQIColor(p.predicted_aqi) }}>
                  {formatAQI(p.predicted_aqi)}
                </p>
                <span className={`badge text-xs mt-1 ${getAQIBadgeClass(p.aqi_category)}`}>
                  {p.aqi_category || '—'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
