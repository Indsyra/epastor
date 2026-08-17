# ePastor

Plateforme permettant à tout pasteur/serviteur/église de rendre son
contenu YouTube interrogeable en langage naturel — avec réponses sourcées
(vidéo + timestamp) et renvoi vers son catalogue de livres quand pertinent.

> 📄 Voir [`docs/SPECS.md`](docs/SPECS.md) pour la vision complète et
> [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) pour le schéma de données.

## Statut du projet

🚧 **En phase de spécification.** Le modèle de données et les specs v1
sont validés. Le code est encore minimal (script de découverte vidéo
uniquement). Rien n'est en production.

## Concept en une phrase

Un moteur unique (découverte de vidéos → transcription → indexation
vectorielle → réponse sourcée par IA), réutilisable pour n'importe quel
pasteur, avec deux façons d'y accéder :

- **Widget intégré** à un site d'église existant (une instance fixe)
- **App ePastor générale**, où le visiteur choisit ses pasteurs préférés
  et reçoit aussi des suggestions de pasteurs "associés"

## Structure du repo

```
epastor/
├── docs/            specs et modèle de données (source de vérité du projet)
├── db/              modèles ORM + migrations (base multi-tenant, un pasteur = un tenant)
├── ingestion/        découverte vidéos → transcription → chunking/embeddings
├── catalog/          gestion du catalogue de livres par pasteur
├── agent/             LangGraph : retrieval → réponse sourcée → enrichissement livres
├── api/               FastAPI (routes opérateur / visiteur / widget)
├── web/                interfaces (formulaire opérateur, chatbot visiteur)
├── config.py           paramètres techniques globaux (pas la liste des pasteurs — voir db/)
└── tests/
```

## Principe clé : multi-tenant dès la v1

Un pasteur = un `tenant_id`. Toutes les données (vidéos, chunks, livres)
sont dans une base unique, filtrées par pasteur — pas une base séparée
par pasteur. Ce choix est documenté dans `docs/SPECS.md` §3.

## Cas de test de référence

Le développement est validé sur le cas de Mohammed Sanogo (double chaîne
YouTube — personnelle + église, avec filtrage par intervenant nécessaire
sur la seconde — et catalogue de livres externe), car c'est le cas le
plus complexe couvert par les specs. Une fois validé dessus, le même
moteur doit fonctionner pour un pasteur avec une seule chaîne et aucun
catalogue, sans changement de code.

## Ce qui est fait / à faire

- [x] Specs v1 (`docs/SPECS.md`)
- [x] Modèle de données (`docs/DATA_MODEL.md`)
- [x] User stories v1, avec technos/output/process par story (`docs/USER_STORIES.md`)
- [x] Script de découverte vidéo, version fichier (`ingestion/discover_videos.py`)
      — encore basé sur `config.py` en dur, doit migrer vers la base
- [x] Script de création automatique des issues GitHub à partir des US
      (`scripts/create_github_issues.py`)
- [ ] **US-01 — Modèles ORM (`db/models.py`) — en cours**
  - [x] `Base` (`db/base.py`)
  - [x] Modèle `Pastor` (id, display_name, church_name, created_at, status
        en `Enum` natif avec `create_constraint=True`) — testé (insertion,
        contrainte enum, valeurs par défaut)
  - [x] Modèle `Channel` (id, pastor_id en clé étrangère, youtube_url,
        youtube_channel_id, requires_speaker_filter, name_keywords en
        `JSON`, last_scanned_at) — testé en bout en bout (insertion,
        relecture depuis une nouvelle session, contrainte de clé étrangère
        vérifiée, `PRAGMA foreign_keys=ON` requis sous SQLite)
  - [ ] Modèle `Video`
  - [ ] Modèle `TranscriptChunk`
  - [ ] Modèle `Book`
  - [ ] Modèle `Visitor`
  - [ ] Modèle `VisitorPastorFollow`
  - [ ] `db/session.py` (connexion, avec le `PRAGMA foreign_keys=ON` pour SQLite)
  - [ ] Migration Alembic initiale
- [ ] US-02 — Script de seed (créer un pasteur/chaîne en base)
- [ ] Migration de la découverte vers la base (US-03/04/05)
- [ ] Transcription (`ingestion/fetch_transcripts.py`)
- [ ] Chunking + embeddings (`ingestion/chunk_and_embed.py`)
- [ ] Agent LangGraph (retrieval + réponse + extraction livres)
- [ ] API FastAPI
- [ ] Formulaire opérateur
- [ ] Interface chatbot visiteur

**Environnement de dev actuel** : SQLite (fichier local, zéro install) pour
apprendre et itérer vite. Migration vers PostgreSQL prévue avant tout
déploiement réel (voir `docs/USER_STORIES.md` US-01) — le code SQLAlchemy
reste quasi identique entre les deux, seule la chaîne de connexion change.

## Hors périmètre v1

Voir `docs/SPECS.md` §6 — notamment : pas de texte intégral de livres
(droits d'auteur), pas d'authentification/paiement, pas de calcul de
recommandation par co-occurrence (structure prévue, algorithme en v2).

## Setup local (à date)

```bash
pip install yt-dlp
python -m ingestion.discover_videos --dry-run
```

Nécessite de renseigner les chaînes cibles dans `config.py` pour l'instant
(migration vers un formulaire prévue — voir "Ce qui est fait / à faire").
