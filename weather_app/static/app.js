// Weather Report dashboard: the drawer's cities, the search, and the weather of the chosen city (from /api).
const $ = (id) => document.getElementById(id);
const state = { cities: [], selected: null, units: localStorage.getItem('units') || 'metric' };

async function call(method, url, body) {
  const res = await fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : {}, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

function showError(message) { $('error').textContent = message; $('error').hidden = !message; }
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
const hour = (iso) => iso.slice(11, 16);
const dayName = (iso, i) => (i === 0 ? 'Today' : new Date(`${iso}T12:00:00`).toLocaleDateString([], { weekday: 'short' }));
const compass = (deg) => ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.round(deg / 45) % 8];

// ---------- drawer ----------
function openDrawer(open) {
  $('drawer').classList.toggle('open', open);
  $('scrim').hidden = !open;
  $('menu').setAttribute('aria-expanded', String(open));
}
$('menu').addEventListener('click', () => openDrawer(true));
$('scrim').addEventListener('click', () => openDrawer(false));

function renderCities() {
  const list = $('city-list');
  list.replaceChildren();
  for (const c of state.cities) {
    const li = el('li', `city${state.selected && state.selected.id === c.id ? ' active' : ''}`);
    const pick = el('button', 'pick');
    pick.type = 'button';
    pick.append(c.name, el('small', '', c.country));
    pick.addEventListener('click', () => { select(c); openDrawer(false); });
    const remove = el('button', 'remove', '×');
    remove.type = 'button';
    remove.setAttribute('aria-label', `Remove ${c.name}`);
    remove.addEventListener('click', async () => {
      try {
        await call('DELETE', `/api/cities/${c.id}`);
        state.cities = state.cities.filter((x) => x.id !== c.id);
        if (state.selected && state.selected.id === c.id) select(state.cities[0] || null);
        renderCities();
      } catch (err) { showError(err.message); }
    });
    li.append(pick, remove);
    list.append(li);
  }
}

function renderUnits() {
  document.querySelectorAll('.unit').forEach((b) => b.classList.toggle('on', b.dataset.units === state.units));
}
document.querySelectorAll('.unit').forEach((b) => b.addEventListener('click', () => {
  state.units = b.dataset.units;
  localStorage.setItem('units', state.units);
  renderUnits();
  if (state.selected) loadWeather();
}));

// ---------- search ----------
let searchTimer;
$('city-search').addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  const q = e.target.value.trim();
  if (q.length < 2) { $('search-results').hidden = true; return; }
  searchTimer = setTimeout(async () => {
    try {
      const found = await call('GET', `/api/search?q=${encodeURIComponent(q)}`);
      const box = $('search-results');
      box.replaceChildren();
      if (!found.length) box.append(el('li', 'none', 'No place found'));
      for (const p of found) {
        const li = el('li');
        const b = el('button', '', `${p.name}${p.region ? ', ' + p.region : ''} · ${p.country}`);
        b.type = 'button';
        b.addEventListener('click', () => addCity(p));
        li.append(b);
        box.append(li);
      }
      box.hidden = false;
    } catch (err) { showError(err.message); }
  }, 300);
});

async function addCity(p) {
  try {
    const city = await call('POST', '/api/cities', { name: p.name, country: p.country, latitude: p.latitude, longitude: p.longitude });
    state.cities.push(city);
    $('city-search').value = '';
    $('search-results').hidden = true;
    select(city);
    openDrawer(false);
  } catch (err) { showError(err.message); }
}

// ---------- the dashboard ----------
function select(city) {
  state.selected = city;
  renderCities();
  if (city) loadWeather();
  else { $('dashboard').hidden = true; $('place').textContent = 'Weather Report'; $('updated').textContent = 'Add a city to begin'; }
}

