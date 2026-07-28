import React from 'react';
import clsx from 'clsx';

/**
 * Pagination — reusable page navigation bar.
 *
 * Props:
 *   page      {number}   - current page (1-based)
 *   pages     {number}   - total pages
 *   total     {number}   - total records count
 *   perPage   {number}   - records per page
 *   onPage    {Function} - (newPage) => void
 */
export default function Pagination({ page, pages, total, perPage, onPage }) {
  if (!pages || pages <= 1) return null;

  const from = (page - 1) * perPage + 1;
  const to   = Math.min(page * perPage, total);

  // Build page number list with ellipsis
  const buildPages = () => {
    const arr = [];
    if (pages <= 7) {
      for (let i = 1; i <= pages; i++) arr.push(i);
      return arr;
    }
    arr.push(1);
    if (page > 4) arr.push('...');
    for (let i = Math.max(2, page - 2); i <= Math.min(pages - 1, page + 2); i++) arr.push(i);
    if (page < pages - 3) arr.push('...');
    arr.push(pages);
    return arr;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4">
      <p className="text-sm text-gray-500">
        Showing <strong>{from.toLocaleString()}</strong>–<strong>{to.toLocaleString()}</strong> of{' '}
        <strong>{total?.toLocaleString()}</strong> results
      </p>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPage(page - 1)}
          disabled={page === 1}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-600
                     hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          ← Prev
        </button>

        {buildPages().map((p, i) =>
          p === '...' ? (
            <span key={`e-${i}`} className="px-2 text-gray-400 text-sm">…</span>
          ) : (
            <button
              key={p}
              onClick={() => onPage(p)}
              className={clsx(
                'w-9 h-9 text-sm rounded-lg border transition-colors',
                p === page
                  ? 'bg-primary text-white border-primary font-semibold'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              )}
            >
              {p}
            </button>
          )
        )}

        <button
          onClick={() => onPage(page + 1)}
          disabled={page === pages}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-600
                     hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
