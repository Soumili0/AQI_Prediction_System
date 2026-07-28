import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const token = params.get('token');
  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) { setStatus('error'); setMessage('No verification token found.'); return; }
    authService.verifyEmail(token)
      .then(res => { setStatus('success'); setMessage(res.data.message); })
      .catch(err => { setStatus('error'); setMessage(err.response?.data?.error || 'Verification failed.'); });
  }, [token]);

  const icons = { verifying: '⏳', success: '✅', error: '❌' };
  const colors = { verifying: 'text-blue-500', success: 'text-green-600', error: 'text-red-500' };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary to-secondary flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center animate-slide-up">
        <div className="text-5xl mb-4">{icons[status]}</div>
        <h2 className={`text-2xl font-bold mb-3 ${colors[status]}`}>
          {status === 'verifying' ? 'Verifying your email…' : status === 'success' ? 'Email Verified!' : 'Verification Failed'}
        </h2>
        <p className="text-gray-500 mb-6">{message}</p>
        {status !== 'verifying' && (
          <Link to="/login" className="btn-primary">Go to Login</Link>
        )}
      </div>
    </div>
  );
}
