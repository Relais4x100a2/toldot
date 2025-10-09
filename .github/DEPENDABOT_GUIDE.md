# Guide Dependabot - geneweb-py

## 🤖 Qu'est-ce que Dependabot ?

Dependabot est un bot GitHub qui :
- ✅ Surveille vos dépendances
- ✅ Détecte les mises à jour disponibles
- ✅ Crée automatiquement des Pull Requests
- ✅ Vérifie que tout fonctionne (via vos tests)

## 📋 Types de PR Dependabot

### 1. Dépendances Python (pip)
**Exemple** : "Bump pytest from 7.0.0 to 7.4.0"

**Ce qui est mis à jour** :
- Fichier `pyproject.toml`
- Dépendances listées dans `[project.dependencies]`
- Ou `[project.optional-dependencies]`

### 2. GitHub Actions
**Exemple** : "Bump actions/checkout from v3 to v4"

**Ce qui est mis à jour** :
- Fichiers `.github/workflows/*.yml`
- Versions des actions utilisées

## ✅ Comment Gérer une PR Dependabot

### Étape 1 : Ouvrir la PR
1. GitHub > Pull requests
2. Cliquer sur la PR Dependabot

### Étape 2 : Vérifier les Checks
⏳ **Attendre 5-10 minutes** que les checks se terminent

✅ **Si tout est VERT** :
- Tests passent
- Couverture ≥84%
- Linting OK
→ **Vous pouvez merger en toute sécurité**

❌ **Si quelque chose est ROUGE** :
- Cliquer sur "Details" pour voir l'erreur
- Lire les logs
- Décider si c'est bloquant

### Étape 3 : Lire les Changements
Cliquer sur "Files changed" :
- Voir exactement ce qui change
- Généralement juste une version de package

### Étape 4 : Merger ou Fermer

**Pour MERGER** :
```
1. Bouton "Merge pull request"
2. Confirmer
3. Optionnel : "Delete branch" (recommandé)
```

**Pour FERMER** :
```
1. Bouton "Close pull request"
2. Ajouter un commentaire expliquant pourquoi
```

## 🎯 Cas d'Usage Fréquents

### PR "Bump pytest from X to Y"
✅ **Action recommandée** : Merger si checks verts

**Pourquoi** : pytest est votre framework de test, maintenir à jour est important

### PR "Bump actions/checkout from v3 to v4"
✅ **Action recommandée** : Merger si checks verts

**Pourquoi** : Améliorations de performance GitHub Actions

### PR avec patch de sécurité
🔴 **Action urgente** : Merger IMMÉDIATEMENT si checks verts

**Pourquoi** : Corrige une faille de sécurité

### PR qui casse les tests
❌ **Action** : 
1. Commenter : "@dependabot ignore this major version"
2. Fermer la PR
3. Investiguer pourquoi ça casse

## 🛠️ Commandes Dependabot

Vous pouvez commander Dependabot en commentant la PR :

| Commande | Action |
|----------|--------|
| `@dependabot merge` | Merge automatiquement si checks verts |
| `@dependabot recreate` | Recrée la PR à neuf |
| `@dependabot rebase` | Rebase la PR sur main |
| `@dependabot ignore this dependency` | Ignore cette dépendance |
| `@dependabot ignore this major version` | Ignore cette version majeure |
| `@dependabot close` | Ferme la PR |

## ⚙️ Configuration Actuelle

Dans `.github/dependabot.yml` :

```yaml
# Dépendances Python
- Fréquence : Hebdomadaire (lundis 9h)
- Max PR ouvertes : 5
- Labels : dependencies, python

# GitHub Actions  
- Fréquence : Hebdomadaire (lundis 9h)
- Max PR ouvertes : 3
- Labels : dependencies, github-actions
```

## 🔧 Modifier la Configuration

### Changer la Fréquence

Éditer `.github/dependabot.yml` :

```yaml
schedule:
  interval: "daily"     # Ou "weekly", "monthly"
  day: "monday"         # Jour de la semaine
  time: "09:00"         # Heure (UTC)
```

### Limiter les PR

```yaml
open-pull-requests-limit: 3  # Max 3 PR ouvertes
```

### Désactiver Dependabot

Supprimer ou renommer :
```bash
mv .github/dependabot.yml .github/dependabot.yml.disabled
```

## 📊 Workflow Type

### Lundi Matin
1. Dependabot crée 0-5 PR
2. Attendre que les checks passent
3. Merger celles qui sont vertes ✅
4. Investiguer celles qui sont rouges ❌

**Temps** : 5-10 minutes par semaine

### Sécurité Critique
Si Dependabot crée une PR avec label "security" :
→ **Priorité maximale**, merger dès que possible

## ✅ Checklist PR Dependabot

Avant de merger :

- [ ] Tous les checks sont verts ✅
- [ ] Couverture ≥84%
- [ ] Lire le changelog (dans la description PR)
- [ ] Vérifier les "Files changed" (normalement 1-2 fichiers)
- [ ] Pas de breaking changes majeurs

Si tout est OK → **Merger !**

## 🎯 Avantages

1. **Sécurité** : Corrections de failles automatiques
2. **Modernité** : Toujours à jour
3. **Qualité** : Vérifié par vos tests
4. **Gain de temps** : Automatique

## ⚠️ Quand NE PAS Merger

- ❌ Checks rouges (tests échouent)
- ❌ Couverture baisse significativement
- ❌ Breaking changes non documentés
- ❌ Version majeure sans review

## 💡 Bonnes Pratiques

1. **Merger régulièrement** : Ne pas accumuler les PR
2. **Lire les changelogs** : Comprendre ce qui change
3. **Tester localement** si doute : `git pull origin dependabot/...`
4. **Grouper si possible** : Dependabot peut grouper les updates

---

## 🚀 Action Immédiate Recommandée

**Pour les 3 PR actuelles** :

1. Aller sur https://github.com/Relais4x100a2/geneweb-py/pulls
2. Pour chaque PR :
   - Vérifier que les checks sont verts ✅
   - Lire rapidement les changements
   - Cliquer "Merge pull request"
3. Voilà ! 🎉

**Temps total** : 2-3 minutes

Les mises à jour Dependabot sont généralement **sûres et bénéfiques**. Si vos tests passent, vous pouvez merger en confiance !

