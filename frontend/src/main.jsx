import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { background: '#1e3a5f', color: '#fff', borderRadius: '8px' },
          success: { style: { background: '#2d6a4f' } },
          error:   { style: { background: '#c0392b' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);
