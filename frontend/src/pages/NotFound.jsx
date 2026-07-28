import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4 text-white">
      <div className="text-center animate-slide-up">
        <div className="text-8xl font-black text-white/30 mb-4">404</div>
        <div className="text-5xl mb-4">🌫️</div>
        <h1 className="text-3xl font-bold mb-3">Page Not Found</h1>
        <p className="text-blue-200 mb-8 max-w-md">
          Looks like this page got lost in the smog. Head back to cleaner air.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link to="/"          className="bg-white text-primary font-semibold px-6 py-3 rounded-xl hover:bg-blue-50 transition-colors">
            Home
          </Link>
          <Link to="/dashboard" className="border-2 border-white/40 text-white font-semibold px-6 py-3 rounded-xl hover:bg-white/10 transition-colors">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
