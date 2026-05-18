# geneweb-py.toldot.fr Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter une interface web publique (SPA Vanilla JS + Bootstrap, thème héritage) à l'API geneweb-py existante, servie par FastAPI depuis le même conteneur CapRover.

**Architecture:** FastAPI sert à la fois l'API REST (`/api/v1/`) et les fichiers statiques du front (`/`) via `StaticFiles`. Le front stocke le token de session dans `sessionStorage`, interroge l'API avec l'en-tête `X-Session-Token`, et offre 5 onglets : Personnes, Familles, Événements, Stats, Export.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Bootstrap 5.3 (local), Vanilla JS (ES2022), Docker, CapRover.

---

## File Structure

```
Dockerfile                                         ← nouveau
captain-definition                                 ← nouveau
src/geneweb_py/api/
  main.py                                          ← modifié (StaticFiles + CSP)
  static/
    index.html                                     ← nouveau
    style.css                                      ← nouveau
    app.js                                         ← nouveau
    vendor/
      bootstrap.min.css                            ← téléchargé
      bootstrap.bundle.min.js                      ← téléchargé
```

---

## API Shape Reference

Les tâches JS utilisent ces endpoints existants (tous requièrent `X-Session-Token`) :

| Endpoint | Paramètres clés | Réponse |
|----------|----------------|---------|
| `POST /api/v1/sessions` | multipart `file` | `{session_token, expires_at, stats:{persons,families}}` |
| `DELETE /api/v1/sessions/{token}` | — | 204 |
| `GET /api/v1/genealogy/stats` | — | `SuccessResponse.data` = stats complets |
| `GET /api/v1/persons` | `page`, `size`, `query` | `PaginatedResponse {items, pagination}` |
| `GET /api/v1/persons/{id}` | — | `SuccessResponse.data` = person |
| `GET /api/v1/persons/{id}/families` | — | `SuccessResponse.data` = tableau de familles |
| `GET /api/v1/families` | `page`, `size` | `PaginatedResponse {items, pagination}` |
| `GET /api/v1/families/{id}/children` | — | `SuccessResponse.data` = tableau de personnes |
| `GET /api/v1/events` | `page`, `size`, `event_type`, `year_from`, `year_to` | `PaginatedResponse` |
| `GET /api/v1/genealogy/export/{format}` | format = `gedcom`/`json`/`xml` | fichier binaire |

**Person fields :** `id`, `first_name`, `surname`, `birth_date`, `birth_place`, `death_date`, `death_place`, `sex`, `families`, `related_families`

**Family fields :** `id`, `husband_id`, `wife_id`, `children` (list of person IDs), `marriage_date`, `marriage_place`, `divorce_date`

**Pagination :** `pagination.page`, `pagination.pages`, `pagination.has_next`, `pagination.has_prev`, `pagination.total`

---

## Task 1 : Dockerfile + captain-definition

**Files:**
- Create: `Dockerfile`
- Create: `captain-definition`

