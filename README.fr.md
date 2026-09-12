# ePastor

Plateforme permettant à tout pasteur/serviteur/église de rendre son
contenu YouTube interrogeable en langage naturel — pour aider une
personne à trouver des réponses concrètes à des questions de vie
pratique (dépression, prière, prospérité, discipline...) à travers de
vrais enseignements, avec réponses sourcées (vidéo + timestamp) et
renvoi vers le catalogue de livres quand pertinent.

> 📄 Voir [`docs/SPECS.md`](docs/SPECS.md) pour la vision complète et
> [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) pour le schéma de données.
>
> 🗺️ Avancement visuel : [`docs/roadmap/chronological.mermaid`](docs/roadmap/chronological.mermaid)
> (ordre d'exécution) et [`docs/roadmap/by_epic.mermaid`](docs/roadmap/by_epic.mermaid)
> (regroupé par epic) — mis à jour après chaque user story terminée.
>
> 🇬🇧 English version (reference): [`README.md`](README.md)

## Statut du projet

🚧 **Specs et modèle de données largement formalisés, première couche
de données implémentée et testée.** Le schéma (10 tables) tourne en
local avec Alembic, une suite de tests unitaires couvre les modèles
principaux. L'ingestion, l'agent et l'API restent à construire. Rien
n'est en production.

## Concept en une phrase

Un moteur unique (découverte de vidéos → transcription → indexation
vectorielle → réponse sourcée par IA, capable de synthétiser plusieurs
vidéos et, prudemment, le catalogue de livres), réutilisable pour
n'importe quel pasteur, avec trois façons d'y accéder :

- **Widget intégré** à un site d'église existant (une instance fixe)
- **App ePastor générale**, où le visiteur choisit ses pasteurs préférés
  et reçoit aussi des suggestions de pasteurs "associés"
- **Mode général**, sans sélection de pasteur, pour les grandes questions
  de vie qui traversent plusieurs enseignants — avec attribution nommée
  stricte quand les positions divergent, jamais de fusion en voix unique

Un soin particulier est porté aux sujets sensibles (santé mentale,
détresse, besoins matériels) : l'outil oriente toujours vers un
accompagnement humain réel, jamais comme substitut — voir la section
dédiée plus bas.

## Structure du repo

```
epastor/
├── docs/            specs et modèle de données (source de vérité du projet)
├── db/              modèles ORM + migrations (base multi-tenant, un pasteur = un tenant)
├── ingestion/        découverte vidéos → transcription → chunking/embeddings
├── catalog/          gestion du catalogue de livres par pasteur
├── agent/             LangGraph : retrieval multi-sources → synthèse → enrichissement livres
├── api/               FastAPI (routes opérateur / visiteur / widget)
├── web/                interfaces (formulaire opérateur, chatbot visiteur)
├── tests/              tests unitaires (pytest, SQLite en mémoire)
├── config.py           paramètres techniques globaux (pas la liste des pasteurs — voir db/)
└── scripts/            scripts admin (ex: synchronisation des issues GitHub)
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
  - [x] Modèle `Pastor` (id, display_name, church_name,
        pastoral_team_contact_email, created_at, status en `Enum` natif
        avec `create_constraint=True`)
  - [x] Modèle `Channel` (id, pastor_id en clé étrangère, youtube_url,
        youtube_channel_id, requires_speaker_filter, name_keywords en
        `JSON`, last_scanned_at)
  - [x] Modèle `Show` (émissions ciblées sur chaîne perso, optionnel —
        channel_id, name, keywords en `JSON`, is_active)
  - [x] Modèle `Video` (id = id YouTube en `String(11)`, pas un UUID ;
        channel_id + pastor_id dénormalisés, show_id optionnel,
        transcript_status en `Enum`)
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
  - [x] Suite de tests unitaires (`tests/`, pytest + SQLite en mémoire) —
        19 tests couvrant les 8 premiers modèles
  - [ ] Modèles `PrayerSignal` et `HumanContactRequest` (sujets
        sensibles, US-32/US-33) — spécifiés en détail dans
        `docs/DATA_MODEL.md` §8bis/§8ter, pas encore codés
- [x] **US-02 — Script de seed — terminée** (pasteur + 2 chaînes Sanogo,
      idempotent, testé deux fois sans doublon)
- [ ] Migration de la découverte vers la base (US-03/04/05)
- [ ] Filtrage par émission ciblée (US-25, P2, chaîne perso)
- [ ] Transcription (`ingestion/fetch_transcripts.py`)
- [ ] Chunking + embeddings (`ingestion/chunk_and_embed.py`)
- [ ] Agent LangGraph — cas simple (US-09/US-10)
- [ ] Agent LangGraph — synthèse multi-sources (US-26 à US-28, Epic H)
- [ ] Mode général + interaction conversationnelle (US-29/US-30, Epic I)
- [ ] Garde-fous sujets sensibles + signalement de prière + mise en
      relation humaine (US-31 à US-33, Epic I) — **implique une vraie
      politique RGPD, voir section dédiée ci-dessous**
- [ ] API FastAPI
- [ ] Formulaire opérateur
- [ ] Interface chatbot visiteur
- [ ] Epic G — orchestration (Apache Airflow), ingestion incrémentale,
      qualité des données, monitoring, **purge automatique des données
      sensibles (US-34, P0 — bloquant avant prod réelle)**
      (voir `docs/USER_STORIES.md` US-21 à US-24 et US-34)

**Environnement de dev actuel** : SQLite (fichier local, zéro install) pour
apprendre et itérer vite. Migration vers PostgreSQL prévue avant tout
déploiement réel (voir `docs/USER_STORIES.md` US-01) — le code SQLAlchemy
reste quasi identique entre les deux, seule la chaîne de connexion change.

## Sujets sensibles — santé mentale, détresse, besoins matériels

Le mode général (5c) doit répondre à de vraies questions de vie
("comment sortir de la dépression ?"), ce qui implique une
responsabilité particulière. Principes actés (détail dans
`docs/USER_STORIES.md` US-31 à US-34 et `docs/DATA_MODEL.md` §8bis/§8ter) :

- L'outil **n'est jamais un substitut** à un accompagnement humain réel —
  toute réponse sur un sujet sensible oriente vers un accompagnement
  professionnel/communautaire, même quand le contenu source (une vidéo)
  ne le fait pas explicitement.
- **Aucun signalement automatique/silencieux** : le "signalement de
  prière" et la "mise en relation humaine" ne se déclenchent que par une
  action volontaire et explicite du visiteur — jamais par la simple
  détection d'un sujet sensible côté système.
- **Double destinataire à divulguer** : chaque signalement va à la fois
  à l'équipe du pasteur et à l'équipe support ePastor — ça doit être dit
  clairement à la personne avant qu'elle consente, pas caché dans des
  conditions générales.
- **Rétention courte et purge automatique proposée** (14-30 jours selon
  la table, détail en `DATA_MODEL.md`) — à valider avec un conseil
  juridique/DPO avant toute mise en production réelle ; ce n'est pas un
  avis juridique, seulement un défaut technique raisonnable.

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
