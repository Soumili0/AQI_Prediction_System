import React from 'react';
import { titleCase } from '../../utils/formatters';
import { formatRelativeTime } from '../../utils/formatters';

/**
 * UserTable — reusable table for displaying users in the admin panel.
 *
 * Props:
 *   users        {Array}    - list of user objects from API
 *   onToggle     {Function} - (user) => void  — activate/deactivate
 *   onRoleChange {Function} - (user, newRole) => void
 */
export default function UserTable({ users = [], onToggle, onRoleChange }) {
  const ROLES = ['citizen', 'researcher', 'policy_maker', 'admin'];

  if (!users.length) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        No users found.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-100">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            {['ID', 'Name', 'Email', 'Role', 'Status', 'Verified', 'Last Login', 'Actions'].map(h => (
              <th key={h} className="table-header">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {users.map((user, i) => (
            <tr key={user.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
              <td className="table-cell text-gray-400 text-xs">{user.id}</td>
              <td className="table-cell">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold shrink-0">
                    {(user.first_name?.[0] || user.username?.[0] || 'U').toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">
                      {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.username}
                    </p>
                    <p className="text-xs text-gray-400">@{user.username}</p>
                  </div>
                </div>
              </td>
              <td className="table-cell text-xs text-gray-500">{user.email}</td>
              <td className="table-cell">
                <select
                  value={user.role}
                  onChange={e => onRoleChange?.(user, e.target.value)}
                  className="text-xs border border-gray-200 rounded-md px-2 py-1 bg-white focus:ring-1 focus:ring-primary/40 focus:outline-none"
                >
                  {ROLES.map(r => (
                    <option key={r} value={r}>{titleCase(r)}</option>
                  ))}
                </select>
              </td>
              <td className="table-cell">
                <span className={`badge ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {user.is_active ? '● Active' : '○ Inactive'}
                </span>
              </td>
              <td className="table-cell">
                <span className={`badge ${user.is_verified ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {user.is_verified ? '✓ Yes' : '! No'}
                </span>
              </td>
              <td className="table-cell text-xs text-gray-400">
                {user.last_login ? formatRelativeTime(user.last_login) : 'Never'}
              </td>
              <td className="table-cell">
                <button
                  onClick={() => onToggle?.(user)}
                  className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                    user.is_active
                      ? 'bg-red-50 text-red-600 hover:bg-red-100'
                      : 'bg-green-50 text-green-600 hover:bg-green-100'
                  }`}
                >
                  {user.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
