import React from 'react';

export default function Settings() {
  return (
    <div className="space-y-5 animate-slide-up max-w-2xl">
      <h2 className="text-2xl font-bold text-gray-900">Settings</h2>

      <div className="card space-y-6">
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-3">Notifications</h3>
          {[
            { label: 'Email alerts for AQI above 150', defaultChecked: true },
            { label: 'Weekly analytics summary',        defaultChecked: false },
            { label: 'New prediction notifications',    defaultChecked: true },
          ].map(({ label, defaultChecked }) => (
            <label key={label} className="flex items-center gap-3 py-2 cursor-pointer">
              <input type="checkbox" defaultChecked={defaultChecked}
                className="w-4 h-4 accent-primary rounded" />
              <span className="text-sm text-gray-700">{label}</span>
            </label>
          ))}
        </div>

        <div className="border-t border-gray-100 pt-4">
          <h3 className="text-base font-semibold text-gray-800 mb-3">Display</h3>
          <div>
            <label className="label">Default city</label>
            <input type="text" placeholder="e.g. Delhi" className="input max-w-xs" />
          </div>
          <div className="mt-3">
            <label className="label">Default period</label>
            <select className="input max-w-xs">
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>
          </div>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <h3 className="text-base font-semibold text-gray-800 mb-3">API Access</h3>
          <p className="text-sm text-gray-500 mb-3">
            Use the token below to access the AQI API programmatically.
          </p>
          <div className="flex items-center gap-2">
            <input type="password" className="input max-w-xs font-mono text-sm"
              value="••••••••••••••••••••••••••••••" readOnly />
            <button className="btn-outline py-2 px-3 text-sm">Show</button>
            <button className="btn-outline py-2 px-3 text-sm">Copy</button>
          </div>
        </div>

        <div className="pt-2">
          <button className="btn-primary">Save Settings</button>
        </div>
      </div>
    </div>
  );
}
