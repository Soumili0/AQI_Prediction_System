import React, { useEffect, useState } from 'react';
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom';
import {
  MdPeople, MdStorage, MdOutlineAir, MdModelTraining,
  MdHistory, MdBarChart, MdRefresh,
} from 'react-icons/md';
import toast from 'react-hot-toast';
import { adminService } from '../services/adminService';
import { getAQIBadgeClass, formatDate } from '../utils/aqiUtils';
import LoadingSpinner from '../components/common/LoadingSpinner';
import StatCard from '../components/common/StatCard';
import clsx from 'clsx';

/* ── Sub-tab nav ── */
const TABS = [
  { id: 'overview',   label: 'Overview',     icon: MdBarChart      },
  { id: 'users',      label: 'Users',         icon: MdPeople        },
  { id: 'datasets',   label: 'Datasets',      icon: MdStorage       },
  { id: 'predictions',label: 'Predictions',   icon: MdOutlineAir    },
  { id: 'models',     label: 'Models',        icon: MdModelTraining },
  { id: 'audit',      label: 'Audit Logs',    icon: MdHistory       },
];

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="space-y-5 animate-slide-up">
      <h2 className="text-2xl font-bold text-gray-900">Admin Panel</h2>

      {/* Tab bar */}
      <div className="flex flex-wrap gap-1 bg-gray-100 p-1 rounded-xl">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={clsx(
              'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === id
                ? 'bg-white text-primary shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            )}>
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      {activeTab === 'overview'    && <AdminOverview />}
      {activeTab === 'users'       && <AdminUsers />}
      {activeTab === 'datasets'    && <AdminDatasets />}
      {activeTab === 'predictions' && <AdminPredictions />}
      {activeTab === 'models'      && <AdminModels />}
      {activeTab === 'audit'       && <AdminAuditLogs />}
    </div>
  );
}

/* ── Overview ── */
function AdminOverview() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    adminService.getStats().then(r => setStats(r.data)).catch(() => {});
  }, []);

  if (!stats) return <LoadingSpinner />;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      <StatCard title="Total Users"       value={stats.total_users?.toLocaleString()}       icon={MdPeople}        color="blue" />
      <StatCard title="Active Users"      value={stats.active_users?.toLocaleString()}      icon={MdPeople}        color="green" />
      <StatCard title="Datasets"          value={stats.total_datasets?.toLocaleString()}    icon={MdStorage}       color="orange" />
      <StatCard title="AQI Readings"      value={stats.total_readings?.toLocaleString()}    icon={MdBarChart}      color="purple" />
      <StatCard title="Predictions Made"  value={stats.total_predictions?.toLocaleString()} icon={MdOutlineAir}   color="blue" />
      <StatCard title="Trained Models"    value={stats.total_models}                        icon={MdModelTraining} color="green" />
      <div className="card sm:col-span-2">
        <p className="text-sm text-gray-500 mb-1">Active Production Model</p>
        <p className="text-xl font-bold text-primary">{stats.active_model || 'None selected'}</p>
      </div>
    </div>
  );
}