- [ ] **Step 1 : Créer le Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[api]"
EXPOSE 8000
CMD ["uvicorn", "geneweb_py.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2 : Créer captain-definition**

```json
{
  "schemaVersion": 2,
  "dockerfilePath": "./Dockerfile"
}
```

- [ ] **Step 3 : Tester le build Docker**

```bash
docker build -t geneweb-py-test .
```

Expected : build complète sans erreur, image créée.

- [ ] **Step 4 : Vérifier que le conteneur démarre**

```bash
docker run --rm -p 8001:8000 -e READ_ONLY=true geneweb-py-test &
sleep 3
curl http://localhost:8001/health
kill %1
```

Expected : `{"status":"healthy","message":"GeneWeb-py API is running","version":"0.1.0"}`

- [ ] **Step 5 : Commit**

```bash
git add Dockerfile captain-definition
git commit -m "feat(deploy): ajouter Dockerfile et captain-definition pour CapRover"
```

---

## Task 2 : StaticFiles mount + mise à jour CSP dans main.py

**Files:**
- Modify: `src/geneweb_py/api/main.py`
- Create: `src/geneweb_py/api/static/index.html` (minimal, pour que le test passe)

- [ ] **Step 1 : Écrire le test qui échoue**

Dans `tests/api/test_main.py`, ajouter :

```python
def test_root_serves_html(client):
    """GET / doit servir index.html (text/html), pas du JSON."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
```

- [ ] **Step 2 : Vérifier que le test échoue**

```bash
pytest tests/api/test_main.py::test_root_serves_html -v
```

Expected : FAIL — `200` mais `content-type: application/json`.

- [ ] **Step 3 : Créer le dossier static et un index.html minimal**

```bash
mkdir -p src/geneweb_py/api/static
```

Créer `src/geneweb_py/api/static/index.html` :

```html
<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Toldot · GeneWeb-py</title></head>
<body><h1>Toldot</h1></body>
</html>
```

- [ ] **Step 4 : Modifier main.py — supprimer la route JSON `/` et monter StaticFiles**

Dans `src/geneweb_py/api/main.py` :

1. Ajouter l'import en tête de fichier, après les imports existants :

```python
from fastapi.staticfiles import StaticFiles
import pathlib
```

2. Dans la fonction `create_app()`, **supprimer** le bloc suivant (route JSON racine) :

```python
    @application.get("/")
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "message": "Bienvenue sur l'API GeneWeb-py",
                "version": "0.1.0",
                "documentation": "/docs",
                "redoc": "/redoc",
            }
        )
```

3. Mettre à jour le middleware CSP — remplacer le bloc `if`/`else` existant sur les CSP par :

```python
        _docs_paths = {"/docs", "/redoc", "/openapi.json"}
        if request.url.path in _docs_paths:
            csp = (
                "default-src 'self'; "
                "script-src 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src data: fastapi.tiangolo.com; "
                "connect-src 'self' cdn.jsdelivr.net"
            )
        elif request.url.path.startswith("/api/v1/"):
            csp = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        else:
            # Front-end statique
            csp = (
                "default-src 'self'; "
                "img-src 'self' data:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'"
            )
```

4. À la **fin** de `create_app()`, juste avant `return application`, ajouter le mount StaticFiles :

```python
    _static_dir = pathlib.Path(__file__).parent / "static"
    if _static_dir.exists():
        application.mount(
            "/",
            StaticFiles(directory=str(_static_dir), html=True),
            name="static",
        )

    return application
```

- [ ] **Step 5 : Vérifier que le test passe**

```bash
pytest tests/api/test_main.py::test_root_serves_html -v
```

Expected : PASS

- [ ] **Step 6 : Vérifier que les tests existants passent toujours**

```bash
pytest tests/api/test_main.py -v
```

Expected : tous les tests PASS.

- [ ] **Step 7 : Commit**

```bash
git add src/geneweb_py/api/main.py src/geneweb_py/api/static/index.html
git commit -m "feat(api): monter StaticFiles à / et mettre à jour le CSP pour le front"
```

---

## Task 3 : index.html complet + style.css + Bootstrap local

**Files:**
- Modify: `src/geneweb_py/api/static/index.html`
- Create: `src/geneweb_py/api/static/style.css`
- Create: `src/geneweb_py/api/static/vendor/bootstrap.min.css`
- Create: `src/geneweb_py/api/static/vendor/bootstrap.bundle.min.js`

- [ ] **Step 1 : Télécharger Bootstrap 5.3 localement**

```bash
mkdir -p src/geneweb_py/api/static/vendor
curl -L "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" \
  -o src/geneweb_py/api/static/vendor/bootstrap.min.css
curl -L "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" \
  -o src/geneweb_py/api/static/vendor/bootstrap.bundle.min.js
```

Expected : deux fichiers créés (bootstrap.min.css ~230KB, bootstrap.bundle.min.js ~75KB).

- [ ] **Step 2 : Créer style.css — thème héritage/patrimoine**

Créer `src/geneweb_py/api/static/style.css` :

```css
/* === Palette héritage === */
:root {
  --bg: #fdf6ec;
  --bg-card: #fef9f0;
  --bg-active: #fef0d0;
  --accent: #8b6914;
  --accent-light: #c8a96e;
  --text: #2c1810;
  --text-muted: #5a3e28;
  --border: #e8d5b0;
  --danger: #c0392b;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: Georgia, 'Times New Roman', serif;
  min-height: 100vh;
}

/* Navbar */
.toldot-nav {
  background: var(--bg);
  border-bottom: 2px solid var(--accent);
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.toldot-nav .brand {
  font-size: 1.2rem;
  font-weight: bold;
  color: var(--accent);
  text-decoration: none;
}
.toldot-nav .nav-stats {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.toldot-nav .timer {
  background: var(--bg-active);
  color: var(--accent);
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
}
.btn-quit {
  font-size: 0.8rem;
  color: var(--danger);
  border: 1px solid var(--danger);
  background: none;
  border-radius: 4px;
  padding: 2px 10px;
  cursor: pointer;
}
.btn-quit:hover { background: var(--danger); color: #fff; }

/* Landing */
#view-landing {
  max-width: 640px;
  margin: 3rem auto;
  padding: 1rem;
  text-align: center;
}
#view-landing h1 { color: var(--accent); font-size: 1.6rem; }
#view-landing .lead { color: var(--text-muted); font-style: italic; font-size: 0.95rem; }
.upload-zone {
  border: 2px dashed var(--accent);
  border-radius: 8px;
  padding: 2rem;
  background: var(--bg-card);
  cursor: pointer;
  margin: 1.5rem 0;
  transition: background 0.2s;
}
.upload-zone:hover { background: var(--bg-active); }
.upload-zone .icon { font-size: 2.5rem; }
.btn-primary-toldot {
  background: var(--accent);
  color: var(--bg);
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1.5rem;
  font-family: Georgia, serif;
  font-size: 1rem;
  cursor: pointer;
}
.btn-primary-toldot:hover { background: var(--text); }
.assurance-list {
  list-style: none;
  padding: 0;
  margin: 1.5rem 0 0;
  text-align: left;
  font-size: 0.88rem;
  color: var(--text-muted);
}
.assurance-list li::before { content: "✓ "; color: var(--accent); font-weight: bold; }

/* Tabs */
.toldot-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
  padding: 0 1rem;
}
.toldot-tab {
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.toldot-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: bold;
}

/* Content panels */
.tab-panel { display: none; padding: 1rem; }
.tab-panel.active { display: block; }

/* Person / Family cards */
.item-row {
  border-left: 3px solid var(--accent-light);
  padding: 0.4rem 0.75rem;
  margin-bottom: 4px;
  background: var(--bg-card);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}
.item-row:nth-child(even) { background: #fff; }
.item-row .item-name { color: var(--text); }
.item-row .item-meta { color: var(--text-muted); font-size: 0.82rem; }
.btn-see {
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  font-family: Georgia, serif;
}
.btn-see:hover { text-decoration: underline; }

/* Person detail / mini-tree */
.person-detail {
  border: 1px solid var(--accent-light);
  border-radius: 6px;
  padding: 1rem;
  margin-top: 0.5rem;
  background: var(--bg-active);
}
.mini-tree {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}
.mini-tree-col { text-align: center; }
.mini-tree-label { font-size: 0.72rem; color: var(--accent); margin-bottom: 4px; }
.mini-tree-person {
  display: block;
  background: #fff;
  border: 1px solid var(--accent-light);
  border-radius: 3px;
  padding: 2px 8px;
  font-size: 0.78rem;
  margin: 2px 0;
  cursor: pointer;
  color: var(--text);
  text-decoration: none;
}
.mini-tree-person:hover { background: var(--accent); color: #fff; }
.mini-tree-person.self {
  background: var(--accent);
  color: var(--bg);
  cursor: default;
}
.mini-tree-arrow { color: var(--accent-light); font-size: 1.2rem; }

/* Search bar */
.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.search-bar input {
  flex: 1;
  border: 1px solid var(--accent-light);
  border-radius: 4px;
  padding: 0.35rem 0.6rem;
  font-family: Georgia, serif;
  background: var(--bg-card);
  color: var(--text);
}
.search-bar button {
  background: var(--accent);
  color: var(--bg);
  border: none;
  border-radius: 4px;
  padding: 0.35rem 0.8rem;
  cursor: pointer;
  font-family: Georgia, serif;
}

/* Pagination */
.pagination-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}
.pagination-bar button {
  background: none;
  border: 1px solid var(--accent-light);
  border-radius: 3px;
  padding: 2px 10px;
  cursor: pointer;
  color: var(--accent);
  font-family: Georgia, serif;
}
.pagination-bar button:disabled { opacity: 0.4; cursor: default; }

/* Events filters */
.event-filters {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}
.event-filters label {
  font-size: 0.85rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 2px;
}
.event-filters input[type="number"] {
  width: 80px;
  border: 1px solid var(--accent-light);
  border-radius: 3px;
  padding: 3px 6px;
  background: var(--bg);
  color: var(--text);
  font-family: Georgia, serif;
}
.event-type-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.event-type-checkboxes label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: var(--text);
  cursor: pointer;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
  text-align: center;
}
.stat-card .stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--accent);
}
.stat-card .stat-label {
  font-size: 0.82rem;
  color: var(--text-muted);
}

/* Export */
.export-btns {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 320px;
}
.btn-export {
  background: var(--bg-card);
  border: 2px solid var(--accent);
  border-radius: 6px;
  padding: 0.6rem 1rem;
  font-family: Georgia, serif;
  font-size: 1rem;
  color: var(--accent);
  cursor: pointer;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.btn-export:hover { background: var(--accent); color: var(--bg); }

/* Alert / message */
.alert-toldot {
  border-radius: 6px;
  padding: 0.6rem 1rem;
  margin: 0.5rem 0;
  font-size: 0.88rem;
}
.alert-toldot.error { background: #fde8e8; color: var(--danger); border: 1px solid #f5b5b5; }
.alert-toldot.info { background: var(--bg-active); color: var(--text-muted); border: 1px solid var(--accent-light); }

/* Footer */
.toldot-footer {
  text-align: center;
  font-size: 0.78rem;
  color: var(--text-muted);
  padding: 2rem 1rem 1rem;
  border-top: 1px solid var(--border);
  margin-top: 3rem;
}
```

- [ ] **Step 3 : Créer index.html — SPA shell complet**

Créer `src/geneweb_py/api/static/index.html` :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Toldot · GeneWeb-py</title>
  <link rel="stylesheet" href="/vendor/bootstrap.min.css">
  <link rel="stylesheet" href="/style.css">
</head>
<body>

<!-- ==================== LANDING ==================== -->
<div id="view-landing">
  <h1>Toldot · GeneWeb-py</h1>
  <p class="lead">Explorez votre fichier généalogique — aucune donnée conservée sur le serveur</p>

  <div class="upload-zone" id="drop-zone">
    <div class="icon">📂</div>
    <p class="mb-1">Glissez un fichier <strong>.gw</strong> ici</p>
    <p class="text-muted" style="font-size:0.85rem">ou cliquez pour parcourir</p>
    <input type="file" id="file-input" accept=".gw,.gwplus" style="display:none">
  </div>

  <button class="btn-primary-toldot" id="btn-upload">Charger et analyser</button>

  <div id="upload-error" class="alert-toldot error" style="display:none"></div>

  <ul class="assurance-list mt-4">
    <li>Parsing en mémoire — fichier supprimé immédiatement après chargement</li>
    <li>Session d'1 heure · Export GEDCOM · JSON · XML</li>
    <li>Code source libre — <a href="https://github.com/Relais4x100a2/geneweb-py" target="_blank" rel="noopener" style="color:var(--accent)">GitHub</a></li>
  </ul>

  <footer class="toldot-footer">
    Site non professionnel au sens de l'article 6 III 2° de la loi 2004-575. Aucune donnée personnelle collectée.
  </footer>
</div>

<!-- ==================== APP ==================== -->
<div id="view-app" style="display:none">

  <!-- Navbar -->
  <nav class="toldot-nav">
    <span class="brand">Toldot · GeneWeb-py</span>
    <span class="nav-stats" id="nav-stats"></span>
    <span style="flex:1"></span>
    <span class="timer" id="nav-timer"></span>
    <button class="btn-quit" id="btn-quit">Quitter la session</button>
  </nav>

  <!-- Tabs -->
  <div class="toldot-tabs">
    <div class="toldot-tab active" data-tab="persons">Personnes</div>
    <div class="toldot-tab" data-tab="families">Familles</div>
    <div class="toldot-tab" data-tab="events">Événements</div>
    <div class="toldot-tab" data-tab="stats">Stats</div>
    <div class="toldot-tab" data-tab="export">Export</div>
  </div>

  <div class="container-fluid py-3">

    <!-- === PERSONNES === -->
    <div id="panel-persons" class="tab-panel active">
      <div class="search-bar">
        <input type="text" id="persons-search" placeholder="Rechercher un nom…">
        <button id="persons-search-btn">Chercher</button>
        <button id="persons-clear-btn" style="background:none;border:1px solid var(--accent-light);border-radius:4px;padding:0.35rem 0.6rem;cursor:pointer;color:var(--text-muted)">✕</button>
      </div>
      <div id="persons-list"></div>
      <div class="pagination-bar">
        <button id="persons-prev" disabled>← Précédent</button>
        <span id="persons-page-info"></span>
        <button id="persons-next" disabled>Suivant →</button>
      </div>
    </div>

    <!-- === FAMILLES === -->
    <div id="panel-families" class="tab-panel">
      <div id="families-list"></div>
      <div class="pagination-bar">
        <button id="families-prev" disabled>← Précédent</button>
        <span id="families-page-info"></span>
        <button id="families-next" disabled>Suivant →</button>
      </div>
    </div>

    <!-- === ÉVÉNEMENTS === -->
    <div id="panel-events" class="tab-panel">
      <div class="event-filters">
        <div class="row g-2 mb-2">
          <div class="col-auto">
            <label>Jour</label>
            <input type="number" id="evt-day" min="1" max="31" placeholder="1-31">
          </div>
          <div class="col-auto">
            <label>Mois</label>
            <input type="number" id="evt-month" min="1" max="12" placeholder="1-12">
          </div>
          <div class="col-auto">
            <label>Année</label>
            <input type="number" id="evt-year" min="1000" max="3000" placeholder="ex. 1914">
          </div>
        </div>
        <div>
          <label>Types (cumulatifs)</label>
          <div class="event-type-checkboxes" id="evt-types"></div>
        </div>
        <div class="mt-2">
          <button class="btn-primary-toldot" style="font-size:0.9rem;padding:0.4rem 1.2rem" id="evt-search-btn">Rechercher</button>
        </div>
      </div>
      <div id="events-list"></div>
    </div>

    <!-- === STATS === -->
    <div id="panel-stats" class="tab-panel">
      <div id="stats-content"></div>
    </div>

    <!-- === EXPORT === -->
    <div id="panel-export" class="tab-panel">
      <p style="color:var(--text-muted);font-style:italic;margin-bottom:1.5rem">
        Les fichiers sont générés à la volée depuis vos données de session — aucune copie conservée.
      </p>
      <div class="export-btns">
        <button class="btn-export" id="btn-export-gedcom">📄 Télécharger en GEDCOM</button>
        <button class="btn-export" id="btn-export-json">{ } Télécharger en JSON</button>
        <button class="btn-export" id="btn-export-xml">🗂 Télécharger en XML</button>
      </div>
      <div id="export-error" class="alert-toldot error mt-2" style="display:none"></div>
    </div>

  </div>
</div>

<script src="/vendor/bootstrap.bundle.min.js"></script>
<script src="/app.js"></script>
</body>
</html>
```

- [ ] **Step 4 : Vérifier visuellement**

```bash
python run_api.py --reload
```

Ouvrir `http://localhost:8000` → la landing page doit s'afficher avec le thème sépia.

- [ ] **Step 5 : Commit**

```bash
git add src/geneweb_py/api/static/
git commit -m "feat(front): ajouter index.html, style.css et Bootstrap local"
```

---

## Task 4 : app.js — upload + gestion de session

**Files:**
- Create: `src/geneweb_py/api/static/app.js`

- [ ] **Step 1 : Créer app.js — state global + helpers API**

Créer `src/geneweb_py/api/static/app.js` :

```javascript
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
  try { await fetch(`/api/v1/sessions/${state.token}`, { method: 'DELETE', headers: { 'X-Session-Token': state.token } }); } catch { /* ignore */ }
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
    // Reprendre une session existante (rechargement de page)
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
```

- [ ] **Step 2 : Ajouter le câblage de la zone d'upload**

Ajouter à la suite de `app.js` :

```javascript
// ==================== UPLOAD ZONE ====================
function wireUploadZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const uploadBtn = document.getElementById('btn-upload');

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.background = 'var(--bg-active)'; });
  dropZone.addEventListener('dragleave', () => { dropZone.style.background = ''; });
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
```

- [ ] **Step 3 : Tester l'upload manuellement**

```bash
python run_api.py --reload
```

Ouvrir `http://localhost:8000`, glisser `tests/fixtures/simple_test.gw` → la vue app doit apparaître (navbar visible, onglets visibles).

- [ ] **Step 4 : Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): upload .gw, gestion session, bascule landing/app"
```

---

## Task 5 : app.js — navbar + timer + onglets

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

- [ ] **Step 1 : Ajouter loadStats, timer et câblage onglets**

Ajouter à la suite de `app.js` :

```javascript
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
```

- [ ] **Step 2 : Vérifier manuellement**

Recharger `http://localhost:8000`, uploader `tests/fixtures/simple_test.gw`. Vérifier :
- La navbar affiche "N personnes · M familles"
- Le timer affiche "⏱ 59 min" (approximativement)
- Cliquer sur "Quitter la session" → retour landing
- Les onglets changent de panel au clic

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): navbar avec stats, timer de session, navigation par onglets"
```

---

## Task 6 : app.js — onglet Personnes (liste + pagination + recherche)

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

- [ ] **Step 1 : Ajouter loadPersons, renderPersons et câblage**

Ajouter à la suite de `app.js` :

```javascript
// ==================== PERSONNES ====================
function wirePersonsTab() {
  document.getElementById('persons-search-btn').addEventListener('click', () => {
    const q = document.getElementById('persons-search').value.trim();
    loadPersons(1, q);
  });
  document.getElementById('persons-search').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('persons-search-btn').click();
  });
  document.getElementById('persons-clear-btn').addEventListener('click', () => {
    document.getElementById('persons-search').value = '';
    loadPersons(1, '');
  });
  document.getElementById('persons-prev').addEventListener('click', () => {
    const q = document.getElementById('persons-search').value.trim();
    loadPersons(state.persons.page - 1, q);
  });
  document.getElementById('persons-next').addEventListener('click', () => {
    const q = document.getElementById('persons-search').value.trim();
    loadPersons(state.persons.page + 1, q);
  });
}

