# ePastor

A platform allowing any pastor, minister, or church to make their
YouTube content searchable in natural language — helping someone find
concrete answers to practical life questions (depression, prayer,
prosperity, discipline...) through real teachings, with sourced answers
(video + timestamp) and links to the book catalog when relevant.

> 📄 See [`docs/SPECS.md`](docs/SPECS.md) for the full vision and
> [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) for the data schema.
>
> 🗺️ Visual progress: [`docs/roadmap/chronological.mermaid`](docs/roadmap/chronological.mermaid)
> (execution order) and [`docs/roadmap/by_epic.mermaid`](docs/roadmap/by_epic.mermaid)
> (grouped by epic) — updated after each completed user story.
>
> 🇫🇷 Version française : [`README.fr.md`](README.fr.md)

## Project status

🚧 **Specs and data model largely formalized, first data layer
implemented and tested.** The schema (10 tables) runs locally with
Alembic, and a unit test suite covers the core models. Ingestion, the
agent, and the API still need to be built. Nothing is in production.

## Concept in one sentence

A single generic engine (video discovery → transcription → vector
indexing → sourced AI answer, capable of synthesizing across several
videos and, carefully, the book catalog), reusable for any pastor, with
three ways to access it:

- **Embedded widget** on an existing church website (a fixed instance)
- **General ePastor app**, where the visitor picks preferred pastors and
  also gets suggestions for "associated" pastors
- **General mode**, with no pastor selected, for broad life questions
  that cut across several teachers — with strict named attribution when
  positions diverge, never blended into a single voice

Sensitive topics (mental health, distress, material needs) get careful
handling: the tool always points toward real human support, never acts
as a substitute — see the dedicated section below.

## Repo structure

```
epastor/
├── docs/            specs and data model (source of truth for the project)
├── db/              ORM models + Alembic migrations (multi-tenant base, one pastor = one tenant)
├── ingestion/        video discovery → transcription → chunking/embeddings
├── catalog/          per-pastor book catalog management
├── agent/             LangGraph: multi-source retrieval → synthesis → book enrichment
├── api/               FastAPI (operator / visitor / widget routes)
├── web/                interfaces (operator form, visitor chatbot)
├── tests/              unit tests (pytest, in-memory SQLite)
├── scripts/            one-off/admin scripts (e.g. GitHub issue sync from user stories)
└── config.py           global technical settings (not the list of pastors — see db/)
```

## Key principle: multi-tenant from v1

One pastor = one `tenant_id`. All data (videos, chunks, books) lives in
a single database, filtered by pastor — not a separate database per
pastor. This choice is documented in `docs/SPECS.md` §3.

## Reference test case

Development is validated against Mohammed Sanogo's case (dual YouTube
channel — personal + church, requiring speaker-based filtering on the
second one — plus an external book catalog), since it's the most
complex case covered by the specs. Once validated on him, the same
engine must work for a pastor with a single channel and no catalog,
with zero code changes.

## What's done / what's left

- [x] v1 specs (`docs/SPECS.md`)
- [x] Data model (`docs/DATA_MODEL.md`)
- [x] v1 user stories, with tech/output/process per story (`docs/USER_STORIES.md`)
- [x] Video discovery script, file-based version (`ingestion/discover_videos.py`)
      — still driven by a hardcoded `config.py`, needs to migrate to the database
- [x] Script that syncs GitHub issues from the user stories file
      (`scripts/create_github_issues.py`), with update-in-place support
      and auto-generated sub-task checklists from each story's Process section
