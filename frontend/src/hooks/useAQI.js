import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { predictionService } from '../services/predictionService';
import { analyticsService }  from '../services/analyticsService';
import { getAQICategory }    from '../utils/aqiUtils';

/**
 * useAQI
 * ------
 * Centralised hook for AQI prediction and analytics data fetching.
 * Used by Dashboard, Prediction page, and any widget that needs live AQI data.
 *
 * @returns prediction state, analytics state, and action functions
 */
export function useAQI() {
  // ── Prediction state ────────────────────────────────────────────
  const [prediction,  setPrediction]  = useState(null);
  const [predLoading, setPredLoading] = useState(false);
  const [predError,   setPredError]   = useState(null);

  // ── Analytics state ─────────────────────────────────────────────
  const [overview,    setOverview]    = useState(null);
  const [trend,       setTrend]       = useState([]);
  const [cities,      setCities]      = useState([]);
  const [pollutants,  setPollutants]  = useState({});
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // ── Predict ──────────────────────────────────────────────────────
  const predict = useCallback(async (features) => {
    setPredLoading(true);
    setPredError(null);
    try {
      const res  = await predictionService.predict(features);
      const data = res.data;
      setPrediction(data);
      return data;
    } catch (err) {
      const msg = err.response?.data?.error || 'Prediction failed.';
      setPredError(msg);
      toast.error(msg);
      return null;
    } finally {
      setPredLoading(false);
    }
  }, []);

  const clearPrediction = useCallback(() => {
    setPrediction(null);
    setPredError(null);
  }, []);

  // ── Fetch analytics ──────────────────────────────────────────────
  const fetchAnalytics = useCallback(async (city, days = 30) => {
    setAnalyticsLoading(true);
    try {
      const [ovRes, trendRes, pollRes, cityRes] = await Promise.allSettled([
        analyticsService.getOverview(city || undefined, days),
        analyticsService.getTrend(city || undefined, 'daily', days),
        analyticsService.getPollutants(city || undefined, days),
        analyticsService.getCities(),
      ]);

      if (ovRes.status   === 'fulfilled') setOverview(ovRes.value.data);
      if (trendRes.status=== 'fulfilled') setTrend(trendRes.value.data.trend || []);
      if (pollRes.status === 'fulfilled') setPollutants(pollRes.value.data.pollutants || {});
      if (cityRes.status === 'fulfilled') setCities(cityRes.value.data.cities || []);
    } catch {
      toast.error('Failed to load analytics data.');
    } finally {
      setAnalyticsLoading(false);
    }
  }, []);

  // ── Derived helpers ──────────────────────────────────────────────
  const aqiCategory    = prediction ? getAQICategory(prediction.predicted_aqi) : null;
  const currentAQI     = overview?.current_aqi  ?? null;
  const currentCat     = aqiCategory?.label ?? overview?.aqi_category ?? null;

  return {
    // Prediction
    prediction, predLoading, predError, predict, clearPrediction, aqiCategory,
    // Analytics
    overview, trend, cities, pollutants, analyticsLoading, fetchAnalytics,
    // Derived
    currentAQI, currentCat,
  };
}