async function loadPersons(page, query) {
  const params = new URLSearchParams({ page, size: 50 });
  if (query) params.set('query', query);
  const data = await apiJson(`/api/v1/persons?${params}`);
  state.persons.items = data.items;
  state.persons.page = data.pagination.page;
  state.persons.pages = data.pagination.pages;
  state.currentPersonId = null;
  renderPersons();
  updatePersonPagination(data.pagination);
}

function renderPersons() {
  const list = document.getElementById('persons-list');
  if (state.persons.items.length === 0) {
    list.innerHTML = '<p class="text-muted" style="font-style:italic;padding:0.5rem">Aucune personne trouvée.</p>';
    return;
  }
  list.innerHTML = state.persons.items.map(p => {
    const name = `<strong>${escHtml(p.surname || '—')}</strong>, ${escHtml(p.first_name || '—')}`;
    const meta = [
      p.birth_date ? `°${shortDate(p.birth_date)}` : '',
      p.birth_place ? p.birth_place : '',
      p.death_date ? `†${shortDate(p.death_date)}` : '',
    ].filter(Boolean).join(' · ');
    return `<div class="item-row">
      <span><span class="item-name">${name}</span> <span class="item-meta">${escHtml(meta)}</span></span>
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
```

- [ ] **Step 2 : Vérifier manuellement**

Uploader `tests/fixtures/simple_test.gw`. Onglet Personnes :
- La liste s'affiche avec noms, dates
- La pagination est fonctionnelle (ou désactivée si toutes les personnes tiennent en une page)
- La recherche par nom fonctionne

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): onglet Personnes avec liste paginée et recherche"
```

---

## Task 7 : app.js — fiche personne + mini-arbre

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

Le mini-arbre affiche : Parents → Personne → Enfants. Les parents viennent des familles où la personne est enfant (`related_families`), les enfants des familles où elle est parent (`families`).

- [ ] **Step 1 : Ajouter showPersonDetail et renderMiniTree**

Ajouter à la suite de `app.js` :

```javascript
// ==================== FICHE PERSONNE ====================
async function showPersonDetail(personId, btnEl) {
  // Fermer le détail ouvert si c'est la même personne
  const existing = document.getElementById('person-detail-panel');
  if (existing) {
    const wasOpen = existing.dataset.personId === personId;
    existing.remove();
    if (wasOpen) { state.currentPersonId = null; return; }
  }

  state.currentPersonId = personId;

  // Récupérer la personne et ses familles
  const [personResp, familiesResp] = await Promise.all([
    apiJson(`/api/v1/persons/${encodeURIComponent(personId)}`),
    apiJson(`/api/v1/persons/${encodeURIComponent(personId)}/families`),
  ]);
  const person = personResp.data;
  const families = familiesResp.data || [];

  // Construire l'arbre
  const parents = [];
  const children = [];

  for (const fam of families) {
    const isParent = fam.husband_id === personId || fam.wife_id === personId;
    if (isParent) {
      // Personne est parent → les children de la famille sont ses enfants
      (fam.children || []).forEach(childId => {
        if (childId !== personId) children.push({ id: childId, label: childId });
      });
    } else {
      // Personne est enfant → les parents de la famille sont ses parents
      if (fam.husband_id && fam.husband_id !== personId) parents.push({ id: fam.husband_id, label: fam.husband_id });
      if (fam.wife_id && fam.wife_id !== personId) parents.push({ id: fam.wife_id, label: fam.wife_id });
    }
  }

  // Résoudre les noms des parents et enfants
  const allIds = [...new Set([...parents.map(p => p.id), ...children.map(c => c.id)])];
  const nameMap = await resolvePersonNames(allIds);
  parents.forEach(p => { p.label = nameMap[p.id] || p.id; });
  children.forEach(c => { c.label = nameMap[c.id] || c.id; });

  const selfName = `${person.surname || '—'}, ${person.first_name || '—'}`;
  const panel = buildPersonDetailPanel(person, selfName, parents, children);
  panel.dataset.personId = personId;

  // Insérer le panneau après la ligne cliquée
  const row = btnEl.closest('.item-row');
  row.insertAdjacentElement('afterend', panel);

  // Rendre les noms dans l'arbre cliquables
  panel.querySelectorAll('.mini-tree-person[data-id]').forEach(el => {
    el.addEventListener('click', () => {
      const btn = document.createElement('button');
      btn.className = 'btn-see';
      btn.dataset.id = el.dataset.id;
      showPersonDetail(el.dataset.id, btn.closest('.item-row') || row);
    });
  });
}

async function resolvePersonNames(ids) {
  const map = {};
  await Promise.all(ids.map(async id => {
    try {
      const r = await apiJson(`/api/v1/persons/${encodeURIComponent(id)}`);
      const p = r.data;
      map[id] = `${p.surname || '—'}, ${p.first_name || '—'}`;
    } catch { map[id] = id; }
  }));
  return map;
}

function buildPersonDetailPanel(person, selfName, parents, children) {
  const panel = document.createElement('div');
  panel.id = 'person-detail-panel';
  panel.className = 'person-detail';

  const dates = [
    person.birth_date ? `°${shortDate(person.birth_date)}` : '',
    person.death_date ? `†${shortDate(person.death_date)}` : '',
  ].filter(Boolean).join(' · ');

  const parentsHtml = parents.length
    ? parents.map(p => `<a class="mini-tree-person" data-id="${escHtml(p.id)}" title="${escHtml(p.id)}">${escHtml(p.label)}</a>`).join('')
    : '<span class="mini-tree-person" style="opacity:0.4;cursor:default">—</span>';

  const childrenHtml = children.length
    ? children.map(c => `<a class="mini-tree-person" data-id="${escHtml(c.id)}" title="${escHtml(c.id)}">${escHtml(c.label)}</a>`).join('')
    : '<span class="mini-tree-person" style="opacity:0.4;cursor:default">—</span>';

  panel.innerHTML = `
    <div><strong>${escHtml(selfName)}</strong>${dates ? ' <span style="color:var(--text-muted);font-size:0.85rem">— ' + escHtml(dates) + '</span>' : ''}</div>
    <div class="mini-tree">
      <div class="mini-tree-col">
        <div class="mini-tree-label">Parents</div>
        ${parentsHtml}
      </div>
      <div class="mini-tree-arrow">→</div>
      <div class="mini-tree-col">
        <div class="mini-tree-label">Lui/Elle</div>
        <span class="mini-tree-person self">${escHtml(selfName.split(',')[0] || '?')}</span>
      </div>
      <div class="mini-tree-arrow">→</div>
      <div class="mini-tree-col">
        <div class="mini-tree-label">Enfants</div>
        ${childrenHtml}
      </div>
    </div>`;
  return panel;
}
```

- [ ] **Step 2 : Vérifier manuellement**

Uploader `tests/fixtures/test_relations.gw` (le plus riche en relations). Cliquer "Voir ›" sur une personne → le panneau de détail doit apparaître avec le mini-arbre parents/enfants. Cliquer à nouveau sur "Voir ›" → le panneau se ferme.

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): fiche personne avec mini-arbre parents/enfants"
```

---

## Task 8 : app.js — onglet Familles

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

- [ ] **Step 1 : Ajouter loadFamilies, renderFamilies et showFamilyDetail**

Ajouter à la suite de `app.js` :

```javascript
// ==================== FAMILLES ====================
function wireFamiliesTab() {
  document.getElementById('families-prev').addEventListener('click', () => loadFamilies(state.families.page - 1));
  document.getElementById('families-next').addEventListener('click', () => loadFamilies(state.families.page + 1));
}

async function loadFamilies(page) {
  const params = new URLSearchParams({ page, size: 50 });
  const data = await apiJson(`/api/v1/families?${params}`);
  state.families.items = data.items;
  state.families.page = data.pagination.page;
  state.families.pages = data.pagination.pages;
  renderFamilies();
  updateFamiliesPagination(data.pagination);
}

function renderFamilies() {
  const list = document.getElementById('families-list');
  if (state.families.items.length === 0) {
    list.innerHTML = '<p class="text-muted" style="font-style:italic;padding:0.5rem">Aucune famille trouvée.</p>';
    return;
  }
  list.innerHTML = state.families.items.map(f => {
    const husband = f.husband_id ? escHtml(f.husband_id) : '—';
    const wife = f.wife_id ? escHtml(f.wife_id) : '—';
    const childCount = (f.children || []).length;
    const date = f.marriage_date ? ` · ⚭ ${shortDate(f.marriage_date)}` : '';
    return `<div class="item-row">
      <span>
        <span class="item-name">${husband} &amp; ${wife}</span>
        <span class="item-meta">${childCount} enfant(s)${escHtml(date)}</span>
      </span>
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
    const wasOpen = existing.dataset.familyId === familyId;
    existing.remove();
    if (wasOpen) return;
  }

  const childrenResp = await apiJson(`/api/v1/families/${encodeURIComponent(familyId)}/children`);
  const children = childrenResp.data || [];

  const panel = document.createElement('div');
  panel.id = 'family-detail-panel';
  panel.className = 'person-detail';
  panel.dataset.familyId = familyId;

  const childrenHtml = children.length
    ? children.map(c => {
        const name = `${c.surname || '—'}, ${c.first_name || '—'}`;
        return `<a class="mini-tree-person" data-id="${escHtml(c.id)}">${escHtml(name)}</a>`;
      }).join('')
    : '<em style="color:var(--text-muted);font-size:0.85rem">Aucun enfant enregistré.</em>';

  panel.innerHTML = `<div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.5rem">Enfants :</div>${childrenHtml}`;

  // Clic sur enfant → ouvre la fiche personne (onglet Personnes)
  panel.querySelectorAll('.mini-tree-person[data-id]').forEach(el => {
    el.addEventListener('click', () => {
      showTab('persons');
      // Chercher la personne dans la liste actuelle
      const existing = document.querySelector(`.btn-see[data-id="${CSS.escape(el.dataset.id)}"]`);
      if (existing) showPersonDetail(el.dataset.id, existing);
    });
  });

  btnEl.closest('.item-row').insertAdjacentElement('afterend', panel);
}
```

- [ ] **Step 2 : Vérifier manuellement**

Uploader `tests/fixtures/simple_family.gw`. Onglet Familles : les familles s'affichent. Cliquer "Voir ›" → les enfants apparaissent.

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): onglet Familles avec liste paginée et détail enfants"
```