- [x] **US-01 — ORM models + migrations — done**
  - [x] `Base` (`db/base.py`)
  - [x] `Pastor` model (id, display_name, church_name,
        pastoral_team_contact_email, created_at, status as a native
        `Enum` with `create_constraint=True`)
  - [x] `Channel` model (id, pastor_id as foreign key, youtube_url,
        youtube_channel_id, requires_speaker_filter, name_keywords as
        `JSON`, last_scanned_at)
  - [x] `Show` model (targeted shows on a personal channel, optional —
        channel_id, name, JSON keywords, is_active)
  - [x] `Video` model (id = YouTube video id as `String(11)`, not a UUID;
        channel_id + pastor_id denormalized, optional show_id,
        transcript_status as `Enum`)
  - [x] `TranscriptChunk` model (text as `Text`, start/end_seconds as
        `Float`; `embedding` intentionally absent — lives in FAISS,
        linked by `id`, not stored in the relational database)
  - [x] `Book` model (per-pastor catalog)
  - [x] `Visitor` model
  - [x] `VisitorPastorFollow` model (composite primary key
        visitor_id + pastor_id, no separate technical id)
  - [x] `db/session.py` (engine, `PRAGMA foreign_keys=ON` for SQLite,
        `SessionLocal` factory, reads `DATABASE_URL`)
  - [x] Alembic configured (`alembic.ini`, `db/migrations/env.py`) and
        initial migration generated + applied — see detailed section below
  - [x] Unit test suite (`tests/`, pytest + in-memory SQLite) — 19 tests
        covering the first 8 models
  - [ ] `PrayerSignal` and `HumanContactRequest` models (sensitive
        topics, US-32/US-33) — fully specified in `docs/DATA_MODEL.md`
        §8bis/§8ter, not yet coded
- [x] **US-02 — Seed script — done** (Sanogo pastor + 2 channels,
      idempotent, tested twice with no duplicates)
- [ ] Migrate discovery to the database (US-03/04/05)
- [ ] Targeted show filtering (US-25, P2, personal channel)
- [ ] Transcription (`ingestion/fetch_transcripts.py`)
- [ ] Chunking + embeddings (`ingestion/chunk_and_embed.py`)
- [ ] LangGraph agent — simple case (US-09/US-10)
- [ ] LangGraph agent — multi-source synthesis (US-26 to US-28, Epic H)
- [ ] General mode + conversational interaction (US-29/US-30, Epic I)
- [ ] Sensitive-topic safeguards + prayer signal + human contact request
      (US-31 to US-33, Epic I) — **involves a real GDPR policy, see
      dedicated section below**
- [ ] FastAPI API
- [ ] Operator form
- [ ] Visitor chatbot interface
- [ ] Epic G — orchestration (Apache Airflow), incremental ingestion,
      data quality, monitoring, **automatic purge of sensitive data
      (US-34, P0 — blocking before real production)**
      (see `docs/USER_STORIES.md` US-21 to US-24 and US-34)

**Current dev environment**: SQLite (local file, zero install) to learn
and iterate fast. Migration to PostgreSQL is planned before any real
deployment (see `docs/USER_STORIES.md` US-01) — the SQLAlchemy code
stays nearly identical between the two, only the connection string
changes.

## Sensitive topics — mental health, distress, material needs

