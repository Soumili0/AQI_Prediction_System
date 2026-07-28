import React from 'react';
import { Link } from 'react-router-dom';
import { MdOutlineAir, MdBarChart, MdSecurity, MdExplore } from 'react-icons/md';

const FEATURES = [
  { icon: MdOutlineAir,  title: 'Real-time AQI Prediction',      desc: 'Accurate predictions using XGBoost, Random Forest, LSTM and more — trained on real sensor data.' },
  { icon: MdBarChart,    title: 'Explainable AI',                 desc: 'Every prediction explained using SHAP and LIME — understand which pollutants drive the AQI.' },
  { icon: MdSecurity,    title: 'Secure & Role-based',            desc: 'JWT authentication, RBAC for Citizens, Researchers, Policy Makers, and Admins.' },
  { icon: MdExplore,     title: 'Interactive Analytics',          desc: 'City-wise trends, seasonal analysis, pollutant heatmaps, and downloadable PDF/CSV reports.' },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary via-primary-600 to-secondary text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-6 md:px-12 py-5">
        <div className="text-xl font-bold">🌍 AQI Prediction</div>
        <div className="flex items-center gap-3">
          <Link to="/login"    className="text-sm text-blue-200 hover:text-white font-medium">Sign In</Link>
          <Link to="/register" className="bg-white text-primary text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors">
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center animate-fade-in">
        <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-1.5 mb-6 text-sm text-blue-100">
          🔬 AI-Powered • Explainable • Open Data
        </div>
        <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
          Predict Air Quality with <span className="text-yellow-300">Explainable AI</span>
        </h1>
        <p className="text-blue-100 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          Industry-grade AQI prediction system powered by XGBoost, LSTM, and real-time sensor data.
          Every prediction explained. Every insight actionable.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/register" className="bg-yellow-400 text-gray-900 font-bold px-8 py-3.5 rounded-xl hover:bg-yellow-300 transition-colors text-base">
            Start Predicting Free
          </Link>
          <Link to="/login" className="border-2 border-white/40 text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-white/10 transition-colors text-base">
            Sign In
          </Link>
        </div>
      </section>

      {/* AQI Scale */}
      <section className="max-w-3xl mx-auto px-6 py-8">
        <h3 className="text-center text-lg font-semibold text-blue-100 mb-4">AQI Health Scale</h3>
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          {[
            { label: 'Good',      range: '0-50',   color: 'bg-green-400' },
            { label: 'Moderate',  range: '51-100',  color: 'bg-yellow-400' },
            { label: 'Sensitive', range: '101-150', color: 'bg-orange-400' },
            { label: 'Unhealthy', range: '151-200', color: 'bg-red-500' },
            { label: 'Very',      range: '201-300', color: 'bg-purple-500' },
            { label: 'Hazardous', range: '301+',    color: 'bg-rose-800' },
          ].map(({ label, range, color }) => (
            <div key={label} className="bg-white/10 rounded-lg p-3 text-center">
              <div className={`w-6 h-6 rounded-full ${color} mx-auto mb-1`} />
              <div className="text-xs font-semibold">{label}</div>
              <div className="text-xs text-blue-200">{range}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-center text-3xl font-bold mb-12">Everything you need</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white/10 backdrop-blur-sm rounded-xl p-6 hover:bg-white/15 transition-colors">
              <div className="bg-yellow-400/20 w-12 h-12 rounded-xl flex items-center justify-center mb-4">
                <Icon size={24} className="text-yellow-300" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{title}</h3>
              <p className="text-blue-100 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="text-center px-6 py-16 border-t border-white/10">
        <h2 className="text-3xl font-bold mb-4">Ready to monitor air quality?</h2>
        <p className="text-blue-200 mb-8">Join researchers, policy makers, and citizens making data-driven decisions.</p>
        <Link to="/register" className="bg-yellow-400 text-gray-900 font-bold px-10 py-4 rounded-xl text-lg hover:bg-yellow-300 transition-colors">
          Get Started — It's Free
        </Link>
      </section>

      <footer className="text-center py-6 text-blue-300 text-sm border-t border-white/10">
        © 2025 AI AQI Prediction System. Built with ❤️ using React + Flask + XGBoost
      </footer>
    </div>
  );
}
