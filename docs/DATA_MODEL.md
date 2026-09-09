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
| pastoral_team_contact_email | string, nullable | Destinataire des signalements de prière et demandes de contact (§8bis, §8ter) — non renseigné par défaut, les deux fonctionnalités restent inactives tant qu'il ne l'est pas |
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

**Double usage de `name_keywords` selon `requires_speaker_filter`** :
- Si `requires_speaker_filter=true` (chaîne multi-orateurs) : variantes du
  nom du pasteur, utilisées par `title_mentions_speaker()` pour ne
  retenir que ses interventions (usage actif dès US-04).
- Si `requires_speaker_filter=false` (chaîne perso) : historiquement
  utilisé pour noter les émissions/segments récurrents de la chaîne (ex:
  "flamme matinale", "nightfire") en attendant que la table `shows`
  ci-dessous existe formellement — voir §2bis pour le mécanisme réel.

**Lien avec le code existant** : c'est la version "en base" de la liste
`CHANNELS` codée en dur dans `config.py`. Une ligne = un élément de cette
liste, mais éditable via formulaire au lieu d'un fichier.

## 2bis. `shows` (émissions ciblées, optionnel par chaîne)

Permet à un pasteur de définir des émissions/segments récurrents sur sa
**chaîne personnelle**, pour filtrer les vidéos par émission plutôt que
par intervenant — mécanisme indépendant de `requires_speaker_filter`
(qui répond à "qui parle ?"), celui-ci répond à "dans quelle émission ?".

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK |
| channel_id | UUID | FK → channels.id |
| name | string | Nom de l'émission (ex: "Flamme matinale") |
| keywords | string[] | Mots-clés de titre pour la reconnaissance (ex: ["flamme matinale"]) |
| is_active | boolean | Désactiver une émission sans la supprimer (émission arrêtée) |

**Comportement attendu** : si une chaîne n'a aucune émission active
définie, aucun filtrage par émission ne s'applique (comportement actuel
inchangé — tout le contenu de la chaîne est retenu, sous réserve du
filtre intervenant s'il est actif). Si au moins une émission active
existe pour la chaîne, seules les vidéos dont le titre matche au moins
une émission sont retenues.

**Lien avec `channels.name_keywords`** : le champ `name_keywords` sur
`channels` avait été renseigné en avance pour ce cas d'usage (voir note
§2) avant que la table `shows` existe formellement. À terme, cette
donnée devrait migrer vers des lignes `shows` plutôt que de rester dans
`channels.name_keywords`, pour permettre plusieurs émissions distinctes
avec activation individuelle — non fait immédiatement, à traiter lors de
l'implémentation (voir US dédiée dans `USER_STORIES.md`).

---

## 3. `videos`

Résultat de la découverte (`discover_videos.py`), une ligne par vidéo retenue.

| Champ | Type | Notes |
|---|---|---|
| id (video_id YouTube) | string | PK, pas un UUID — c'est déjà unique |
| channel_id | UUID | FK → channels.id |
| pastor_id | UUID | FK → pastors.id (dénormalisé, évite une jointure à chaque requête) |
| show_id | UUID, nullable | FK → shows.id — émission détectée, si filtrage par émission actif (§2bis) |
| title | string | |
| url | string | |
| duration_seconds | int, nullable | |
| upload_date | date, nullable | |
| language | enum, nullable | `fr`, `en` — rempli à l'étape transcript (US-06), pas à la découverte : c'est la langue du transcript qui réussit (fr essayé en premier, fallback en) qui fait foi, pas une déduction depuis le titre |
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
| language | enum, nullable | Copié depuis `videos.language` au moment du chunking (US-08) — même logique de dénormalisation que `pastor_id`, pour filtrer par langue au retrieval sans jointure |
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

## 8bis. `prayer_signals` (signalement de prière — sensible, RGPD)

