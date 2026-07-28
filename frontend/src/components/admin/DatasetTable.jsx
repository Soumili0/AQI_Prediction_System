import React from 'react';
import { formatBytes, formatDateOnly } from '../../utils/formatters';
import clsx from 'clsx';

/**
 * DatasetTable — reusable table for displaying datasets in the admin panel.
 *
 * Props:
 *   datasets  {Array}    - list of dataset objects from API
 *   onDelete  {Function} - (datasetId) => void
 */
export default function DatasetTable({ datasets = [], onDelete }) {
  const statusStyle = {
    ready:      'bg-green-100 text-green-700',
    processing: 'bg-blue-100 text-blue-700',
    pending:    'bg-yellow-100 text-yellow-700',
    failed:     'bg-red-100 text-red-700',
  };

  const sourceStyle = {
    csv_upload:  'bg-purple-100 text-purple-700',
    openaq_api:  'bg-teal-100 text-teal-700',
    government:  'bg-orange-100 text-orange-700',
    historical:  'bg-gray-100 text-gray-700',
  };

  if (!datasets.length) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        No datasets found.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-100">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            {['ID', 'Name', 'Source', 'Status', 'Rows', 'Size', 'Location', 'Created', 'Actions'].map(h => (
              <th key={h} className="table-header">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {datasets.map((ds, i) => (
            <tr key={ds.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
              <td className="table-cell text-gray-400 text-xs">{ds.id}</td>
              <td className="table-cell">
                <p className="font-medium text-gray-800 max-w-[180px] truncate" title={ds.name}>
                  {ds.name}
                </p>
                {ds.original_filename && (
                  <p className="text-xs text-gray-400 truncate max-w-[180px]">{ds.original_filename}</p>
                )}
              </td>
              <td className="table-cell">
                <span className={clsx('badge', sourceStyle[ds.source] || 'bg-gray-100 text-gray-600')}>
                  {ds.source?.replace('_', ' ')}
                </span>
              </td>
              <td className="table-cell">
                <span className={clsx('badge', statusStyle[ds.status] || 'bg-gray-100 text-gray-600')}>
                  {ds.status}
                </span>
              </td>
              <td className="table-cell">{ds.row_count?.toLocaleString() ?? '—'}</td>
              <td className="table-cell text-xs">{ds.file_size_kb ? formatBytes(ds.file_size_kb * 1024) : '—'}</td>
              <td className="table-cell text-xs text-gray-500">{ds.location || '—'}</td>
              <td className="table-cell text-xs text-gray-400">{formatDateOnly(ds.created_at)}</td>
              <td className="table-cell">
                <button
                  onClick={() => {
                    if (window.confirm(`Delete dataset "${ds.name}"? This also removes all its readings.`)) {
                      onDelete?.(ds.id);
                    }
                  }}
                  className="text-xs px-2.5 py-1 rounded-md font-medium bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
