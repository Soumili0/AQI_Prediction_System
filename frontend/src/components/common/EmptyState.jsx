import React from 'react';

/**
 * EmptyState — displayed when a list or dataset has no results.
 *
 * Props:
 *   icon     {string}    - emoji or icon string
 *   title    {string}
 *   message  {string}
 *   action   {ReactNode} - optional CTA button/link
 */
export default function EmptyState({
  icon = '📭',
  title = 'No data found',
  message = 'There is nothing to display here yet.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-5xl mb-4" role="img">{icon}</span>
      <h3 className="text-base font-semibold text-gray-700 mb-2">{title}</h3>
      <p className="text-sm text-gray-400 max-w-sm leading-relaxed mb-5">{message}</p>
      {action && <div>{action}</div>}
    </div>
  );
}
