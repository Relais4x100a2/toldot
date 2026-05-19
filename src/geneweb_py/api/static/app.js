'use strict';

// ==================== STATE ====================
const state = {
  token: sessionStorage.getItem('gwToken') || null,
  expiresAt: sessionStorage.getItem('gwExpiresAt') || null,
  stats: null,
  persons: { items: [], page: 1, pages: 1 },
  families: { items: [], page: 1, pages: 1, nameMap: {} },
  currentPersonId: null,
};

// ==================== UTILITAIRES ====================
function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function shortDate(dateStr) {
  if (!dateStr) return '';
  const m = String(dateStr).match(/(\d{4})/);
  return m ? m[1] : String(dateStr);
}

// ==================== API HELPERS ====================
async function apiFetch(path, options = {}) {
  const headers = { 'X-Session-Token': state.token, ...options.headers };
  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    handleExpiry();
    throw new Error('session-expired');
  }
  return res;
}

async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);
  if (!res.ok) throw Object.assign(new Error('api-error'), { status: res.status });
  return res.json();
}

// ==================== SESSION ====================
async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);
  let res;
  try {
    res = await fetch('/api/v1/sessions', { method: 'POST', body: form });
  } catch {
    showUploadError('Impossible de joindre le serveur.');
    return;
  }
  if (res.status === 413) { showUploadError('Fichier trop volumineux (max 10 Mo).'); return; }
  if (res.status === 400 || res.status === 415) { showUploadError('Format invalide, attendu .gw ou .gwplus'); return; }
  if (res.status === 503) { showUploadError('Serveur saturé, réessayez dans quelques minutes.'); return; }
  if (res.status === 429) { showUploadError('Trop de tentatives, réessayez plus tard.'); return; }
  if (!res.ok) { showUploadError('Erreur inattendue, réessayez.'); return; }

  const data = await res.json();
  state.token = data.session_token;
  state.expiresAt = data.expires_at;
  sessionStorage.setItem('gwToken', state.token);
  sessionStorage.setItem('gwExpiresAt', state.expiresAt);
  await enterApp();
}

async function deleteSession() {
  if (!state.token) return;
  try {
    await fetch(`/api/v1/sessions/${state.token}`, {
      method: 'DELETE',
      headers: { 'X-Session-Token': state.token },
    });
  } catch { /* ignore network errors on delete */ }
  clearSession();
}

function clearSession() {
  state.token = null;
  state.expiresAt = null;
  sessionStorage.removeItem('gwToken');
  sessionStorage.removeItem('gwExpiresAt');
  if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
  showLanding();
}

function handleExpiry() {
  clearSession();
  showLanding();
  showUploadError('Votre session a expiré. Rechargez votre fichier pour continuer.');
}

// ==================== VIEWS ====================
function showLanding() {
  document.getElementById('view-landing').style.display = '';
  document.getElementById('view-app').style.display = 'none';
}

function showApp() {
  document.getElementById('view-landing').style.display = 'none';
  document.getElementById('view-app').style.display = '';
}

function showUploadError(msg) {
  const el = document.getElementById('upload-error');
  el.textContent = msg;
  el.style.display = '';
}

function hideUploadError() {
  document.getElementById('upload-error').style.display = 'none';
}

// ==================== INIT ====================
async function enterApp() {
  showApp();
  await loadStats();
  startTimer();
  await loadPersons(1, '');
}

async function init() {
  wireUploadZone();
  wireQuit();
  wireTabs();
  wirePersonsTab();
  wireFamiliesTab();
  wireEventsTab();
  wireExportTab();
  buildEventTypeCheckboxes();

  if (state.token) {
    try {
      await enterApp();
    } catch {
      clearSession();
      showLanding();
    }
  } else {
    showLanding();
  }
}

window.addEventListener('DOMContentLoaded', init);

// ==================== UPLOAD ZONE ====================
function wireUploadZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const uploadBtn = document.getElementById('btn-upload');

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.background = 'var(--bg-active)';
  });
  dropZone.addEventListener('dragleave', () => {
    dropZone.style.background = '';
  });
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.background = '';
    const file = e.dataTransfer.files[0];
    if (file) { fileInput.files = e.dataTransfer.files; }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) {
      dropZone.querySelector('p').textContent = fileInput.files[0].name;
    }
  });

  uploadBtn.addEventListener('click', async () => {
    hideUploadError();
    const file = fileInput.files[0];
    if (!file) { showUploadError('Sélectionnez un fichier .gw.'); return; }
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Chargement…';
    await uploadFile(file);
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Charger et analyser';
  });
}