async function loadWeather() {
  const c = state.selected;
  $('place').textContent = `${c.name}${c.country ? ', ' + c.country : ''}`;
  $('updated').textContent = 'Loading...';
  try {
    const w = await call('GET', `/api/weather?lat=${c.latitude}&lon=${c.longitude}&units=${state.units}`);
    if (state.selected !== c) return; // another city was chosen meanwhile
    showError('');
    render(w);
  } catch (err) {
    $('updated').textContent = '';
    showError(err.message);
  }
}

function render(w) {
  const t = w.units.temp;
  const now = w.current;
  const today = w.daily[0];
  $('updated').textContent = `Local time ${now.time.replace('T', ' ')} · ${w.timezone}`;
  $('hero').classList.toggle('night', !now.isDay);
  $('now-icon').textContent = now.icon;
  $('now-temp').textContent = `${Math.round(now.temperature)}${t}`;
  $('now-text').textContent = now.text;
  $('now-range').textContent = today ? `High ${Math.round(today.max)}${t} · Low ${Math.round(today.min)}${t}` : '';
  $('feels').textContent = `${Math.round(now.feelsLike)}${t}`;
  $('humidity').textContent = `${now.humidity}%`;
  $('wind').textContent = `${Math.round(now.windSpeed)} ${w.units.wind} ${compass(now.windDirection)}`;
  $('sun').textContent = today ? `${hour(today.sunrise)} · ${hour(today.sunset)}` : '-';
  renderChart(w.hourly, t);
  const days = $('days');
  days.replaceChildren();
  w.daily.forEach((d, i) => {
    const li = el('li', 'day');
    li.append(el('b', '', dayName(d.date, i)), el('span', 'icon', d.icon), el('span', 'hi', `${Math.round(d.max)}°`), ' ', el('span', 'lo', `${Math.round(d.min)}°`));
    if (d.precip > 0) li.append(el('span', 'rain', `${d.precip} mm`));
    li.title = d.text;
    days.append(li);
  });
  $('dashboard').hidden = false;
}

// the next 24 hours: a temperature line over bars for the chance of rain (inline SVG, no chart library)
function renderChart(hours, unit) {
  const W = 760, H = 220, P = { l: 30, r: 16, t: 26, b: 34 };
  const temps = hours.map((h) => h.temperature);
  const lo = Math.min(...temps) - 1, hi = Math.max(...temps) + 1;
  const x = (i) => P.l + (i * (W - P.l - P.r)) / Math.max(1, hours.length - 1);
  const y = (v) => P.t + ((hi - v) * (H - P.t - P.b)) / (hi - lo || 1);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const add = (tag, attrs, text) => { const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (text !== undefined) e.textContent = text; svg.append(e); return e; };
  const barW = (W - P.l - P.r) / hours.length * 0.6;
  hours.forEach((h, i) => {
    const bh = ((h.precipChance || 0) / 100) * (H - P.t - P.b);
    add('rect', { class: 'rain-bar', x: x(i) - barW / 2, y: H - P.b - bh, width: barW, height: bh });
  });
  const line = hours.map((h, i) => `${x(i)},${y(h.temperature)}`).join(' ');
  add('polygon', { class: 'temp-area', points: `${x(0)},${H - P.b} ${line} ${x(hours.length - 1)},${H - P.b}` });
  add('polyline', { class: 'temp-line', points: line });
  hours.forEach((h, i) => {
    if (i % 3 !== 0) return;
    add('text', { x: x(i), y: H - 12, 'text-anchor': 'middle' }, hour(h.time));
    add('text', { class: 'temp-label', x: x(i), y: y(h.temperature) - 8, 'text-anchor': 'middle' }, `${Math.round(h.temperature)}°`);
  });
  add('text', { x: W - P.r, y: 14, 'text-anchor': 'end' }, `line: temperature (${unit}) · bars: chance of rain`);
  $('chart').replaceChildren(svg);
}

// ---------- start ----------
(async () => {
  renderUnits();
  try {
    state.cities = await call('GET', '/api/cities');
    select(state.cities[0] || null);
  } catch (err) { showError(err.message); }
})();
