import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { MdOutlineAir, MdInfo } from 'react-icons/md';
import { predictionService } from '../services/predictionService';
import { getAQIColor, getAQIBadgeClass, getAQICategory } from '../utils/aqiUtils';
import LoadingSpinner from '../components/common/LoadingSpinner';

const FIELDS = [
  { name: 'pm25',         label: 'PM2.5',        unit: 'µg/m³', placeholder: '85.5',   required: true },
  { name: 'pm10',         label: 'PM10',         unit: 'µg/m³', placeholder: '120.0',  required: true },
  { name: 'no2',          label: 'NO₂',          unit: 'µg/m³', placeholder: '45.2',   required: true },
  { name: 'so2',          label: 'SO₂',          unit: 'µg/m³', placeholder: '18.3',   required: true },
  { name: 'co',           label: 'CO',           unit: 'mg/m³', placeholder: '1.2',    required: true },
  { name: 'o3',           label: 'Ozone (O₃)',   unit: 'µg/m³', placeholder: '60.0',   required: true },
  { name: 'nh3',          label: 'NH₃',          unit: 'µg/m³', placeholder: '12.0',   required: false },
  { name: 'temperature',  label: 'Temperature',  unit: '°C',    placeholder: '28.5',   required: false },
  { name: 'humidity',     label: 'Humidity',     unit: '%',     placeholder: '65.0',   required: false },
  { name: 'wind_speed',   label: 'Wind Speed',   unit: 'm/s',   placeholder: '3.2',    required: false },
  { name: 'pressure',     label: 'Pressure',     unit: 'hPa',   placeholder: '1013.0', required: false },
];

export default function Prediction() {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors }, reset } = useForm();

  const onSubmit = async (data) => {
    // Convert string values to numbers
    const payload = { city: data.city || undefined };
    FIELDS.forEach(({ name }) => {
      const v = data[name];
      if (v !== '' && v !== undefined) payload[name] = parseFloat(v);
    });

    setLoading(true);
    try {
      const res = await predictionService.predict(payload);
      setResult(res.data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Prediction failed. Check your inputs.');
    } finally {
      setLoading(false);
    }
  };

  const cat = result ? getAQICategory(result.predicted_aqi) : null;

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="page-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AQI Prediction</h2>
          <p className="text-gray-500 text-sm mt-0.5">Enter pollutant values to predict the Air Quality Index</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input form */}
        <div className="lg:col-span-2 card">
          <h3 className="text-base font-semibold text-gray-800 mb-5 flex items-center gap-2">
            <MdOutlineAir className="text-primary" size={20} />
            Pollutant & Weather Inputs
          </h3>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="label">City (optional)</label>
              <input type="text" placeholder="e.g. Delhi" className="input max-w-sm"
                {...register('city')} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {FIELDS.map(({ name, label, unit, placeholder, required }) => (
                <div key={name}>
                  <label className="label">
                    {label} <span className="text-gray-400 font-normal">({unit})</span>
                    {required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder={placeholder}
                    className="input"
                    {...register(name, {
                      required: required ? `${label} is required` : false,
                      min: { value: 0, message: 'Must be ≥ 0' },
                    })}
                  />
                  {errors[name] && <p className="text-red-500 text-xs mt-1">{errors[name].message}</p>}
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-2">
              <button type="submit" disabled={loading} className="btn-primary py-2.5 px-8">
                {loading ? 'Predicting…' : '🎯 Predict AQI'}
              </button>
              <button type="button" onClick={() => { reset(); setResult(null); }}
                className="btn-outline py-2.5 px-6">
                Reset
              </button>
            </div>
          </form>
        </div>

        {/* Result panel */}
        <div className="space-y-4">
          {loading ? (
            <div className="card"><LoadingSpinner text="Running ML model…" /></div>
          ) : result ? (
            <>
              {/* AQI result */}
              <div className="card text-center"
                style={{ borderTop: `4px solid ${cat?.color}` }}>
                <p className="text-sm text-gray-500 mb-2">Predicted AQI</p>
                <p className="text-7xl font-black mb-3"
                  style={{ color: cat?.color }}>
                  {result.predicted_aqi}
                </p>
                <span className={`badge text-sm px-4 py-1.5 ${getAQIBadgeClass(result.aqi_category)}`}>
                  {result.aqi_category}
                </span>
                <p className="text-sm text-gray-500 mt-4 leading-relaxed">
                  {result.health_advisory}
                </p>
                {result.city && (
                  <p className="text-xs text-gray-400 mt-2">📍 {result.city}</p>
                )}
              </div>

              {/* SHAP feature importance */}
              {result.explanation?.feature_importance && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-gray-800 mb-3">
                    🔍 Top Feature Contributions (SHAP)
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(result.explanation.feature_importance)
                      .slice(0, 8)
                      .map(([feat, val]) => {
                        const isPositive = val > 0;
                        const maxVal = Math.max(...Object.values(result.explanation.feature_importance).map(Math.abs));
                        const width = `${(Math.abs(val) / maxVal) * 100}%`;
                        return (
                          <div key={feat}>
                            <div className="flex justify-between text-xs text-gray-600 mb-0.5">
                              <span className="font-medium">{feat.toUpperCase()}</span>
                              <span className={isPositive ? 'text-red-500' : 'text-blue-500'}>
                                {val > 0 ? '+' : ''}{val.toFixed(3)}
                              </span>
                            </div>
                            <div className="bg-gray-100 rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${isPositive ? 'bg-red-400' : 'bg-blue-400'}`}
                                style={{ width }}
                              />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* SHAP waterfall plot */}
              {result.explanation?.waterfall_plot_b64 && (
                <div className="card">
                  <h4 className="text-sm font-semibold text-gray-800 mb-3">SHAP Waterfall Plot</h4>
                  <img
                    src={`data:image/png;base64,${result.explanation.waterfall_plot_b64}`}
                    alt="SHAP waterfall"
                    className="w-full rounded-lg"
                  />
                </div>
              )}
            </>
          ) : (
            <div className="card text-center py-10">
              <div className="text-4xl mb-3">🌬️</div>
              <p className="text-gray-400 text-sm">Fill in the pollutant values and click "Predict AQI" to see results</p>
              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-left">
                <p className="text-xs text-blue-600 font-medium flex items-center gap-1">
                  <MdInfo size={14} /> Required: PM2.5, PM10, NO₂, SO₂, CO, O₃
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