The general mode (5c) has to answer real life questions ("how do I get
out of depression?"), which carries real responsibility. Principles
already decided (details in `docs/USER_STORIES.md` US-31 to US-34 and
`docs/DATA_MODEL.md` §8bis/§8ter):

- The tool is **never a substitute** for real human support — any answer
  on a sensitive topic points toward professional/community support,
  even when the source content (a video) doesn't do so explicitly.
- **No automatic or silent reporting**: the "prayer signal" and "human
  contact request" only trigger through a deliberate, explicit action by
  the visitor — never from the system merely detecting a sensitive topic.
- **Dual recipient, disclosed upfront**: every signal goes to both the
  pastor's team and the ePastor support team — this must be stated
  clearly to the person before they consent, not buried in general terms.
- **Short retention and a proposed automatic purge** (14-30 days
  depending on the table, details in `DATA_MODEL.md`) — to be validated
  with legal counsel/a DPO before any real production deployment; this
  is not legal advice, just a reasonable technical default.

## Out of scope for v1

See `docs/SPECS.md` §6 — notably: no full book text ingestion
(copyright), no authentication/payment, no co-occurrence-based
recommendation engine (data structure ready, algorithm deferred to v2),
and no LLM-generated "pastor style" imitation (deliberately dropped, not
just deferred — see SPECS.md §6 for the reasoning; replaced by a
lighter approach: citing the pastor's exact wording more generously
within existing quotation limits).

## Alembic — schema migration management

Added as part of US-01. This section documents what Alembic does and
why, so it doesn't need to be rediscovered later.

### The problem Alembic solves

`Base.metadata.create_all(engine)` (used during the initial testing of
`db/models.py`) creates tables that don't exist yet, but **never
modifies an already-existing table**. If a column is added to `Pastor`
later on, `create_all` does nothing — the database stays out of sync
with the code. Alembic solves this with **versioned migration
scripts**, able to evolve an existing database (add/rename/drop a
column, etc.) without losing the data already there.

### Structure in place

```
epastor/
├── alembic.ini              # general config
└── db/migrations/
    ├── env.py                 # connection + model detection
    ├── script.py.mako         # template for each new migration
    └── versions/
        └── 4e1ab6dd2715_initial_schema.py   # the initial migration
```

### Project-specific configuration

Two files were adapted from what `alembic init` generates by default,
so the connection string is only defined in one place (`DATABASE_URL`,
the same variable used by `db/session.py`):

- **`alembic.ini`**: the `sqlalchemy.url = ...` line was removed / left
  commented out — the real value is injected dynamically by `env.py`,
  not read from this file.
- **`db/migrations/env.py`**: two additions compared to the
  default-generated file:
  1. Import of `Base` **and** every model class
     (`from db.models import Pastor, Channel, ...`). This isn't
     cosmetic: `Base.metadata` only "knows" about a table if its class
     has actually been executed by Python at least once. Importing
     `Base` alone isn't enough.
  2. Reading `DATABASE_URL` from the environment and injecting it into
     Alembic's config via `config.set_main_option("sqlalchemy.url", ...)`,
     with the same SQLite fallback default as `db/session.py`.

### Working cycle with Alembic

1. **Modify `db/models.py`** (add/change a field)
2. **Generate a migration**:
   ```powershell
   alembic revision --autogenerate -m "description of the change"
   ```
   Alembic compares `Base.metadata` (what the code says) against the
   actual state of the database, and generates a script in
   `db/migrations/versions/` with two functions: `upgrade()` (applies
   the change) and `downgrade()` (reverts it).
3. **⚠️ Always review the generated script before applying it.**
   `--autogenerate` is not 100% reliable — concretely tested on this
   project: adding a simple field to `Pastor` produced two spurious
   `op.drop_constraint(...)` calls on the enum `CHECK` constraints
   (`status`, `transcript_status`), which hadn't actually changed. This
   is a known Alembic false positive with enums on SQLite. Applied as-is,
   this script would have dropped valid constraints for no reason. →
   always read `upgrade()` line by line before the next step.
4. **Apply the migration**:
   ```powershell
   alembic upgrade head
   ```
   `head` means "the most recent migration". Alembic knows which
   migrations have already been applied thanks to the technical
   `alembic_version` table, created automatically in the database — it
   holds a single row pointing to the last applied migration, which lets
   `upgrade head` only replay what's missing.

### This project's initial migration

`4e1ab6dd2715_initial_schema.py` — generated via autogeneration from the
7 models, applied successfully. Contains one `op.create_table(...)` per
table, in an order that respects foreign-key dependencies (`pastors`
before `channels`/`books`, etc.), automatically inferred by Alembic from
the `ForeignKey` declarations in `models.py`.

### Reference commands

```powershell
# Generate a new migration after modifying models.py
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration (uses downgrade())
alembic downgrade -1

# View migration history
alembic history
```

## Local setup (as of now)

```powershell
pip install yt-dlp sqlalchemy alembic requests
python -m ingestion.discover_videos --dry-run
```

Requires target channels to be set in `config.py` for now (migration to
a web form planned — see "What's done / what's left").
