# Design : Token de session éphémère — Privacy by Design

**Date :** 2026-05-18
**Statut :** Approuvé

---

## Contexte

L'API geneweb-py doit pouvoir être hébergée sur un serveur web public personnel sans conserver aucune donnée généalogique côté serveur. Les données des utilisateurs (fichiers `.gw`) sont sensibles (données personnelles et familiales) et ne doivent jamais être persistées sur disque ni loguées.

L'architecture actuelle utilise un singleton `GenealogyService` global partagé entre tous les appels — incompatible avec un usage multi-utilisateurs et contraire au principe de privacy by design.

---

## Objectifs

- Zéro donnée persistée sur disque après le parsing
- Isolation complète entre sessions utilisateurs
- Nettoyage garanti des données en mémoire à l'expiration
- Déploiement configurable : mode lecture seule (serveur public) ou mode complet (CRUD)
- Résistance aux abus sur un serveur public (rate limiting + cap de sessions)

---

## Architecture générale

```
Client
  │
  ├── POST /api/v1/sessions              ← upload du fichier .gw
  │     → parse en mémoire
  │     → fichier tmp supprimé immédiatement
  │     → stocke Genealogy dans SessionStore
  │     → retourne { session_token, expires_at, stats }
  │
  ├── GET /api/v1/persons               ← header X-Session-Token requis
  ├── GET /api/v1/families              ← lecture seule ou CRUD selon mode
  ├── GET /api/v1/events
  ├── GET /api/v1/genealogy/stats
  ├── GET /api/v1/genealogy/export/{format}
  ├── GET /api/v1/genealogy/search
  │
  ├── POST/PUT/DELETE /api/v1/persons   ← 405 si READ_ONLY=true
  ├── POST/PUT/DELETE /api/v1/families  ← 405 si READ_ONLY=true
  ├── POST/PUT/DELETE /api/v1/events    ← 405 si READ_ONLY=true
  │
  └── DELETE /api/v1/sessions/{token}  ← suppression explicite (privacy)

SessionStore (app.state)
  ├── dict { token → SessionEntry(genealogy, expires_at, created_at) }
  ├── cap : MAX_SESSIONS (env var SESSION_MAX_SESSIONS, défaut 10)
  └── TTL : SESSION_TTL_SECONDS (défaut 3600 = 1 heure, sliding window)

Tâche asyncio de fond
  └── toutes les 5 minutes → purge des sessions expirées
```

---

## Composants

### `api/session_store.py` (nouveau)

```python
@dataclass
class SessionEntry:
    genealogy: Genealogy
    expires_at: datetime
    created_at: datetime

class SessionStore:
    # Configurable via env vars
    MAX_SESSIONS: int   # SESSION_MAX_SESSIONS, défaut 10
    TTL_SECONDS: int    # SESSION_TTL_SECONDS, défaut 3600

    def create(self, genealogy: Genealogy) -> str
    def get(self, token: str) -> Genealogy | None   # sliding window TTL
    def delete(self, token: str) -> bool
    def cleanup_expired(self) -> int
    def count_active(self) -> int
    def is_full(self) -> bool
```

- **Token** : `secrets.token_urlsafe(32)` — 256 bits d'entropie
- **TTL sliding window** : `get()` repousse `expires_at` à chaque appel
- **Concurrence** : `asyncio.Lock` sur toutes les mutations
- **Cap** : `create()` lève `SessionFullError` si `is_full()` → HTTP 503

### `api/routers/sessions.py` (nouveau)

```
POST   /api/v1/sessions
  - Rate limit : 5/heure/IP
  - Vérifie cap → 503
  - Valide extension (.gw / .gwplus) et MIME
  - Vérifie taille ≤ MAX_UPLOAD_BYTES
  - Parse en mémoire via GeneWebParser (fichier tmp supprimé après parsing)
  - Efface source_file dans GenealogyMetadata
  - Stocke dans SessionStore
  - Retourne : { session_token, expires_at, stats: { persons, families } }
  - Headers : Cache-Control: no-store

DELETE /api/v1/sessions/{token}
  - Pas de rate limit (encourager la suppression)
  - 204 si supprimé, 404 si inconnu/expiré
```

### `api/dependencies.py` (modifié)

Nouvelle dépendance remplaçant `get_genealogy_service()` :

```python
def get_session_genealogy(
    x_session_token: str = Header(...),
    store: SessionStore = Depends(get_store),
) -> Genealogy:
    genealogy = store.get(x_session_token)
    if genealogy is None:
        raise HTTPException(401, "Session inconnue ou expirée")
    return genealogy
```

Nouvelle dépendance pour le mode lecture seule :

```python
def require_write_mode() -> None:
    if settings.READ_ONLY:
        raise HTTPException(405, "API en mode lecture seule")
```

