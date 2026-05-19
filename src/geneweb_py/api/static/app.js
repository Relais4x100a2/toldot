'use strict';

// ==================== STATE ====================
const state = {
  token: sessionStorage.getItem('gwToken') || null,
  expiresAt: sessionStorage.getItem('gwExpiresAt') || null,
  stats: null,
  persons: { items: [], page: 1, pages: 1 },
  families: { items: [], page: 1, pages: 1 },
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

// ==================== STUBS (implemented in later tasks) ====================
async function loadPersons(_page, _query) {}
function wirePersonsTab() {}
function wireFamiliesTab() {}
function wireEventsTab() {}
function wireExportTab() {}
function buildEventTypeCheckboxes() {}
