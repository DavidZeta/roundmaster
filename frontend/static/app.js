// ── Config ────────────────────────────────────────────────────────────
const API = 'http://localhost:8000/api';

// ── API helper ────────────────────────────────────────────────────────
async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

const get  = (path)         => api('GET',    path);
const post = (path, body)   => api('POST',   path, body);
const put  = (path, body)   => api('PUT',    path, body);
const del  = (path)         => api('DELETE', path);

// ── Toast ─────────────────────────────────────────────────────────────
function toast(msg, type = 'ok') {
  let c = document.getElementById('toast-container');
  if (!c) {
    c = document.createElement('div');
    c.id = 'toast-container';
    document.body.appendChild(c);
  }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

// ── Tabs ──────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(target)?.classList.add('active');
    });
  });
}

// ── Formato fecha ─────────────────────────────────────────────────────
function fmtFecha(str) {
  if (!str) return '—';
  const [y, m, d] = str.split('-');
  return `${d}/${m}/${y}`;
}

// ── Resultado label ───────────────────────────────────────────────────
function labelResultado(r) {
  if (!r) return '<span class="badge badge-gray">Pendiente</span>';
  if (r === 'bye') return '<span class="badge badge-blue">BYE</span>';
  if (r === 'empate') return '<span class="badge badge-gold">Empate</span>';
  return '<span class="badge badge-green">Registrado</span>';
}