function wireQuit() {
  document.getElementById('btn-quit').addEventListener('click', async () => {
    await deleteSession();
  });
}

// ==================== NAVBAR ====================
async function loadStats() {
  const data = await apiJson('/api/v1/genealogy/stats');
  state.stats = data.data;
  document.getElementById('nav-stats').textContent =
    `${state.stats.total_persons} personnes · ${state.stats.total_families} familles`;
}

let _timerInterval = null;

function startTimer() {
  if (_timerInterval) clearInterval(_timerInterval);
  updateTimer();
  _timerInterval = setInterval(updateTimer, 30000);
}

function updateTimer() {
  if (!state.expiresAt) return;
  const remaining = Math.max(0, new Date(state.expiresAt) - Date.now());
  const h = Math.floor(remaining / 3600000);
  const m = Math.floor((remaining % 3600000) / 60000);
  document.getElementById('nav-timer').textContent =
    remaining > 0 ? `⏱ ${h > 0 ? h + 'h ' : ''}${m} min` : '⌛ Expiré';
}

// ==================== TABS ====================
function wireTabs() {
  document.querySelectorAll('.toldot-tab').forEach(tab => {
    tab.addEventListener('click', () => showTab(tab.dataset.tab));
  });
}

function showTab(name) {
  document.querySelectorAll('.toldot-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `panel-${name}`));
  if (name === 'families' && state.families.items.length === 0) loadFamilies(1);
  if (name === 'stats') renderStats();
}

// ==================== PERSONNES ====================
let _personsSeq = 0;
let _familiesSeq = 0;

function wirePersonsTab() {
  const searchInput = document.getElementById('persons-search');
  const searchBtn = document.getElementById('persons-search-btn');
  const clearBtn = document.getElementById('persons-clear-btn');
  const prevBtn = document.getElementById('persons-prev');
  const nextBtn = document.getElementById('persons-next');

  searchBtn.addEventListener('click', () => {
    loadPersons(1, searchInput.value.trim());
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loadPersons(1, searchInput.value.trim());
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    loadPersons(1, '');
  });

  prevBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    loadPersons(state.persons.page - 1, query);
  });

  nextBtn.addEventListener('click', () => {
    const query = searchInput.value.trim();
    loadPersons(state.persons.page + 1, query);
  });
}

async function loadPersons(page, query) {
  const seq = ++_personsSeq;
  let url = `/api/v1/persons?page=${page}&size=50`;
  if (query) url += `&query=${encodeURIComponent(query)}`;
  let data;
  try {
    data = await apiJson(url);
  } catch (err) {
    if (seq === _personsSeq) {
      document.getElementById('persons-list').innerHTML =
        '<p class="alert-toldot error">Impossible de charger les personnes.</p>';
    }
    throw err;
  }
  if (seq !== _personsSeq) return;
  state.persons.items = data.items;
  state.persons.page = data.pagination.page;
  state.persons.pages = data.pagination.pages;
  state.currentPersonId = null;
  renderPersons();
  updatePersonPagination(data.pagination);
}

function renderPersons() {
  const list = document.getElementById('persons-list');
  if (!state.persons.items.length) {
    list.innerHTML = '<p class="text-muted" style="font-style:italic;padding:0.5rem">Aucune personne trouvée.</p>';
    return;
  }
  list.innerHTML = state.persons.items.map(p => {
    const metaParts = [];
    if (p.birth_date) metaParts.push(`°${shortDate(p.birth_date)}`);
    if (p.death_date) metaParts.push(`†${shortDate(p.death_date)}`);
    const meta = metaParts.join(' · ');
    return `<div class="item-row">
      <span><span class="item-name"><strong>${escHtml(p.surname)}</strong>, ${escHtml(p.first_name)}</span> <span class="item-meta">${escHtml(meta)}</span></span>
      <button class="btn-see" data-id="${escHtml(p.id)}">Voir ›</button>
    </div>`;
  }).join('');
  list.querySelectorAll('.btn-see').forEach(btn => {
    btn.addEventListener('click', () => showPersonDetail(btn.dataset.id, btn));
  });
}

