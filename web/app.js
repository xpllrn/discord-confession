
const toggle = document.querySelector('.nav-toggle');
const links = document.querySelector('.nav-links');
if (toggle && links) {
  toggle.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
}

async function loadStatus() {
  const root = document.querySelector('[data-status-root]');
  if (!root) return;
  const offlineName = root.getAttribute('data-offline-name') || 'the bot';
  const banner = root.querySelector('[data-status-banner]');
  const title = root.querySelector('[data-status-title]');
  const updated = root.querySelector('[data-status-updated]');
  const latency = root.querySelector('[data-metric-latency]');
  const guilds = root.querySelector('[data-metric-guilds]');
  const uptime = root.querySelector('[data-metric-uptime]');
  const services = root.querySelector('[data-services]');

  const endpoints = ['/api/status'];

  let data = null;
  for (const url of endpoints) {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 2500);
      const res = await fetch(url, { signal: ctrl.signal, cache: 'no-store' });
      clearTimeout(t);
      if (res.ok) { data = await res.json(); break; }
    } catch (_) {}
  }

  const stamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  if (updated) updated.textContent = `Checked ${stamp}`;

  if (!data) {
    banner?.classList.add('is-bad');
    banner?.classList.remove('is-loading', 'is-ok');
    if (title) title.textContent = `Can’t reach ${offlineName} right now`;
    if (latency) latency.textContent = '—';
    if (guilds) guilds.textContent = '—';
    if (uptime) uptime.textContent = '—';
    if (services) {
      services.innerHTML = `<div class="svc"><div><strong>Cluster</strong><small>Live metrics unavailable. Try again in a moment.</small></div><span class="pill is-bad">Offline</span></div>`;
    }
    return;
  }

  const ok = data.status === 'operational';
  banner?.classList.toggle('is-bad', !ok);
  banner?.classList.toggle('is-ok', ok);
  banner?.classList.remove('is-loading');
  if (title) title.textContent = ok ? 'All systems operational' : 'Degraded performance';
  if (latency) latency.textContent = data.latency_ms != null ? `${data.latency_ms} ms` : '—';
  if (guilds) guilds.textContent = data.guilds != null ? Number(data.guilds).toLocaleString() : '—';
  if (uptime) {
    const s = Number(data.uptime_seconds || 0);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    uptime.textContent = h > 0 ? `${h}h ${m}m` : `${m}m`;
  }
  if (services && Array.isArray(data.services)) {
    services.innerHTML = data.services.map((svc) => {
      const good = svc.status === 'operational' || svc.status === 'online';
      return `<div class="svc"><div><strong>${svc.name}</strong><small>${svc.details || ''}</small></div><span class="pill ${good ? '' : 'is-bad'}">${good ? 'Operational' : 'Issue'}</span></div>`;
    }).join('');
  }
}

loadStatus();
setInterval(loadStatus, 15000);
