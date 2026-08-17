# ePastor — Modèle de données v1

Convention : chaque table a un `id` technique (UUID) en clé primaire,
non représenté explicitement ci-dessous sauf mention contraire.

---

## 1. `pastors` (le tenant)

L'entité centrale. Un pasteur = une instance = un `tenant_id`.

| Champ | Type | Notes |
|---|---|---|
| id (tenant_id) | UUID | PK |
| display_name | string | Nom public ("Mohammed Sanogo") |
| church_name | string, nullable | Ex: "Vases d'Honneur" |
| created_at | timestamp | |
| status | enum | `pending`, `active`, `suspended` — cf. Q ouverte "légitimité opérateur" |

**Pourquoi séparer `display_name` du nom de chaîne YouTube ?**
Un pasteur peut avoir 2 chaînes avec des noms différents. Le nom public
du pasteur est une donnée à part, saisie par lui via le formulaire (spec §5, étape opérateur).

---

## 2. `channels`

Une ou plusieurs chaînes YouTube rattachées à un pasteur (spec §4).

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK |
| pastor_id | UUID | FK → pastors.id |
| youtube_url | string | |
| youtube_channel_id | string, nullable | Rempli après première découverte |
| requires_speaker_filter | boolean | Chaîne perso (false) vs multi-orateurs (true) |
| name_keywords | string[] | Variantes de nom si filtre actif (ex: ["sanogo", "apôtre sanogo"]) |
| last_scanned_at | timestamp, nullable | Pour savoir quand relancer la découverte |

**Lien avec le code existant** : c'est la version "en base" de la liste
`CHANNELS` codée en dur dans `config.py`. Une ligne = un élément de cette
liste, mais éditable via formulaire au lieu d'un fichier.

---

## 3. `videos`

Résultat de la découverte (`discover_videos.py`), une ligne par vidéo retenue.

| Champ | Type | Notes |
|---|---|---|
| id (video_id YouTube) | string | PK, pas un UUID — c'est déjà unique |
| channel_id | UUID | FK → channels.id |
| pastor_id | UUID | FK → pastors.id (dénormalisé, évite une jointure à chaque requête) |
| title | string | |
| url | string | |
| duration_seconds | int, nullable | |
| upload_date | date, nullable | |
| speaker_match | boolean | Résultat du filtre titre |
| match_reason | string | Traçabilité — pourquoi retenue/exclue |
| transcript_status | enum | `pending`, `fetched`, `unavailable`, `error` |

**Pourquoi dénormaliser `pastor_id` ici alors qu'on peut le retrouver via `channel_id` ?**
Toutes les requêtes de retrieval (spec §5b : "pioche dans préférés + associés")
vont filtrer par pasteur en premier lieu. Avoir `pastor_id` directement
évite une jointure sur *chaque* recherche vectorielle — un choix de perf,
pas de pureté relationnelle.

---

## 4. `transcript_chunks`

Le contenu réellement indexé et recherché (le cœur du RAG).

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK |
| video_id | string | FK → videos.id |
| pastor_id | UUID | FK → pastors.id (même logique de dénormalisation) |
| text | text | Le contenu du chunk |
| start_seconds | float | Timestamp de départ dans la vidéo |
| end_seconds | float | |
| embedding | vector | Selon le store choisi (FAISS = fichier séparé, sinon colonne pgvector) |

**Note technique** : si on reste sur FAISS (comme discuté au départ), cette
table vit en deux morceaux — les métadonnées ici, et les vecteurs dans
l'index FAISS séparé, reliés par `id`. Si on bascule vers une base avec
extension vectorielle (ex: PostgreSQL + pgvector), tout tient dans une
seule table. **Décision à prendre plus tard**, pas urgente maintenant.

---

## 5. `books` (catalogue, optionnel par pasteur)

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK |
| pastor_id | UUID | FK → pastors.id |
| title | string | |
| url | string | |
| price | string | Garder en texte affichable ("€16,00") plutôt que decimal — pas de calcul dessus |
| synopsis | text, nullable | |

---

## 6. `visitors` (app générale uniquement — spec §4bis)

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK, anonyme pour l'instant (pas de compte obligatoire — à trancher) |
| created_at | timestamp | |

## 7. `visitor_pastor_follows`

Table de liaison — les pasteurs qu'un visiteur suit/préfère.

| Champ | Type | Notes |
|---|---|---|
| visitor_id | UUID | FK → visitors.id |
| pastor_id | UUID | FK → pastors.id |
| is_explicit_preference | boolean | true = ajouté volontairement, false = déduit de l'usage (historique implicite, spec §4bis) |
| created_at | timestamp | |

**Cette table est la base du futur calcul de recommandation** ("pasteurs
associés" = co-occurrence dans cette table), mais le calcul lui-même
reste hors périmètre v1 (spec §6).

---

## Schéma relationnel simplifié

```
pastors (1) ──< channels (1) ──< videos (1) ──< transcript_chunks
   │                                                    
   ├──< books
   │
   └──< visitor_pastor_follows >── visitors
```

---

## Ce que ce schéma NE couvre pas encore (volontairement)

- Table `questions`/`answers` (historique des questions posées) — utile
  pour analytics et pour affiner la recommandation plus tard, mais pas
  mentionnée dans les specs v1, donc pas ajoutée maintenant.
- Authentification opérateur (login/mot de passe) — hors périmètre acté.
- Table de statut du calcul de recommandation (v2).