function updatePersonPagination(pagination) {
  document.getElementById('persons-prev').disabled = !pagination.has_prev;
  document.getElementById('persons-next').disabled = !pagination.has_next;
  document.getElementById('persons-page-info').textContent =
    `Page ${pagination.page} / ${pagination.pages} (${pagination.total} personnes)`;
}

// ==================== FICHE PERSONNE ====================
async function showPersonDetail(personId, btnEl) {
  const existing = document.getElementById('person-detail-panel');
  if (existing) {
    const wasForSamePerson = existing.dataset.personId === personId;
    existing.remove();
    if (wasForSamePerson) return;
  }

  state.currentPersonId = personId;

  let personResp, familiesResp;
  try {
    [personResp, familiesResp] = await Promise.all([
      apiJson('/api/v1/persons/' + encodeURIComponent(personId)),
      apiJson('/api/v1/persons/' + encodeURIComponent(personId) + '/families'),
    ]);
  } catch (err) {
    if (err.message === 'session-expired') return; // handled by apiFetch
    const row = btnEl ? btnEl.closest('.item-row') : null;
    const errPanel = document.createElement('div');
    errPanel.className = 'alert-toldot error';
    errPanel.textContent = 'Impossible de charger la fiche.';
    if (row) row.insertAdjacentElement('afterend', errPanel);
    else document.getElementById('persons-list').prepend(errPanel);
    return;
  }

  const person = personResp.data;
  const families = familiesResp.data || [];

  const parentIds = [];
  const childIds = [];

  for (const fam of families) {
    if (fam.husband_id === personId || fam.wife_id === personId) {
      // person is a parent in this family → collect children
      for (const cid of (fam.children || [])) {
        if (cid && cid !== personId) childIds.push(cid);
      }
    } else {
      // person is a child in this family → collect parents
      if (fam.husband_id && fam.husband_id !== personId) parentIds.push(fam.husband_id);
      if (fam.wife_id && fam.wife_id !== personId) parentIds.push(fam.wife_id);
    }
  }

  const uniqueParentIds = [...new Set(parentIds)];
  const uniqueChildIds = [...new Set(childIds)];
  const allIds = [...new Set([...uniqueParentIds, ...uniqueChildIds])];

  const nameMap = await resolvePersonNames(allIds);

  const parents = uniqueParentIds.map(id => ({ id, label: nameMap[id] || id }));
  const children = uniqueChildIds.map(id => ({ id, label: nameMap[id] || id }));

  const panel = buildPersonDetailPanel(person, parents, children);
  panel.dataset.personId = personId;

  const row = btnEl ? btnEl.closest('.item-row') : null;
  if (row) {
    row.insertAdjacentElement('afterend', panel);
  } else {
    document.getElementById('persons-list').prepend(panel);
  }

  panel.querySelectorAll('.mini-tree-person[data-id]').forEach(el => {
    el.addEventListener('click', () => showPersonDetail(el.dataset.id, null));
  });
}

async function resolvePersonNames(ids) {
  const map = {};
  // No batch endpoint available; one request per related person
  await Promise.all(ids.map(async id => {
    try {
      const r = await apiJson('/api/v1/persons/' + encodeURIComponent(id));
      const p = r.data;
      map[id] = (p.surname || '—') + ', ' + (p.first_name || '—');
    } catch { map[id] = id; }
  }));
  return map;
}

function buildPersonDetailPanel(person, parents, children) {
  const panel = document.createElement('div');
  panel.id = 'person-detail-panel';
  panel.className = 'person-detail';
  const fullName = escHtml((person.surname || '—') + ', ' + (person.first_name || '—'));

  const dateParts = [];
  if (person.birth_date) dateParts.push('°' + escHtml(shortDate(person.birth_date)));
  if (person.death_date) dateParts.push('†' + escHtml(shortDate(person.death_date)));
  const datesHtml = dateParts.length
    ? `<span style="color:var(--text-muted);font-size:0.85rem"> — ${dateParts.join(' · ')}</span>`
    : '';

  function renderPersonNodes(list) {
    if (!list.length) return '<span class="mini-tree-person placeholder">—</span>';
    return list.map(({ id, label }) =>
      `<a class="mini-tree-person" data-id="${escHtml(id)}">${escHtml(label)}</a>`
    ).join('');
  }

  panel.innerHTML = `
    <div>
      <strong>${fullName}</strong>${datesHtml}
    </div>
    <div class="mini-tree">
      <div class="mini-tree-col">
        <div class="mini-tree-label">Parents</div>
        ${renderPersonNodes(parents)}
      </div>
      <div class="mini-tree-arrow">→</div>
      <div class="mini-tree-col">
        <div class="mini-tree-label">Lui/Elle</div>
        <span class="mini-tree-person self">${escHtml(person.surname || '—')}</span>
      </div>
      <div class="mini-tree-arrow">→</div>
      <div class="mini-tree-col">
        <div class="mini-tree-label">Enfants</div>
        ${renderPersonNodes(children)}
      </div>
    </div>
  `;

  return panel;
}

