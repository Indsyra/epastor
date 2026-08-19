# ePastor

Plateforme permettant à tout pasteur/serviteur/église de rendre son
contenu YouTube interrogeable en langage naturel — avec réponses sourcées
(vidéo + timestamp) et renvoi vers son catalogue de livres quand pertinent.

> 📄 Voir [`docs/SPECS.md`](docs/SPECS.md) pour la vision complète et
> [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) pour le schéma de données.
>
> 🇬🇧 English version (reference): [`README.md`](README.md)

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
      (`scripts/create_github_issues.py`), avec synchronisation et
      sous-tâches générées depuis la section Process de chaque US
- [x] **US-01 — Modèles ORM + migrations — terminée**
  - [x] `Base` (`db/base.py`)
  - [x] Modèle `Pastor` (id, display_name, church_name, created_at, status
        en `Enum` natif avec `create_constraint=True`)
  - [x] Modèle `Channel` (id, pastor_id en clé étrangère, youtube_url,
        youtube_channel_id, requires_speaker_filter, name_keywords en
        `JSON`, last_scanned_at)
  - [x] Modèle `Video` (id = id YouTube en `String(11)`, pas un UUID ;
        channel_id + pastor_id dénormalisés, transcript_status en `Enum`)
  - [x] Modèle `TranscriptChunk` (text en `Text`, start/end_seconds en
        `Float` ; `embedding` volontairement absent — vit dans FAISS,
        relié par `id`, pas en base)
  - [x] Modèle `Book` (catalogue par pasteur)
  - [x] Modèle `Visitor`
  - [x] Modèle `VisitorPastorFollow` (clé primaire composite
        visitor_id + pastor_id, sans id technique séparé)
  - [x] `db/session.py` (engine, `PRAGMA foreign_keys=ON` pour SQLite,
        `SessionLocal` factory, lecture de `DATABASE_URL`)
  - [x] Alembic configuré (`alembic.ini`, `db/migrations/env.py`) et
        migration initiale générée + appliquée — voir détail ci-dessous
- [ ] US-02 — Script de seed (créer un pasteur/chaîne en base)
- [ ] Migration de la découverte vers la base (US-03/04/05)
- [ ] Transcription (`ingestion/fetch_transcripts.py`)
- [ ] Chunking + embeddings (`ingestion/chunk_and_embed.py`)
- [ ] Agent LangGraph (retrieval + réponse + extraction livres)
- [ ] API FastAPI
- [ ] Formulaire opérateur
- [ ] Interface chatbot visiteur
- [ ] Epic G — orchestration, ingestion incrémentale, qualité des
      données, monitoring (voir `docs/USER_STORIES.md` US-21 à US-24)

**Environnement de dev actuel** : SQLite (fichier local, zéro install) pour
apprendre et itérer vite. Migration vers PostgreSQL prévue avant tout
déploiement réel (voir `docs/USER_STORIES.md` US-01) — le code SQLAlchemy
reste quasi identique entre les deux, seule la chaîne de connexion change.

## Alembic — gestion des migrations de schéma

Ajouté dans le cadre de US-01. Cette section documente ce qu'Alembic fait
et pourquoi, pour s'y retrouver plus tard sans avoir à tout redécouvrir.

### Le problème qu'Alembic résout

`Base.metadata.create_all(engine)` (utilisé pendant les tests initiaux
de `db/models.py`) crée les tables qui n'existent pas encore, mais **ne
modifie jamais une table déjà existante**. Si on ajoute une colonne à
`Pastor` après coup, `create_all` ne fait rien — la base reste
désynchronisée avec le code. Alembic résout ça avec des **scripts de
migration versionnés**, capables de faire évoluer une base existante
(ajouter/renommer/supprimer une colonne, etc.) sans perdre les données
déjà présentes.

### Structure mise en place

```
epastor/
├── alembic.ini              # config générale
└── db/migrations/
    ├── env.py                 # connexion + détection des modèles
    ├── script.py.mako         # gabarit pour chaque nouvelle migration
    └── versions/
        └── 4e1ab6dd2715_initial_schema.py   # la migration initiale
```

### Configuration spécifique à ce projet

Deux fichiers ont été adaptés par rapport à ce que `alembic init` génère
par défaut, pour que la chaîne de connexion ne soit définie qu'à un seul
endroit (`DATABASE_URL`, la même variable que `db/session.py`) :

- **`alembic.ini`** : la ligne `sqlalchemy.url = ...` a été retirée /
  laissée en commentaire — la vraie valeur est injectée dynamiquement
  par `env.py`, pas lue depuis ce fichier.
- **`db/migrations/env.py`** : deux ajouts par rapport au fichier généré
  par défaut :
  1. Import de `Base` **et** de toutes les classes de modèles
     (`from db.models import Pastor, Channel, ...`). Ce n'est pas
     cosmétique : `Base.metadata` ne "connaît" une table que si sa
     classe a été exécutée par Python au moins une fois. Importer
     `Base` seule ne suffit pas.
  2. Lecture de `DATABASE_URL` depuis l'environnement et injection dans
     la config Alembic via `config.set_main_option("sqlalchemy.url", ...)`,
     avec le même repli SQLite par défaut que `db/session.py`.

### Le cycle de travail avec Alembic

1. **Modifier `db/models.py`** (ajouter/changer un champ)
2. **Générer une migration** :
   ```powershell
   alembic revision --autogenerate -m "description du changement"
   ```
   Alembic compare `Base.metadata` (ce que dit le code) à l'état réel de
   la base, et génère un script dans `db/migrations/versions/` avec deux
   fonctions : `upgrade()` (applique le changement) et `downgrade()`
   (l'annule).
3. **⚠️ Toujours relire le script généré avant de l'appliquer.**
   `--autogenerate` n'est pas fiable à 100% — testé concrètement sur ce
   projet : ajouter un simple champ à `Pastor` a fait apparaître deux
   `op.drop_constraint(...)` parasites sur les contraintes `CHECK` des
   enums (`status`, `transcript_status`), qui n'avaient pourtant pas
   changé. C'est un faux positif connu d'Alembic sur SQLite avec les
   enums. Appliqué tel quel, ce script aurait supprimé des contraintes
   de validité sans raison. → toujours lire `upgrade()` ligne par ligne
   avant l'étape suivante.
4. **Appliquer la migration** :
   ```powershell
   alembic upgrade head
   ```
   `head` signifie "la migration la plus récente". Alembic sait quelles
   migrations ont déjà été appliquées grâce à la table technique
   `alembic_version`, créée automatiquement en base — elle contient une
   seule ligne indiquant la dernière migration appliquée, ce qui permet
   à `upgrade head` de ne rejouer que ce qui manque.

### Migration initiale de ce projet

`4e1ab6dd2715_initial_schema.py` — générée par autogénération à partir
des 7 modèles, appliquée avec succès. Contient un `op.create_table(...)`
par table, dans un ordre qui respecte les dépendances de clés étrangères
(`pastors` avant `channels`/`books`, etc.), déduit automatiquement par
Alembic à partir des `ForeignKey` définies dans `models.py`.

### Commandes de référence

```powershell
# Générer une nouvelle migration après avoir modifié models.py
alembic revision --autogenerate -m "description"

# Appliquer toutes les migrations en attente
alembic upgrade head

# Revenir en arrière d'une migration (utilise downgrade())
alembic downgrade -1

# Voir l'historique des migrations
alembic history
```

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