Tous les endpoints POST/PUT/DELETE personnes, familles, événements reçoivent
`dependencies=[Depends(require_write_mode)]`.

### `api/main.py` (modifié)

- Suppression du singleton `_genealogy_service` et de `get_global_genealogy_service()`
- Ajout du lifespan FastAPI :

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    store = SessionStore()
    app.state.session_store = store
    task = asyncio.create_task(cleanup_loop(store))
    yield
    task.cancel()
    # store abandonné au GC — aucune donnée persistée
```

- `cleanup_loop` : `asyncio.sleep(300)` puis `store.cleanup_expired()`

### Mode de déploiement (`READ_ONLY`)

Variable d'environnement `READ_ONLY` (défaut `false`) :

| Valeur | Comportement |
|--------|-------------|
| `true` | POST/PUT/DELETE personnes/familles/événements → 405 |
| `false` | CRUD complet actif, mutations sur la `Genealogy` de la session |

En mode CRUD, les mutations s'appliquent à la `Genealogy` en mémoire de la session. Chaque session est isolée — aucune mutation ne croise les sessions.

---

## Mesures Privacy by Design

| Mesure | Détail |
|--------|--------|
| Aucun fichier conservé | Fichier tmp supprimé par `os.unlink()` immédiatement après parsing |
| Aucune donnée loguée | Middleware de logging exclut `X-Session-Token` et le contenu généalogique |
| `source_file = None` | Effacé dans `GenealogyMetadata` avant stockage en session |
| Headers de réponse | `Cache-Control: no-store` sur `/sessions` et tous les endpoints de données |
| Suppression explicite | `DELETE /sessions/{token}` documenté et accessible sans rate limit |
| Arrêt propre | Lifespan annule la tâche de fond, store abandonné — pas de sérialisation disque |
| Token opaque | `secrets.token_urlsafe(32)` — non prévisible, non corrélable |

---

## Gestion des erreurs

| Situation | HTTP | Message |
|-----------|------|---------|
| Cap de sessions atteint | 503 | "Serveur saturé, réessayez plus tard" |
| Token inconnu ou expiré | 401 | "Session inconnue ou expirée" |
| Header `X-Session-Token` absent | 422 | (FastAPI automatique) |
| Fichier trop volumineux | 413 | (déjà en place) |
| Extension/MIME invalide | 400/415 | (déjà en place) |
| Rate limit dépassé | 429 | (slowapi, déjà en place) |
| Mode READ_ONLY + mutation | 405 | "API en mode lecture seule" |

Aucun message d'erreur ne référence de données généalogiques.

---

## Stratégie de tests

### Unitaires (`tests/unit/`)
- `SessionStore` : create, get, delete, cleanup_expired
- TTL sliding window : accès repousse l'expiration
- Cap MAX_SESSIONS : N+1ème create → SessionFullError
- Concurrence : accès simultanés thread-safe

### Intégration (`tests/integration/`)
- Flux complet : upload `.gw` → token → GET persons → DELETE session
- Session expirée : requête après TTL → 401
- Cap atteint : N+1 uploads → 503
- Mode `READ_ONLY=true` : POST person → 405
- Mode `READ_ONLY=false` : POST person → 201
- Token absent : GET sans header → 422
- Suppression explicite : DELETE session → 204, accès suivant → 401

La fixture `tests/fixtures/simple_test.gw` est réutilisée pour tous les tests de session.

---

## Ce qui est conservé

- `GenealogyService` : la classe est conservée mais n'est **plus un singleton**. En mode CRUD (`READ_ONLY=false`), elle est instanciée par session et wrappée autour de la `Genealogy` de la session pour exposer les méthodes CRUD existantes. Les routers CRUD reçoivent une instance `GenealogyService` construite à partir de la `Genealogy` résolue par `get_session_genealogy()`.

---

## Ce qui disparaît

- `GenealogyService` singleton global (`main.py`)
- `get_global_genealogy_service()` et `get_genealogy_service()` (remplacés par `get_session_genealogy()`)
- `validate_genealogy_loaded()` (remplacée par la résolution de token)
- Endpoint `DELETE /api/v1/genealogy/` (clear global — n'a plus de sens)
- Chargement automatique de `simple_test.gw` au démarrage

---

## Variables d'environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `READ_ONLY` | `false` | Mode lecture seule |
| `SESSION_MAX_SESSIONS` | `10` | Nombre max de sessions simultanées |
| `SESSION_TTL_SECONDS` | `3600` | Durée de vie de session (sliding window) |
| `MAX_UPLOAD_BYTES` | (existant) | Taille max du fichier uploadé |
| `CORS_ALLOW_ORIGINS` | (existant) | Origines CORS autorisées |