// ==================== FAMILLES ====================
function wireFamiliesTab() {
  document.getElementById('families-prev').addEventListener('click', () => {
    loadFamilies(state.families.page - 1);
  });
  document.getElementById('families-next').addEventListener('click', () => {
    loadFamilies(state.families.page + 1);
  });
}

async function loadFamilies(page) {
  const seq = ++_familiesSeq;
  const url = `/api/v1/families?page=${page}&size=50`;
  let data;
  try {
    data = await apiJson(url);
  } catch (err) {
    if (seq === _familiesSeq) {
      document.getElementById('families-list').innerHTML =
        '<p class="alert-toldot error">Impossible de charger les familles.</p>';
    }
    throw err;
  }
  if (seq !== _familiesSeq) return;

  // Resolve spouse names
  const spouseIds = [...new Set(
    data.items.flatMap(f => [f.husband_id, f.wife_id].filter(Boolean))
  )];
  const nameMap = await resolvePersonNames(spouseIds);
  if (seq !== _familiesSeq) return; // check again after async name resolution

  state.families.items = data.items;
  state.families.nameMap = nameMap; // store for renderFamilies
  state.families.page = data.pagination.page;
  state.families.pages = data.pagination.pages;
  renderFamilies();
  updateFamiliesPagination(data.pagination);
}

function renderFamilies() {
  const list = document.getElementById('families-list');
  if (!state.families.items.length) {
    list.innerHTML = '<p class="text-muted" style="font-style:italic;padding:0.5rem">Aucune famille trouvée.</p>';
    return;
  }
  list.innerHTML = state.families.items.map(f => {
    const husband = f.husband_id
      ? escHtml(state.families.nameMap[f.husband_id] || f.husband_id)
      : '—';
    const wife = f.wife_id
      ? escHtml(state.families.nameMap[f.wife_id] || f.wife_id)
      : '—';
    const childCount = Array.isArray(f.children) ? f.children.length : 0;
    const metaParts = [`${childCount} enfant(s)`];
    if (f.marriage_date) metaParts.push(`⚭ ${escHtml(shortDate(f.marriage_date))}`);
    const meta = metaParts.join(' · ');
    return `<div class="item-row">
      <span><span class="item-name"><strong>${husband}</strong> &amp; <strong>${wife}</strong></span> <span class="item-meta">${meta}</span></span>
      <button class="btn-see" data-id="${escHtml(f.id)}">Voir ›</button>
    </div>`;
  }).join('');
  list.querySelectorAll('.btn-see').forEach(btn => {
    btn.addEventListener('click', () => showFamilyDetail(btn.dataset.id, btn));
  });
}

function updateFamiliesPagination(pagination) {
  document.getElementById('families-prev').disabled = !pagination.has_prev;
  document.getElementById('families-next').disabled = !pagination.has_next;
  document.getElementById('families-page-info').textContent =
    `Page ${pagination.page} / ${pagination.pages} (${pagination.total} familles)`;
}