Émis uniquement par une action volontaire et explicite du visiteur (ex:
bouton "Prier pour moi" à la fin d'une réponse sur un sujet sensible) —
**jamais généré automatiquement** par la détection d'un sujet sensible
côté système. Voir note RGPD en fin de section.

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK |
| pastor_id | UUID | FK → pastors.id — destinataire via `pastoral_team_contact_email` |
| first_name | string, nullable | Fourni volontairement ; absent par défaut (anonyme) |
| note | text, nullable | Mot libre écrit par la personne elle-même ; **jamais pré-rempli automatiquement à partir de sa question d'origine** |
| created_at | timestamp | |
| status | enum | `new`, `prayed` — suivi côté équipe pastorale |

## 8ter. `human_contact_requests` (mise en relation — sensible, RGPD, données identifiantes)

Plus sensible que `prayer_signals` : implique de vraies coordonnées de
contact. Émis par une action opt-in séparée (ex: "Être recontacté(e) par
quelqu'un de l'équipe"), avec un écran de consentement explicite
indiquant clairement qui recontactera la personne et pourquoi.

| Champ | Type | Notes |
|---|---|---|
| id | UUID | PK |
| pastor_id | UUID | FK → pastors.id |
| first_name | string, nullable | |
| category | enum | `emotional_spiritual`, `housing`, `financial`, `administrative`, `other` — motif de la demande, pour orienter l'équipe qui recontacte |
| contact_method | enum | `phone`, `email` |
| contact_value | string | Donnée identifiante — accès restreint, rétention courte (voir note RGPD) |
| note | text, nullable | |
| created_at | timestamp | |
| status | enum | `new`, `contacted`, `closed` |

### Note RGPD, applicable aux deux tables ci-dessus

- **Consentement explicite et action volontaire uniquement** : ni l'une
  ni l'autre table ne doit jamais être peuplée automatiquement par une
  détection système de sujet sensible (US-31) — seule une action
  délibérée du visiteur (clic sur un bouton dédié, après avoir vu
  clairement ce qui sera partagé et à qui) déclenche un enregistrement.
  Un signalement silencieux à l'insu de la personne serait à la fois un
  problème éthique (proche de la surveillance plutôt que de
  l'accompagnement) et une violation du RGPD (données de santé/détresse
  = catégorie spéciale, article 9, consentement explicite obligatoire).
- **Minimisation par défaut** : `first_name` reste vide sauf si la
  personne choisit de le renseigner. `note` n'est jamais pré-rempli
  depuis la question d'origine.
- **Double destinataire — à divulguer explicitement** : par défaut,
  chaque signalement/demande est transmis à **deux** destinataires :
  l'équipe pastorale du pasteur concerné (`pastoral_team_contact_email`)
  **et** l'équipe support de la plateforme ePastor, sur une boîte dédiée
  (supervision transverse, ex: repérer un pasteur qui ne répond jamais).
  Le RGPD exige que la personne connaisse tous les destinataires de sa
  donnée avant de consentir — l'écran de consentement (US-32/US-33) doit
  donc nommer explicitement les deux, pas seulement "l'équipe du
  pasteur".
- **Accès restreint** : au-delà de ces deux destinataires déclarés,
  aucun autre pasteur ni tableau de bord général ne doit exposer ces
  enregistrements.
- **Politique de rétention proposée** (défaut technique à valider avec un
  conseil juridique/DPO avant mise en production réelle — ce qui suit
  n'est pas un avis juridique) :

  | Table | État | Purge |
  |---|---|---|
  | `prayer_signals` | `new`, sans action depuis 14 jours | passe automatiquement à un état clos (pas de suppression immédiate, juste arrêt du suivi actif) |
  | `prayer_signals` | `prayed` (ou clos automatiquement) | supprimée 30 jours après passage à cet état |
  | `human_contact_requests` | `new`, sans contact depuis 7 jours | passe automatiquement à un état clos (délai plus court : une demande de contact non traitée après une semaine perd sa pertinence) |
  | `human_contact_requests` | `contacted`/`closed` | `contact_value` et `first_name` supprimés (anonymisation) sous 14 jours ; `category`/`created_at`/`status` peuvent être conservés sans lien identifiant, à des fins statistiques uniquement |

  Mécanisme d'application : un job planifié (voir US-34, Epic G — cohérent
  avec le choix Airflow déjà fait pour l'orchestration) qui applique ces
  règles quotidiennement, plutôt qu'une purge manuelle.

---

## Schéma relationnel simplifié

```
pastors (1) ──< channels (1) ──< videos (1) ──< transcript_chunks
   │                  │                │
   │                  └──< shows ──────┘  (video.show_id optionnel)
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