---

## Task 9 : app.js — onglet Événements

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

**Note sur les filtres :** L'API `GET /api/v1/events` supporte `year_from`, `year_to` et `event_type` (valeur unique). Pour les types cumulatifs, on fait une requête par type et on fusionne. Pour le filtre jour/mois, on récupère les événements côté serveur avec le filtre année, puis on filtre côté client par mois/jour.

- [ ] **Step 1 : Définir les types d'événements et construire les checkboxes**

Ajouter à la suite de `app.js` :

```javascript
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
  container.innerHTML = EVENT_TYPES.map(t =>
    `<label><input type="checkbox" value="${t.value}" class="evt-type-cb"> ${escHtml(t.label)}</label>`
  ).join('');
}

function wireEventsTab() {
  document.getElementById('evt-search-btn').addEventListener('click', searchEvents);
}

async function searchEvents() {
  const day = parseInt(document.getElementById('evt-day').value) || null;
  const month = parseInt(document.getElementById('evt-month').value) || null;
  const year = parseInt(document.getElementById('evt-year').value) || null;
  const selectedTypes = [...document.querySelectorAll('.evt-type-cb:checked')].map(cb => cb.value);

  const list = document.getElementById('events-list');
  list.innerHTML = '<p style="color:var(--text-muted);font-style:italic">Recherche en cours…</p>';

  try {
    let items = await fetchAllEventItems(year, selectedTypes);

    // Filtre client-side mois / jour
    if (month !== null) items = items.filter(e => extractMonth(e.date) === month);
    if (day !== null)   items = items.filter(e => extractDay(e.date) === day);

    renderEvents(items);
  } catch (err) {
    if (err.message !== 'session-expired') {
      list.innerHTML = '<p class="alert-toldot error">Erreur lors de la recherche.</p>';
    }
  }
}

async function fetchAllEventItems(year, selectedTypes) {
  const base = new URLSearchParams({ size: 100 });
  if (year) { base.set('year_from', year); base.set('year_to', year); }

  const typesToFetch = selectedTypes.length > 0 ? selectedTypes : [null];
  const allItems = [];

  for (const type of typesToFetch) {
    const params = new URLSearchParams(base);
    if (type) params.set('event_type', type);
    let page = 1;
    while (true) {
      params.set('page', page);
      const data = await apiJson(`/api/v1/events?${params}`);
      allItems.push(...data.items);
      if (!data.pagination.has_next) break;
      page++;
    }
  }

  // Dédoublonner par event_id si multiple types
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
  if (items.length === 0) {
    list.innerHTML = '<p class="text-muted" style="font-style:italic;padding:0.5rem">Aucun événement trouvé.</p>';
    return;
  }
  list.innerHTML = items.map(e => {
    const typeLabel = EVENT_TYPES.find(t => t.value === e.event_type)?.label || e.event_type || '?';
    const date = e.date ? shortDate(e.date) : '—';
    const place = e.place ? ` · ${escHtml(e.place)}` : '';
    const personId = e.person_id || null;
    return `<div class="item-row">
      <span>
        <span class="item-name">${escHtml(typeLabel)}</span>
        <span class="item-meta"> ${escHtml(date)}${escHtml(place)}</span>
      </span>
      ${personId ? `<button class="btn-see" data-id="${escHtml(personId)}">Personne ›</button>` : ''}
    </div>`;
  }).join('');
  list.querySelectorAll('.btn-see[data-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      showTab('persons');
      // Charger la personne directement si pas dans la liste
      apiJson(`/api/v1/persons/${encodeURIComponent(btn.dataset.id)}`).then(resp => {
        const p = resp.data;
        // Ajouter une entrée temporaire si absente
        let row = document.querySelector(`.btn-see[data-id="${CSS.escape(p.id)}"]`);
        if (!row) {
          const tmpRow = document.createElement('div');
          tmpRow.className = 'item-row';
          tmpRow.innerHTML = `<span class="item-name"><strong>${escHtml(p.surname || '—')}</strong>, ${escHtml(p.first_name || '—')}</span><button class="btn-see" data-id="${escHtml(p.id)}">Voir ›</button>`;
          document.getElementById('persons-list').prepend(tmpRow);
          row = tmpRow.querySelector('.btn-see');
          row.addEventListener('click', () => showPersonDetail(row.dataset.id, row));
        }
        showPersonDetail(p.id, row);
      }).catch(() => {});
    });
  });
}

// Helpers date : extraire mois et jour d'une chaîne de date
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
```