async function showFamilyDetail(familyId, btnEl) {
  const existing = document.getElementById('family-detail-panel');
  if (existing) {
    const wasForSameFamily = existing.dataset.familyId === familyId;
    existing.remove();
    if (wasForSameFamily) return;
  }

  const row = btnEl ? btnEl.closest('.item-row') : null;

  let childrenResp;
  try {
    childrenResp = await apiJson('/api/v1/families/' + encodeURIComponent(familyId) + '/children');
  } catch (err) {
    if (err.message === 'session-expired') return;
    const errPanel = document.createElement('div');
    errPanel.className = 'alert-toldot error';
    errPanel.textContent = 'Impossible de charger les enfants.';
    if (row) row.insertAdjacentElement('afterend', errPanel);
    else document.getElementById('families-list').prepend(errPanel);
    return;
  }

  const children = childrenResp.data || [];

  const panel = document.createElement('div');
  panel.id = 'family-detail-panel';
  panel.className = 'person-detail';
  panel.dataset.familyId = familyId;

  let childrenHtml;
  if (children.length) {
    childrenHtml = children.map(child => {
      const label = escHtml((child.surname || '—') + ', ' + (child.first_name || '—'));
      return `<a class="mini-tree-person" data-id="${escHtml(child.id)}">${label}</a>`;
    }).join('');
  } else {
    childrenHtml = '<em style="color:var(--text-muted);font-size:0.85rem">Aucun enfant enregistré.</em>';
  }

  panel.innerHTML = `
    <div><strong>Enfants :</strong></div>
    <div>${childrenHtml}</div>
  `;

  panel.querySelectorAll('a.mini-tree-person[data-id]').forEach(el => {
    el.addEventListener('click', () => {
      showTab('persons');
      showPersonDetail(el.dataset.id, null);
    });
  });

  if (row) {
    row.insertAdjacentElement('afterend', panel);
  } else {
    document.getElementById('families-list').prepend(panel);
  }
}

// ==================== ÉVÉNEMENTS ====================
const EVENT_TYPES = [
  { value: 'birt', label: 'Naissance' },
  { value: 'deat', label: 'Décès' },
  { value: 'marr', label: 'Mariage' },
  { value: 'div',  label: 'Divorce' },
  { value: 'sep',  label: 'Séparation' },
  { value: 'bapt', label: 'Baptême' },
  { value: 'buri', label: 'Inhumation' },
  { value: 'enga', label: 'Fiançailles' },
  { value: 'pacs', label: 'PACS' },
  { value: 'oth',  label: 'Autre' },
];

function buildEventTypeCheckboxes() {
  const container = document.getElementById('evt-types');
  if (!container) return;
  container.innerHTML = EVENT_TYPES.map(t =>
    `<label><input type="checkbox" value="${escHtml(t.value)}" class="evt-type-cb"> ${escHtml(t.label)}</label>`
  ).join('');
}

function wireEventsTab() {
  const btn = document.getElementById('evt-search-btn');
  if (btn) btn.addEventListener('click', searchEvents);
}

async function searchEvents() {
  const day   = parseInt(document.getElementById('evt-day').value)   || null;
  const month = parseInt(document.getElementById('evt-month').value) || null;
  const year  = parseInt(document.getElementById('evt-year').value)  || null;
  const selectedTypes = [...document.querySelectorAll('.evt-type-cb:checked')].map(cb => cb.value);

  const list = document.getElementById('events-list');
  list.innerHTML = '<p style="color:var(--text-muted);font-style:italic">Recherche en cours…</p>';

  try {
    let items = await fetchAllEventItems(year, selectedTypes);
    if (month !== null) items = items.filter(e => extractMonth(e.date) === month);
    if (day   !== null) items = items.filter(e => extractDay(e.date)   === day);
    renderEvents(items);
  } catch (err) {
    if (err.message === 'session-expired') return;
    list.innerHTML = '<p class="alert-toldot error">Erreur lors de la recherche.</p>';
  }
}

async function fetchAllEventItems(year, selectedTypes) {
  const typesToFetch = selectedTypes.length > 0 ? selectedTypes : [null];
  const allItems = [];

  for (const type of typesToFetch) {
    let page = 1;
    while (true) {
      const params = new URLSearchParams({ page, size: 100 });
      if (year) { params.set('year_from', year); params.set('year_to', year); }
      if (type) params.set('event_type', type);
      const data = await apiJson('/api/v1/events?' + params);
      allItems.push(...data.items);
      if (!data.pagination.has_next) break;
      page++;
      if (page > 100) break; // safeguard against runaway loop
    }
  }

  // Deduplicate by id when multiple types were fetched
  if (selectedTypes.length > 1) {
    const seen = new Set();
    return allItems.filter(e => {
      if (seen.has(e.id)) return false;
      seen.add(e.id);
      return true;
    });
  }
  return allItems;
}

