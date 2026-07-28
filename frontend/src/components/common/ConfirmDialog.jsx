import React from 'react';

/**
 * ConfirmDialog — modal confirmation popup.
 *
 * Props:
 *   isOpen    {boolean}
 *   title     {string}
 *   message   {string}
 *   onConfirm {Function}
 *   onCancel  {Function}
 *   danger    {boolean} - makes confirm button red (default false)
 */
export default function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel, danger = false }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm animate-slide-up">
        <h3 className="text-base font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-500 mb-6 leading-relaxed">{message}</p>

        <div className="flex items-center gap-3 justify-end">
          <button
            onClick={onCancel}
            className="btn-outline py-2 px-4 text-sm"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`py-2 px-4 text-sm rounded-lg font-medium text-white transition-colors ${
              danger
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-primary hover:bg-primary-600'
            }`}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}