/* ── Users ── */
function AdminUsers() {
  const [users, setUsers]   = useState([]);
  const [total, setTotal]   = useState(0);
  const [page, setPage]     = useState(1);
  const [pages, setPages]   = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchUsers = () => {
    setLoading(true);
    adminService.getUsers({ page, per_page: 20, search: search || undefined })
      .then(r => { setUsers(r.data.users || []); setTotal(r.data.total || 0); setPages(r.data.pages || 1); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchUsers(); }, [page]);

  const toggleActive = async (user) => {
    try {
      await adminService.updateUser(user.id, { is_active: !user.is_active });
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'}.`);
      fetchUsers();
    } catch { toast.error('Action failed.'); }
  };

  const changeRole = async (user, role) => {
    try {
      await adminService.updateUser(user.id, { role });
      toast.success('Role updated.');
      fetchUsers();
    } catch { toast.error('Role update failed.'); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <input type="text" placeholder="Search email or username…" className="input max-w-sm"
          value={search} onChange={e => setSearch(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && fetchUsers()} />
        <button onClick={fetchUsers} className="btn-primary py-2 px-4 text-sm">Search</button>
        <span className="text-sm text-gray-500 ml-auto">{total} total users</span>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  {['ID','Username','Email','Role','Status','Verified','Last Login','Actions'].map(h => (
                    <th key={h} className="table-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={u.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="table-cell text-gray-400 text-xs">{u.id}</td>
                    <td className="table-cell font-medium">{u.username}</td>
                    <td className="table-cell text-xs">{u.email}</td>
                    <td className="table-cell">
                      <select value={u.role} className="text-xs border rounded px-1 py-0.5"
                        onChange={e => changeRole(u, e.target.value)}>
                        {['citizen','researcher','policy_maker','admin'].map(r => (
                          <option key={r} value={r}>{r.replace('_',' ')}</option>
                        ))}
                      </select>
                    </td>
                    <td className="table-cell">
                      <span className={`badge ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className={`badge ${u.is_verified ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'}`}>
                        {u.is_verified ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="table-cell text-xs">{u.last_login ? formatDate(u.last_login) : '—'}</td>
                    <td className="table-cell">
                      <button onClick={() => toggleActive(u)}
                        className={`text-xs px-2 py-1 rounded font-medium transition-colors ${
                          u.is_active
                            ? 'bg-red-50 text-red-600 hover:bg-red-100'
                            : 'bg-green-50 text-green-600 hover:bg-green-100'
                        }`}>
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {pages > 1 && (
        <div className="flex items-center gap-2 justify-center">
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}
            className="btn-outline py-1.5 px-3 text-sm disabled:opacity-40">← Prev</button>
          <span className="text-sm text-gray-600">Page {page} of {pages}</span>
          <button onClick={() => setPage(p => Math.min(pages, p+1))} disabled={page === pages}
            className="btn-outline py-1.5 px-3 text-sm disabled:opacity-40">Next →</button>
        </div>
      )}
    </div>
  );
}

/* ── Datasets ── */
function AdminDatasets() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading]   = useState(true);

  const fetchDatasets = () => {
    setLoading(true);
    adminService.getDatasets({ page: 1, per_page: 50 })
      .then(r => setDatasets(r.data.datasets || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDatasets(); }, []);

  const deleteDataset = async (id) => {
    if (!confirm('Delete this dataset and all its readings? This cannot be undone.')) return;
    try {
      await adminService.deleteDataset(id);
      toast.success('Dataset deleted.');
      fetchDatasets();
    } catch { toast.error('Delete failed.'); }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="card p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              {['ID','Name','Source','Status','Rows','Location','Created','Actions'].map(h => (
                <th key={h} className="table-header">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {datasets.map((d, i) => (
              <tr key={d.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="table-cell text-gray-400 text-xs">{d.id}</td>
                <td className="table-cell font-medium max-w-[160px] truncate">{d.name}</td>
                <td className="table-cell">
                  <span className="badge bg-blue-100 text-blue-700">{d.source}</span>
                </td>
                <td className="table-cell">
                  <span className={`badge ${d.status === 'ready' ? 'bg-green-100 text-green-700' : d.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {d.status}
                  </span>
                </td>
                <td className="table-cell">{d.row_count?.toLocaleString() ?? '—'}</td>
                <td className="table-cell">{d.location || '—'}</td>
                <td className="table-cell text-xs">{d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}</td>
                <td className="table-cell">
                  <button onClick={() => deleteDataset(d.id)}
                    className="text-xs bg-red-50 text-red-600 hover:bg-red-100 px-2 py-1 rounded font-medium">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {datasets.length === 0 && (
              <tr><td colSpan={8} className="text-center py-8 text-gray-400">No datasets found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Predictions ── */
function AdminPredictions() {
  const [preds, setPreds]   = useState([]);
  const [total, setTotal]   = useState(0);
  const [page, setPage]     = useState(1);
  const [pages, setPages]   = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    adminService.getPredictions({ page, per_page: 30 })
      .then(r => { setPreds(r.data.predictions || []); setTotal(r.data.total || 0); setPages(r.data.pages || 1); })
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">{total.toLocaleString()} total predictions</p>
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                {['ID','City','Predicted AQI','Category','Model','User','Date'].map(h => (
                  <th key={h} className="table-header">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preds.map((p, i) => (
                <tr key={p.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="table-cell text-gray-400 text-xs">{p.id}</td>
                  <td className="table-cell">{p.city || '—'}</td>
                  <td className="table-cell font-bold">{p.predicted_aqi}</td>
                  <td className="table-cell">
                    <span className={`badge ${getAQIBadgeClass(p.aqi_category)}`}>
                      {p.aqi_category || '—'}
                    </span>
                  </td>
                  <td className="table-cell text-xs">{p.model || '—'}</td>
                  <td className="table-cell text-xs">{p.user_id || 'anon'}</td>
                  <td className="table-cell text-xs">{formatDate(p.requested_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {pages > 1 && (
        <div className="flex items-center gap-2 justify-center">
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}
            className="btn-outline py-1.5 px-3 text-sm disabled:opacity-40">← Prev</button>
          <span className="text-sm text-gray-600">Page {page} of {pages}</span>
          <button onClick={() => setPage(p => Math.min(pages, p+1))} disabled={page === pages}
            className="btn-outline py-1.5 px-3 text-sm disabled:opacity-40">Next →</button>
        </div>
      )}
    </div>
  );
}

/* ── Models ── */
function AdminModels() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchModels = () => {
    setLoading(true);
    adminService.getModels()
      .then(r => setModels(r.data.models || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchModels(); }, []);

  const activate = async (id) => {
    try {
      await adminService.activateModel(id);
      toast.success('Model activated!');
      fetchModels();
    } catch { toast.error('Activation failed.'); }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="card p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              {['ID','Name','Algorithm','MAE','RMSE','R²','Status','Action'].map(h => (
                <th key={h} className="table-header">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {models.map((m, i) => (
              <tr key={m.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="table-cell text-gray-400 text-xs">{m.id}</td>
                <td className="table-cell font-medium">{m.name}</td>
                <td className="table-cell text-xs">{m.algorithm}</td>
                <td className="table-cell">{m.metrics?.mae?.toFixed(3) ?? '—'}</td>
                <td className="table-cell">{m.metrics?.rmse?.toFixed(3) ?? '—'}</td>
                <td className="table-cell">{m.metrics?.r2_score?.toFixed(4) ?? '—'}</td>
                <td className="table-cell">
                  <span className={`badge ${m.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {m.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="table-cell">
                  {!m.is_active && (
                    <button onClick={() => activate(m.id)}
                      className="text-xs bg-primary/10 text-primary hover:bg-primary/20 px-2 py-1 rounded font-medium">
                      Activate
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {models.length === 0 && (
              <tr><td colSpan={8} className="text-center py-8 text-gray-400">No models found. Run training pipeline first.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Audit Logs ── */
function AdminAuditLogs() {
  const [logs, setLogs]     = useState([]);
  const [total, setTotal]   = useState(0);
  const [page, setPage]     = useState(1);
  const [pages, setPages]   = useState(1);
  const [action, setAction] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLogs = () => {
    setLoading(true);
    adminService.getAuditLogs({ page, per_page: 30, action: action || undefined })
      .then(r => { setLogs(r.data.logs || []); setTotal(r.data.total || 0); setPages(r.data.pages || 1); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchLogs(); }, [page]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <input type="text" placeholder="Filter by action (e.g. user.login)…"
          className="input max-w-xs" value={action} onChange={e => setAction(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && fetchLogs()} />
        <button onClick={fetchLogs} className="btn-primary py-2 px-4 text-sm">Filter</button>
        <span className="text-sm text-gray-500 ml-auto">{total.toLocaleString()} entries</span>
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  {['ID','Action','Entity','User ID','Status','IP','Timestamp'].map(h => (
                    <th key={h} className="table-header">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {logs.map((l, i) => (
                  <tr key={l.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="table-cell text-gray-400 text-xs">{l.id}</td>
                    <td className="table-cell font-mono text-xs">{l.action}</td>
                    <td className="table-cell text-xs">{l.entity} {l.entity_id ? `#${l.entity_id}` : ''}</td>
                    <td className="table-cell text-xs">{l.user_id || 'system'}</td>
                    <td className="table-cell">
                      <span className={`badge ${l.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {l.status}
                      </span>
                    </td>
                    <td className="table-cell font-mono text-xs">{l.ip_address}</td>
                    <td className="table-cell text-xs">{formatDate(l.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {pages > 1 && (
        <div className="flex items-center gap-2 justify-center">
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}
            className="btn-outline py-1.5 px-3 text-sm disabled:opacity-40">← Prev</button>
          <span className="text-sm text-gray-600">Page {page} of {pages}</span>
          <button onClick={() => setPage(p => Math.min(pages, p+1))} disabled={page === pages}
            className="btn-outline py-1.5 px-3 text-sm disabled:opacity-40">Next →</button>
        </div>
      )}
    </div>
  );
}