function renderEvents(items) {
  const list = document.getElementById('events-list');
  if (!items.length) {
    list.innerHTML = '<p class="text-muted" style="font-style:italic;padding:0.5rem">Aucun événement trouvé.</p>';
    return;
  }
  list.innerHTML = items.map(e => {
    const typeLabel = EVENT_TYPES.find(t => t.value === e.event_type)?.label || escHtml(e.event_type) || '?';
    const dateStr   = e.date ? escHtml(shortDate(e.date)) : '—';
    const placeHtml = e.place ? ` · ${escHtml(e.place)}` : '';
    const personBtn = e.person_id
      ? ` <button class="btn-see" data-id="${escHtml(e.person_id)}">Personne ›</button>`
      : '';
    return `<div class="item-row">
      <span><span class="item-name"><strong>${typeLabel}</strong></span> <span class="item-meta">${dateStr}${placeHtml}</span></span>
      ${personBtn}
    </div>`;
  }).join('');

  list.querySelectorAll('.btn-see[data-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      showTab('persons');
      showPersonDetail(btn.dataset.id, null);
    });
  });
}

function extractMonth(dateStr) {
  if (!dateStr) return null;
  const m = String(dateStr).match(/[-\/](\d{1,2})[-\/]/);
  return m ? parseInt(m[1]) : null;
}

function extractDay(dateStr) {
  if (!dateStr) return null;
  const m = String(dateStr).match(/[-\/]\d{1,2}[-\/](\d{1,2})/);
  return m ? parseInt(m[1]) : null;
}

// ==================== STATS ====================
function renderStats() {
  const container = document.getElementById('stats-content');
  if (!container) return;

  if (!state.stats) {
    container.innerHTML = '<p>Chargement…</p>';
    return;
  }

  const s = state.stats;

  const cards = [
    { value: s.total_persons,                                          label: 'Personnes' },
    { value: s.total_families,                                         label: 'Familles' },
    { value: s.total_events,                                           label: 'Événements' },
    { value: s.persons_with_birth_date || 0,                           label: 'Avec date de naissance' },
    { value: s.families_with_children || 0,                            label: 'Familles avec enfants' },
    { value: (s.average_children_per_family || 0).toFixed(1),          label: 'Enfants / famille (moy.)' },
  ];

  const gridHtml = `<div class="stats-grid">${
    cards.map(c =>
      `<div class="stat-card">
        <div class="stat-value">${escHtml(String(c.value))}</div>
        <div class="stat-label">${escHtml(c.label)}</div>
      </div>`
    ).join('')
  }</div>`;

  let tableHtml = '';
  const eventsByType = s.events_by_type;
  if (eventsByType && Object.keys(eventsByType).length > 0) {
    const rows = Object.entries(eventsByType).map(([key, count]) => {
      const typeEntry = EVENT_TYPES.find(t => t.value === key);
      const label = typeEntry ? typeEntry.label : escHtml(key);
      return `<tr><td>${label}</td><td>${escHtml(String(count))}</td></tr>`;
    }).join('');
    tableHtml = `
      <h3 style="color:var(--accent);margin-top:1.5rem">Événements par type</h3>
      <div style="max-width:400px">
        <table class="table table-sm">
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  container.innerHTML = gridHtml + tableHtml;
}

// ==================== EXPORT ====================
const EXPORT_EXT = { gedcom: 'ged', json: 'json', xml: 'xml' };

async function downloadExport(format) {
  const errorEl = document.getElementById('export-error');
  errorEl.style.display = 'none';
  try {
    const res = await apiFetch('/api/v1/genealogy/export/' + format);
    if (!res.ok) {
      errorEl.textContent = "Erreur lors de la génération de l'export.";
      errorEl.style.display = '';
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'genealogie.' + EXPORT_EXT[format];
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    if (err.message === 'session-expired') return;
    errorEl.textContent = 'Erreur lors du téléchargement.';
    errorEl.style.display = '';
  }
}

function wireExportTab() {
  document.getElementById('btn-export-gedcom').addEventListener('click', () => downloadExport('gedcom'));
  document.getElementById('btn-export-json').addEventListener('click', () => downloadExport('json'));
  document.getElementById('btn-export-xml').addEventListener('click', () => downloadExport('xml'));
}