- [ ] **Step 2 : Vérifier manuellement**

Uploader `tests/fixtures/test_complete.gw`. Onglet Événements :
- Cocher "Naissance" + "Décès" → cliquer Rechercher → la liste s'affiche
- Mettre "1" dans Mois → les résultats sont filtrés sur janvier
- Cliquer "Personne ›" → bascule sur l'onglet Personnes avec la fiche ouverte

- [ ] **Step 3 : Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): onglet Événements avec filtres date et types cumulatifs"
```

---

## Task 10 : app.js — onglets Stats + Export + utilitaires

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

- [ ] **Step 1 : Ajouter renderStats**

Ajouter à la suite de `app.js` :

```javascript
// ==================== STATS ====================
function renderStats() {
  const s = state.stats;
  if (!s) { document.getElementById('stats-content').innerHTML = '<p>Chargement…</p>'; return; }

  const byType = s.events_by_type || {};
  const typeRows = Object.entries(byType).map(([k, v]) => {
    const label = EVENT_TYPES.find(t => t.value === k)?.label || k;
    return `<tr><td>${escHtml(label)}</td><td>${v}</td></tr>`;
  }).join('');

  document.getElementById('stats-content').innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${s.total_persons}</div><div class="stat-label">Personnes</div></div>
      <div class="stat-card"><div class="stat-value">${s.total_families}</div><div class="stat-label">Familles</div></div>
      <div class="stat-card"><div class="stat-value">${s.total_events}</div><div class="stat-label">Événements</div></div>
      <div class="stat-card"><div class="stat-value">${s.persons_with_birth_date || 0}</div><div class="stat-label">Avec date de naissance</div></div>
      <div class="stat-card"><div class="stat-value">${s.families_with_children || 0}</div><div class="stat-label">Familles avec enfants</div></div>
      <div class="stat-card"><div class="stat-value">${(s.average_children_per_family || 0).toFixed(1)}</div><div class="stat-label">Enfants / famille (moy.)</div></div>
    </div>
    ${typeRows ? `<h3 style="color:var(--accent);font-size:1rem;margin-bottom:0.5rem">Événements par type</h3>
    <table class="table table-sm" style="max-width:400px"><tbody>${typeRows}</tbody></table>` : ''}`;
}
```

- [ ] **Step 2 : Ajouter wireExportTab + downloadExport**

```javascript
// ==================== EXPORT ====================
function wireExportTab() {
  document.getElementById('btn-export-gedcom').addEventListener('click', () => downloadExport('gedcom'));
  document.getElementById('btn-export-json').addEventListener('click', () => downloadExport('json'));
  document.getElementById('btn-export-xml').addEventListener('click', () => downloadExport('xml'));
}

const EXPORT_EXT = { gedcom: 'ged', json: 'json', xml: 'xml' };

async function downloadExport(format) {
  const errorEl = document.getElementById('export-error');
  errorEl.style.display = 'none';
  try {
    const res = await apiFetch(`/api/v1/genealogy/export/${format}`);
    if (!res.ok) { errorEl.textContent = 'Erreur lors de la génération de l\'export.'; errorEl.style.display = ''; return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `genealogie.${EXPORT_EXT[format]}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    if (err.message !== 'session-expired') {
      errorEl.textContent = 'Erreur lors du téléchargement.';
      errorEl.style.display = '';
    }
  }
}
```

- [ ] **Step 3 : Ajouter les utilitaires (escHtml, shortDate)**

```javascript
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
  // Extraire l'année si la chaîne est ISO ou GeneWeb
  const m = String(dateStr).match(/(\d{4})/);
  return m ? m[1] : String(dateStr);
}
```

- [ ] **Step 4 : Vérifier l'export manuellement**

Uploader `tests/fixtures/simple_test.gw`. Onglet Export → cliquer "Télécharger en JSON" → un fichier `genealogie.json` se télécharge. Vérifier que le JSON contient des données.

Répéter pour GEDCOM et XML.

- [ ] **Step 5 : Vérifier les Stats**

Onglet Stats → les 6 cartes s'affichent avec les bonnes valeurs.

- [ ] **Step 6 : Lancer la suite de tests complète**

```bash
pytest --tb=short -q
```

Expected : tous les tests passent (pas de régression sur l'API).

- [ ] **Step 7 : Commit final**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(front): onglets Stats, Export (GEDCOM/JSON/XML) et utilitaires JS"
```

---

## Self-Review du plan

**Spec coverage :**
- ✅ Architecture (FastAPI + StaticFiles, un seul conteneur) → Task 1 + 2
- ✅ Style héritage/patrimoine → Task 3
- ✅ Landing : upload, erreurs 413/400/415/503 → Task 4
- ✅ Session : sessionStorage, timer, quitter, 401 → Task 4 + 5
- ✅ Onglet Personnes : liste paginée, recherche → Task 6
- ✅ Fiche personne + mini-arbre parents/enfants → Task 7
- ✅ Onglet Familles : liste + détail enfants → Task 8
- ✅ Onglet Événements : filtres jour/mois/année + types cumulatifs → Task 9
- ✅ Onglet Stats : 6 cartes + tableau par type → Task 10
- ✅ Onglet Export : GEDCOM/JSON/XML via fetch+blob → Task 10
- ✅ CapRover : Dockerfile + captain-definition → Task 1
- ✅ CSP mise à jour pour le front statique → Task 2

**Placeholders :** Aucun.

**Cohérence des types :** `state.persons.items`, `state.families.items` utilisés de façon cohérente dans toutes les tâches. `apiFetch`/`apiJson` définis en Task 4 et utilisés partout. `escHtml`/`shortDate` définis en Task 10, référencés depuis Task 6, 7, 8, 9 → ⚠️ L'implémenteur doit ajouter ces fonctions dès Task 6 ou les stub-er. **Correction :** les utilitaires (`escHtml`, `shortDate`) sont définis en Task 10 Step 3, mais utilisés dès Task 6. L'implémenteur doit ajouter les deux fonctions à la fin de `app.js` dès la Task 6 (avant les tâches qui les utilisent), ou les ajouter dès le Step 1 de la Task 4. 

**Fix inline :** Dans Task 4 Step 1, ajouter en haut de la section `UTILITAIRES` les deux helpers directement :

```javascript
// Ajouter dès Task 4 Step 1, à la fin du bloc STATE / HELPERS
function escHtml(str) {
  if (str == null) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function shortDate(dateStr) {
  if (!dateStr) return '';
  const m = String(dateStr).match(/(\d{4})/);
  return m ? m[1] : String(dateStr);
}
```

(Task 10 Step 3 les re-déclare — l'implémenteur les consolidera à cet endroit et supprimera la version de Task 4.)
