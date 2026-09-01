# ePastor — User Stories v1

Convention : chaque US a un id (`US-XX`), une priorité (P0 = bloquant
pour un premier bout-à-bout fonctionnel, P1 = nécessaire pour la v1
complète, P2 = peut attendre v2), un renvoi vers la table du
`DATA_MODEL.md` qu'elle touche principalement, les **technos** utilisées,
l'**output** concret produit, et un **résumé du process** pour y arriver.

---

## Epic A — Fondations données (db/)

### US-01 (P0) — Schéma de données en base
*En tant que développeuse, je veux que le schéma de données (tables
`pastors`, `channels`, `videos`, `transcript_chunks`, `books`, `visitors`,
`visitor_pastor_follows`) existe réellement en base, afin que tout le
reste du projet ait une source de vérité unique au lieu de fichiers JSON
éparpillés.*

- **Technos** : PostgreSQL (recommandé si on veut pgvector plus tard sans
  migrer de moteur), SQLAlchemy (ORM), Alembic (migrations)
- **Output** : base PostgreSQL locale/cloud avec les 7 tables créées,
  fichier `db/models.py`, dossier `db/migrations/` versionné
- **Process** : définir les classes ORM à partir de `DATA_MODEL.md` →
  générer une migration Alembic initiale → l'appliquer sur une base de
  dev → vérifier les tables avec un client SQL (ex: DBeaver ou `psql`)

### US-02 (P0) — Créer un pasteur/chaîne en base (script)
*En tant que développeuse, je veux pouvoir créer un pasteur et une
chaîne en base via un script simple (avant même le formulaire web), afin
de valider le schéma sans attendre l'interface.*

- **Technos** : Python, SQLAlchemy (session + insert)
- **Output** : script `db/seed_pastor.py`, une ligne `pastors` + une ou
  plusieurs lignes `channels` visibles en base (cas Sanogo)
- **Process** : écrire un script qui instancie les objets ORM `Pastor` et
  `Channel` avec les données Sanogo (nom, chaîne perso, chaîne église,
  mots-clés) → `session.add()` + `commit()` → vérifier par une requête
  `SELECT`

---

## Epic B — Découverte et ingestion vidéo (ingestion/)

### US-03 (P0) — Lister automatiquement les vidéos des chaînes
*En tant qu'opérateur (pasteur), je veux que le système liste
automatiquement les vidéos de mes chaînes YouTube configurées, afin de
ne pas avoir à les recenser manuellement.*

- **Technos** : `yt-dlp` (déjà utilisé), Python, SQLAlchemy
- **Output** : lignes insérées dans la table `videos` (au lieu du JSONL
  actuel), une ligne par vidéo découverte, `last_scanned_at` mis à jour
  sur la `channel` traitée
- **Process** : lire les `channels` d'un pasteur depuis la base (plus
  depuis `config.py`) → appeler `yt-dlp` en mode `extract_flat` par
  chaîne → mapper chaque résultat vers le modèle `Video` → insérer en
  base avec `channel_id`/`pastor_id`
- **Lien Data Engineering** : cette découverte doit être **incrémentale**,
  pas un re-scan complet à chaque fois (voir US-22, Epic G) — comparer
  les `video_id` déjà connus avant insertion, et ne traiter que les
  nouveaux

### US-04 (P0) — Filtrer les vidéos où le pasteur est l'intervenant
*En tant qu'opérateur avec une chaîne multi-orateurs (ex: chaîne
d'église), je veux que seules les vidéos où je suis l'intervenant soient
retenues, afin que le chatbot ne réponde pas avec le contenu d'autres
pasteurs.*

- **Technos** : Python (regex + normalisation Unicode, logique déjà
  écrite dans `title_mentions_speaker`)
- **Output** : champ `speaker_match` (+ `match_reason`) rempli sur
  chaque ligne `videos`
- **Process** : lire `name_keywords` depuis `channels` en base (plus
  depuis `config.py`) → appliquer la même heuristique de matching sur le
  titre → stocker le résultat, sans supprimer les vidéos exclues (utile
  pour audit/ajustement du filtre plus tard)
- **Lien avec US-25** : ce filtre répond à "qui parle ?" (intervenant).
  Sur une chaîne perso (`requires_speaker_filter=false`), un filtrage
  complémentaire par émission ciblée est possible — voir US-25, un
  mécanisme indépendant, pas un remplacement de celui-ci.

### US-25 (P2) — Filtrer les vidéos par émission ciblée (chaîne perso)
*En tant qu'opérateur avec une chaîne personnelle diffusant plusieurs
émissions récurrentes (ex: "Flamme matinale", "Nightfire"), je veux
pouvoir définir ces émissions et ne faire indexer que celles qui
m'intéressent, afin de ne pas noyer le chatbot avec du contenu hors
sujet (ex: annonces, rediffusions génériques) présent sur la même
chaîne.*

- **Technos** : Python (même logique de matching que
  `title_mentions_speaker`, réutilisée pour matcher un titre contre les
  `keywords` d'une émission plutôt que contre un nom de pasteur),
  SQLAlchemy
- **Output** : table `shows` peuplée (US-12 étendu au formulaire, ou
  script de seed en attendant), champ `show_id` rempli sur `videos`
  quand une émission est détectée
- **Process** : pour une chaîne donnée, récupérer ses `shows` actifs →
  si aucune émission active, ne rien filtrer (comportement actuel
  inchangé) → si au moins une émission active, ne retenir que les
  vidéos dont le titre matche les `keywords` d'au moins une émission →
  stocker `show_id` sur la vidéo retenue pour traçabilité
- **Note de conception** : mécanisme volontairement indépendant de
  `requires_speaker_filter`/US-04 — l'un répond à "qui parle ?", l'autre
  à "dans quelle émission ?". Une chaîne pourrait en théorie combiner les
  deux plus tard, mais ce n'est pas le besoin actuel (le filtrage par
  émission ne cible que les chaînes perso pour l'instant).

### US-05 (P1) — Voir le nombre de vidéos trouvées/retenues
*En tant qu'opérateur, je veux voir combien de vidéos ont été trouvées
et combien retenues après filtrage, afin de vérifier que le filtrage est
pertinent avant de lancer la transcription (coûteuse).*

- **Technos** : SQL (requête d'agrégation), FastAPI (endpoint), simple
  affichage web (peut être fait en HTML basique avant le vrai `web/`)
- **Output** : endpoint `GET /pastors/{id}/discovery-stats` retournant
  un JSON `{total, retained, excluded}`
- **Process** : requête `COUNT(*) GROUP BY speaker_match` sur `videos`
  filtrée par `pastor_id` → exposer en JSON → afficher côté opérateur
- **Lien Data Engineering** : ces stats sont un premier niveau de
  monitoring — voir US-24 (Epic G) pour une observabilité plus complète
  du pipeline (taux d'échec, latence, alerting)

### US-06 (P0) — Récupérer les transcripts avec timestamps
*En tant que système, je veux récupérer le transcript de chaque vidéo
retenue avec les timestamps par segment, afin de pouvoir citer
précisément "à 12:34" dans une réponse.*

- **Technos** : `youtube-transcript-api`, Python, SQLAlchemy
- **Output** : script `ingestion/fetch_transcripts.py`, segments bruts
  stockés temporairement (avant chunking, cf. US-08) avec leur
  `start`/`end`, champ `transcript_status` mis à jour sur `videos`
- **Process** : boucler sur les `videos` avec `speaker_match=true` et
  `transcript_status=pending` → appeler l'API transcript (langue `fr`
  puis fallback `en`) → si succès, stocker les segments ; si échec,
  passer `transcript_status=unavailable` ou `error`
- **Lien Data Engineering** : valider la qualité du transcript avant de
  le marquer `fetched` (transcript vide, trop court, ou anormalement
  répétitif) plutôt que de laisser passer un contenu inexploitable
  silencieusement — voir US-23 (Epic G, qualité des données)

### US-07 (P1) — Signaler les vidéos sans transcript disponible
*En tant qu'opérateur, je veux être informé si une vidéo n'a pas de
transcript disponible (pas de sous-titres), afin de comprendre pourquoi
certaines de mes vidéos ne sont pas interrogeables.*

- **Technos** : SQL, FastAPI (endpoint), même écran que US-05
- **Output** : liste des vidéos `transcript_status=unavailable` exposée
  à l'opérateur
- **Process** : requête filtrée sur `transcript_status` → affichage
  (titre + raison) dans l'écran de suivi

---

## Epic C — Indexation et recherche (ingestion/, agent/)

### US-08 (P0) — Chunker et vectoriser les transcripts
*En tant que système, je veux découper les transcripts en chunks avec
leurs timestamps et les transformer en vecteurs, afin de pouvoir
effectuer une recherche sémantique par question.*

- **Technos** : LangChain (text splitters), un modèle d'embeddings
  (ex: `text-embedding-3-small` OpenAI, ou un modèle open-source via
  `sentence-transformers` si on veut éviter les coûts API), FAISS (déjà
  choisi comme vector store)
- **Output** : lignes `transcript_chunks` en base (texte + timestamps +
  `pastor_id`) + fichier(s) d'index FAISS correspondants
- **Process** : regrouper les segments de transcript en chunks
  cohérents (~30-60s de contenu parlé) → générer l'embedding de chaque
  chunk → insérer les métadonnées en base et le vecteur dans FAISS,
  reliés par `id`
- **Lien Data Engineering** : valider chaque chunk avant insertion
  (texte non vide, `start_seconds < end_seconds`, longueur minimale) —
  voir US-23 (Epic G) ; ne pas ré-embedder des chunks déjà générés lors
  d'un re-run (idempotence, voir US-22)

### US-09 (P0) — Répondre à une question à partir du contenu vidéo
*En tant que visiteur, je veux poser une question en langage naturel et
recevoir une réponse construite à partir du contenu vidéo du/des
pasteur(s) concerné(s), afin d'obtenir une réponse fiable plutôt qu'une
réponse générique du modèle.*

- **Technos** : LangGraph, un LLM (Claude via API Anthropic, cohérent
  avec le reste de ton stack), FAISS (retrieval)
- **Output** : fonction/endpoint qui prend une question + `pastor_id(s)`
  et retourne une réponse texte générée à partir des chunks pertinents
- **Process** : construire le graphe LangGraph (nœud retrieval → nœud
  génération) → au retrieval, filtrer FAISS par `pastor_id` avant la
  recherche de similarité → injecter les chunks trouvés dans le prompt →
  générer la réponse en forçant l'appui sur les sources fournies
  uniquement
- **Lien avec Epic H** : ce flux couvre le cas d'une question ciblée sur
  un point précis. Pour une question large nécessitant de croiser
  plusieurs vidéos, voir US-26/US-27 (décomposition + synthèse
  multi-sources) — un raffinement de ce même graphe, pas un chemin séparé

### US-10 (P0) — Citer la vidéo source avec timestamp
*En tant que visiteur, je veux que chaque réponse indique la ou les
vidéos sources avec un lien direct au bon timestamp, afin de pouvoir
vérifier l'information à la source.*

- **Technos** : LangGraph (même graphe que US-09), formatage Python simple
  (URL YouTube avec paramètre `&t=123s`)
- **Output** : réponse enrichie avec une liste de sources
  `{title, url_with_timestamp}`
- **Process** : à partir des chunks utilisés pour générer la réponse
  (US-09), récupérer leurs `video_id` + `start_seconds` associés →
  construire l'URL avec paramètre de timestamp → les joindre à la
  réponse finale
- **Note de conception** : privilégier des citations généreuses (dans les
  limites déjà fixées pour éviter la reproduction intégrale) plutôt qu'une
  paraphrase systématique — ça restitue une partie du "ton" du pasteur
  sans les risques d'un profil de style généré (voir SPECS.md §6, décision
  actée : pas d'imitation de style par LLM)

### US-11 (P1) — Enrichir avec le catalogue livres
*En tant que visiteur, je veux que si un livre du pasteur est mentionné
dans le contenu utilisé pour répondre, la réponse inclue son titre,
prix, lien et synopsis, afin de découvrir ses ressources sans que le
texte du livre soit reproduit.*

- **Technos** : LangGraph (nœud supplémentaire), LLM avec sortie
  structurée (structured output/function calling), SQLAlchemy (lookup)
- **Output** : réponse enrichie avec une liste optionnelle de livres
  `{title, price, url, synopsis}`
- **Process** : ajouter un nœud après génération qui demande au LLM
  d'extraire les titres de livres mentionnés dans la réponse (sortie
  JSON structurée) → pour chaque titre extrait, recherche floue dans la
  table `books` du pasteur → si trouvé, ajouter à la réponse
- **Distinction avec US-28** : ce mécanisme ne remonte que des livres
  **réellement mentionnés** dans le contenu source de la réponse — donc
  factuel par construction. US-28 (Epic H) ajoute un second mécanisme,
  la suggestion thématique de livres non mentionnés, qui doit rester
  visuellement et textuellement distincte de celui-ci pour ne jamais
  laisser croire que le pasteur a cité un livre qu'il n'a pas cité

---

## Epic D — Configuration opérateur (api/, web/operator/)

### US-12 (P1) — Créer son profil pasteur via formulaire
*En tant qu'opérateur, je veux créer mon profil pasteur et renseigner
mes chaînes YouTube via un formulaire web, afin de configurer mon
instance sans toucher au code.*

- **Technos** : FastAPI (endpoints REST), un frontend simple (React ou
  même un formulaire HTML basique pour commencer), SQLAlchemy
- **Output** : endpoints `POST /pastors`, `POST /pastors/{id}/channels`
  + formulaire web fonctionnel
- **Process** : définir les schémas Pydantic (validation d'entrée) →
  écrire les routes FastAPI qui insèrent en base → construire le
  formulaire qui appelle ces routes → afficher confirmation

### US-13 (P1) — Déclencher l'ingestion depuis l'interface
*En tant qu'opérateur, je veux déclencher la découverte et l'ingestion
depuis l'interface (bouton), afin de ne pas dépendre d'un script en
ligne de commande.*

- **Technos** : FastAPI (endpoint déclencheur), Apache Airflow comme
  orchestrateur de l'exécution réelle (voir US-21, Epic G) — `BackgroundTasks`
  de FastAPI reste une option de repli minimaliste si Airflow n'est pas
  encore en place
- **Output** : endpoint `POST /pastors/{id}/ingest` qui déclenche le DAG
  d'ingestion (US-03 → US-06 → US-08) via l'API Airflow (déclenchement
  d'un DAG run)
- **Process** : encapsuler les 3 scripts existants en tâches du DAG
  Airflow (US-21) → l'endpoint appelle l'API REST d'Airflow pour
  déclencher une exécution du DAG (`dagRuns`) → mettre à jour un statut
  consultable (US-05/US-24 étendus)

### US-14 (P1) — Gérer son catalogue de livres
*En tant qu'opérateur, je veux gérer mon catalogue de livres
(ajouter/modifier titre, prix, lien, synopsis) via formulaire, afin de le
tenir à jour sans intervention technique.*

- **Technos** : FastAPI (CRUD), SQLAlchemy, frontend simple
- **Output** : endpoints `POST/PUT/DELETE /pastors/{id}/books` +
  formulaire de gestion
- **Process** : CRUD standard sur la table `books`, filtré par
  `pastor_id` à chaque opération pour garantir l'isolation multi-tenant

---

## Epic E — Accès visiteur (api/, web/visitor/)

### US-15 (P1) — Widget intégrable sur un site tiers
*En tant que pasteur/église, je veux intégrer un widget de chatbot sur
mon propre site, pointant uniquement vers mon contenu, afin d'offrir
cette expérience à mes propres visiteurs sans passer par l'app générale.*

- **Technos** : FastAPI (endpoint public restreint à un `pastor_id`
  fixe), JavaScript vanilla ou petit composant embarquable (iframe ou
  script tag), CORS configuré
- **Output** : endpoint `POST /widget/{pastor_id}/ask` + snippet
  JS/iframe à coller sur un site externe
- **Process** : créer une route publique qui fige le `pastor_id` (pas de
  sélection possible côté visiteur) → réutiliser le graphe LangGraph de
  US-09/10 avec ce seul `pastor_id` → packager un widget minimal
  (HTML/JS) prêt à intégrer

### US-16 (P1) — Choisir ses pasteurs préférés
*En tant que visiteur de l'app générale, je veux sélectionner un ou
plusieurs pasteurs préférés, afin que mes questions soient répondues en
priorité à partir de leur contenu.*

- **Technos** : FastAPI, SQLAlchemy, frontend (liste de sélection)
- **Output** : endpoint `POST /visitors/{id}/follows`, lignes insérées
  dans `visitor_pastor_follows` avec `is_explicit_preference=true`
- **Process** : lister les pasteurs `status=active` disponibles →
  formulaire de sélection multiple → insertion en base → utilisé ensuite
  comme filtre dans le retrieval (US-09)

### US-17 (P2) — Suggestions de pasteurs associés
*En tant que visiteur de l'app générale, je veux voir des suggestions de
pasteurs "associés" à mes préférés, afin de découvrir du contenu
pertinent que je ne connaissais pas.*

- **Technos** : SQL (requête de co-occurrence sur
  `visitor_pastor_follows`), potentiellement un job périodique
  (cron/Celery beat) qui précalcule les associations
- **Output** : endpoint `GET /visitors/{id}/suggested-pastors`
- **Process** : *repoussé en v2* — nécessite assez de volume dans
  `visitor_pastor_follows` pour qu'une requête de co-occurrence ("les
  visiteurs qui suivent X suivent aussi...") ait un sens statistique

### US-18 (P1) — Cas limite : aucun pasteur préféré sélectionné
*En tant que visiteur de l'app générale sans pasteur préféré
sélectionné, je veux comprendre que je dois en choisir un avant de poser
une question (ou avoir un choix par défaut clair), afin de ne pas me
retrouver bloqué sans comprendre pourquoi.*

- **Technos** : frontend (état vide géré explicitement), FastAPI
  (validation d'entrée)
- **Output** : message d'interface clair + endpoint qui refuse
  proprement une question sans `pastor_id` associé (erreur 400 explicite,
  pas un plantage silencieux)
- **Process** : décision produit à trancher (bloquant vs pasteur par
  défaut) → implémenter côté frontend (état vide) et backend (validation)

---

## Epic F — Confiance et modération (transverse)

### US-19 (P1) — Valider la légitimité d'un opérateur
*En tant qu'admin plateforme (Indira), je veux valider qu'un opérateur a
le droit de créer une instance au nom d'un pasteur, afin d'éviter une
usurpation d'identité.*

- **Technos** : FastAPI (endpoint admin protégé), SQLAlchemy (champ
  `status`), mécanisme de vérification manuel pour commencer (pas
  d'automatisation en v1)
- **Output** : endpoint `PATCH /admin/pastors/{id}/status`, pasteurs
  créés en `status=pending` jusqu'à validation manuelle
- **Process** : à la création (US-12), forcer `status=pending` → toi
  seule (accès admin) passes en `active` après vérification manuelle
  (ex: contact direct avec le pasteur) → un pasteur `pending` n'apparaît
  pas dans l'app générale ni n'est interrogeable publiquement

### US-20 (P2) — Éviter les réponses hors corpus
*En tant que visiteur, je veux que le chatbot précise clairement quand
une question sort du corpus disponible (plutôt que d'inventer une
réponse), afin de ne pas recevoir une fausse citation attribuée au
pasteur.*

- **Technos** : LangGraph (prompt engineering), LLM
- **Output** : réponse type "Je n'ai pas trouvé d'élément dans le contenu
  disponible pour répondre à cette question" quand le retrieval ne
  remonte rien de suffisamment pertinent
- **Process** : définir un seuil de pertinence sur les scores de
  similarité du retrieval → si aucun chunk ne dépasse le seuil,
  court-circuiter la génération et renvoyer le message de repli plutôt
  que de laisser le LLM générer sans base

---

## Epic G — Data Engineering & qualité du pipeline (transverse)

Cet epic ne contient pas de nouvelle fonctionnalité visible côté
utilisateur — il porte les mécanismes d'orchestration, de fiabilité et
d'observabilité **référencés depuis** les US d'ingestion (Epic B) et
d'indexation (Epic C) ci-dessus. Sans lui, le pipeline fonctionne pour
un premier test, mais ne passerait pas à l'échelle proprement (re-scans
coûteux, pas de reprise sur échec, pas de visibilité sur ce qui a
vraiment tourné).

### US-21 (P1) — Orchestrer le pipeline d'ingestion
*En tant que développeuse, je veux que le pipeline (découverte →
transcription → chunking/embeddings) soit orchestré par un outil dédié
plutôt qu'enchaîné manuellement, afin d'avoir une reprise automatique en
cas d'échec partiel et une exécution planifiée (nouveau contenu détecté
périodiquement sans action manuelle).*

- **Technos** : Apache Airflow — préféré à une alternative plus légère
  (ex: Prefect) malgré la charge d'opération plus lourde pour un projet
  solo, car c'est un standard reconnu en entreprise (orchestration de
  pipelines de données) et une compétence directement valorisable en
  candidature AI/Data Engineering
- **Output** : un DAG Airflow définissant les 3 étapes comme des tâches
  liées (`discover → transcribe → chunk_and_embed`), visible et
  relançable depuis l'UI Airflow
- **Process** : convertir `discover_videos.py`, `fetch_transcripts.py`,
  `chunk_and_embed.py` en tâches Airflow (`PythonOperator` ou `@task`
  avec l'API TaskFlow) → les assembler dans un DAG avec dépendances
  explicites entre elles → configurer des retries automatiques en cas
  d'échec sur une tâche → programmer une exécution planifiée (ex:
  quotidienne) par pasteur actif via un `schedule_interval`

### US-22 (P1) — Ingestion incrémentale et idempotence
*En tant que système, je veux ne retraiter que les vidéos réellement
nouvelles à chaque exécution du pipeline, afin d'éviter de re-scanner,
re-transcrire et ré-embedder du contenu déjà traité (coût API et temps
inutiles).*

- **Technos** : Python, SQLAlchemy (requêtes d'exclusion sur `video_id`
  déjà connus)
- **Output** : logique réutilisée par US-03/US-06/US-08 qui vérifie
  l'existant avant de traiter, `last_scanned_at` sur `channels` tenu à
  jour
- **Process** : avant d'insérer une vidéo découverte, vérifier si son
  `video_id` existe déjà en base → ne la retraiter que si absente (ou si
  un indicateur de changement le justifie) → même logique pour les
  transcripts déjà `fetched` et les chunks déjà générés → mettre à jour
  `last_scanned_at` en fin de traitement

### US-23 (P2) — Qualité et validation des données ingérées
*En tant que système, je veux valider la qualité des données à chaque
étape du pipeline (transcript vide, chunk mal formé, timestamps
incohérents), afin de ne pas polluer l'index de recherche avec du
contenu inexploitable ou corrompu.*

- **Technos** : Python (fonctions de validation simples ; un outil dédié
  type Great Expectations serait disproportionné pour ce volume de
  données)
- **Output** : fonctions `validate_transcript()` et `validate_chunk()`
  appelées avant insertion dans US-06/US-08, rejets loggués plutôt que
  silencieux
- **Process** : définir les règles de validation (transcript non vide,
  longueur minimale, `start_seconds < end_seconds`, pas de doublon exact
  de texte) → les appliquer avant chaque insertion → logger les rejets
  avec la raison, sans faire planter tout le pipeline pour une seule
  vidéo problématique

### US-24 (P2) — Monitoring et observabilité du pipeline
*En tant qu'opérateur ou admin plateforme, je veux voir des métriques
claires sur l'état du pipeline (nombre de vidéos traitées, taux
d'échec, temps d'exécution), afin de détecter rapidement un problème
sans avoir à lire des logs bruts.*

- **Technos** : logs structurés Python (`structlog` ou `logging` avec
  formattage JSON), l'UI native d'Airflow (US-21) pour une première
  visibilité, un tableau de bord dédié seulement si le besoin dépasse ce
  qu'Airflow offre déjà
- **Output** : logs structurés exploitables (par pasteur, par étape,
  avec statut/durée), écran de suivi étendu (US-05/US-07) alimenté par
  ces métriques
- **Process** : remplacer les `print()` actuels par des logs structurés
  avec contexte (`pastor_id`, étape, statut) → exploiter les métriques
  déjà exposées par Airflow pour les exécutions de DAG → étendre
  l'endpoint de stats (US-05) avec taux d'échec et durée moyenne par
  étape

### US-34 (P0) — Purge automatique des données sensibles (prayer_signals, human_contact_requests)
*En tant qu'admin plateforme, je veux que les données des tables
`prayer_signals` et `human_contact_requests` soient automatiquement
purgées/anonymisées selon une politique de rétention définie, afin de
respecter le principe de minimisation du RGPD sans dépendre d'une action
manuelle qui pourrait être oubliée.*

- **Technos** : Airflow (DAG planifié quotidien, cohérent avec US-21),
  SQLAlchemy
- **Output** : un DAG `purge_sensitive_data` qui applique la politique de
  rétention documentée dans `DATA_MODEL.md` (§8bis/§8ter, note RGPD) —
  clôture automatique des demandes non traitées après le délai défini,
  puis suppression/anonymisation après le délai de rétention post-clôture
- **Process** : requêter `prayer_signals` avec `status='new'` et
  `created_at` au-delà du seuil d'inactivité → les faire passer à un état
  clos → requêter les lignes closes depuis plus de 30 jours → les
  supprimer → même logique pour `human_contact_requests` avec ses propres
  seuils (7 jours d'inactivité, 14 jours avant anonymisation des champs
  identifiants) → logger chaque purge (nombre de lignes traitées) pour
  audit, sans jamais logger le contenu supprimé lui-même
- **Priorité P0** : contrairement au reste de l'Epic G (plutôt P1/P2, un
  raffinement), cette story est bloquante avant toute mise en production
  avec de vrais visiteurs — stocker indéfiniment des données de détresse
  ou des coordonnées de contact sans purge serait un manquement RGPD
  direct, pas juste une amélioration différable.

---

## Epic H — Synthèse multi-sources (agent/)

Fait évoluer l'agent d'un modèle "une recherche → une génération" (US-09,
suffisant pour une question ponctuelle sur un extrait précis) vers une
vraie synthèse capable de croiser plusieurs vidéos — et, dans une mesure
strictement encadrée, le catalogue de livres — pour répondre à des
questions plus larges (ex: "qu'enseigne le pasteur sur le pardon, à
travers ses différentes prédications ?").

### US-26 (P1) — Décomposer une question complexe en sous-requêtes
*En tant que système, je veux décomposer une question large en
plusieurs sous-questions ciblées avant de chercher, afin de couvrir
différents angles du sujet plutôt qu'une seule recherche vectorielle
généraliste qui manquerait des enseignements pertinents mais formulés
différemment.*

- **Technos** : LangGraph (nœud de planification), LLM avec sortie
  structurée pour générer 2-4 sous-requêtes
- **Output** : liste de sous-requêtes utilisées pour autant de recherches
  FAISS séparées ; une question simple ne génère qu'une seule sous-requête
  (= la question elle-même), pour ne pas complexifier inutilement les cas
  simples déjà couverts par US-09
- **Process** : le LLM évalue si la question porte sur un sujet précis
  déjà bien circonscrit ou sur un thème large → si large, génère 2-4
  reformulations/angles complémentaires → chaque sous-requête déclenche
  sa propre recherche dans US-27

### US-27 (P0) — Synthétiser une réponse à partir de plusieurs vidéos
*En tant que visiteur, je veux qu'une question large obtienne une
réponse qui rassemble les enseignements pertinents de plusieurs vidéos,
avec une source distincte citée pour chaque point, afin d'avoir une vue
complète plutôt qu'un unique extrait isolé.*

- **Technos** : LangGraph, FAISS (une recherche par sous-requête de
  US-26), LLM pour la synthèse finale
- **Output** : réponse unifiée où chaque affirmation reste reliée à sa
  vidéo/timestamp source (extension du format de citation de US-10 à
  plusieurs sources simultanées)
- **Process** : exécuter une recherche FAISS par sous-requête, filtrée
  par pasteur(s) (préférés + associés si applicable, cf. spec §5b) →
  dédupliquer les chunks qui se recoupent entre sous-requêtes → fournir
  l'ensemble au LLM avec instruction explicite de ne pas fusionner des
  enseignements distincts comme s'ils provenaient d'un seul passage, et
  de ne pas inventer de lien logique entre deux vidéos non lié dans le
  contenu réel → chaque affirmation de la réponse finale doit rester
  traçable à au moins un chunk récupéré (même exigence de fondement que
  US-20, étendue au cas multi-sources)

### US-28 (P2) — Suggestion thématique de livres du catalogue
*En tant que visiteur, je veux que la réponse puisse aussi signaler un
livre du catalogue en lien avec le thème de ma question, même si ce
livre n'est pas explicitement cité dans les vidéos utilisées, afin de
découvrir des ressources pertinentes du pasteur.*

- **Technos** : même modèle d'embedding que pour les chunks vidéo
  (cohérence), appliqué au titre + synopsis de chaque livre ; recherche
  de similarité simple (le volume par pasteur est trop faible pour
  justifier un index FAISS dédié — une comparaison cosinus directe sur
  les quelques dizaines d'entrées suffit)
- **Output** : au maximum 1-2 suggestions de livres par réponse, dans un
  bloc **explicitement distinct** de l'enrichissement factuel de US-11
- **Process** : embedder la question (déjà calculé pour la recherche
  principale) → comparer à l'embedding titre+synopsis de chaque livre du
  catalogue du/des pasteur(s) concerné(s) → au-dessus d'un seuil de
  pertinence, inclure en suggestion, plafonnée à 1-2 pour éviter l'effet
  spam
- **Note de conception — distinction stricte avec US-11** : cette
  suggestion doit **toujours** être formulée comme thématique ("ce livre
  aborde un sujet proche"), **jamais** comme une citation du pasteur
  ("le pasteur recommande ce livre" ou "dans ce livre, il explique...")
  — cette dernière formulation n'est légitime que si le livre est
  réellement mentionné dans le contenu source utilisé (cas US-11). Un
  visiteur doit pouvoir distinguer immédiatement, à la lecture, ce qui
  vient d'un enseignement réel de ce qui est une suggestion thématique
  générée. C'est la même exigence de non-attribution trompeuse que celle
  qui a fait écarter le profil de style par pasteur (voir SPECS.md §6).

---

## Epic I — Mode général & interaction conversationnelle (agent/, api/)

Ajoute un troisième mode d'accès (spec §5c) : répondre à des questions de
fond sans sélection préalable de pasteur, en s'appuyant sur l'ensemble
des pasteurs actifs, avec suivi conversationnel et des garde-fous
renforcés pour les sujets sensibles.

### US-29 (P1) — Mode général sans pasteur sélectionné
*En tant que visiteur, je veux pouvoir poser une question de fond (ex:
"comment prier ?") sans avoir à choisir un pasteur au préalable, afin
d'obtenir une réponse construite à partir de l'ensemble des enseignements
disponibles sur la plateforme.*

- **Technos** : réutilise l'architecture de synthèse multi-sources
  (US-26/US-27, Epic H), sans filtre `pastor_id` — recherche sur tous les
  pasteurs `status=active`
- **Output** : réponse synthétisée à partir de plusieurs pasteurs, chaque
  point explicitement attribué au pasteur dont il provient (nom affiché,
  pas juste un lien vidéo générique)
- **Process** : exécuter la recherche multi-sources de US-27 sans filtre
  pasteur → regrouper les chunks récupérés par pasteur d'origine → générer
  la réponse avec instruction explicite d'attribution nommée par pasteur
  pour chaque point → si deux pasteurs expriment des positions
  divergentes sur le même point, le signaler explicitement plutôt que de
  n'en retenir qu'une ou de les fondre
- **Note de conception** : ne jamais présenter une position comme le
  consensus chrétien général à partir du contenu d'un ou deux pasteurs
  seulement — la diversité de courants (spec §5c) doit rester visible

### US-30 (P1) — Interaction conversationnelle (suivi multi-tour)
*En tant que visiteur, je veux pouvoir poser des questions de suivi dans
la continuité de l'échange, et que le système me demande une précision
si ma question est trop large, afin d'avoir un vrai dialogue plutôt
qu'une suite de questions isolées sans mémoire.*

- **Technos** : LangGraph (state/mémoire de session), historique de
  conversation court terme (le temps de la session, pas nécessairement
  persisté au-delà sauf si rattaché à un `Visitor` déjà identifié, cf.
  US-16)
- **Output** : le contexte des échanges précédents de la session est pris
  en compte dans la réponse suivante ; pour une question trop large ou
  ambiguë, l'agent peut poser une question de clarification avant de
  chercher, plutôt que de répondre à côté
- **Process** : conserver les N derniers échanges de la session comme
  contexte → les injecter dans le graphe LangGraph pour chaque nouvelle
  question → ajouter un nœud de clarification optionnel, déclenché quand
  la question est jugée trop large pour une recherche ciblée, qui pose
  une question de suivi avant de lancer le retrieval

### US-31 (P1) — Garde-fous pour les sujets sensibles (santé mentale, détresse)
*En tant que visiteur traversant une difficulté réelle (ex: dépression),
je veux que la réponse m'oriente aussi vers un accompagnement humain
réel, professionnel ou communautaire, en plus de l'enseignement
spirituel, afin de ne jamais traiter un outil IA comme un substitut
suffisant à un vrai accompagnement.*

- **Technos** : instructions de sécurité au niveau du prompt
  (`agent/prompts.py`), classification légère de la question (mots-clés
  ou appel LLM dédié) pour détecter les sujets sensibles avant génération
- **Output** : pour toute question touchant à la santé mentale ou à une
  détresse exprimée, la réponse inclut systématiquement une invitation
  claire à un accompagnement professionnel et/ou communautaire réel — en
  complément du contenu spirituel, jamais à sa place
- **Process** : classifier chaque question entrante pour détecter un
  sujet sensible ou des signaux de détresse → si détecté, adapter le
  prompt de génération pour cette réponse afin d'exiger l'orientation
  vers un accompagnement réel, en plus du contenu issu des enseignements
  → ne jamais formuler de conseil à portée clinique (diagnostic,
  traitement) à partir du contenu des vidéos, même si un pasteur en a
  parlé dans ce sens dans une vidéo source
- **Note de conception** : ce garde-fou est non négociable et prioritaire
  sur la fidélité au contenu source — si une vidéo source contient un
  conseil qui ressemblerait à un avis clinique, la synthèse ne le
  reproduit pas tel quel, elle recentre sur l'encouragement spirituel et
  l'orientation vers un accompagnement réel

### US-32 (P1) — Signalement de prière (opt-in, anonyme par défaut)
*En tant que visiteur traversant une difficulté, je veux pouvoir demander,
par une action volontaire et explicite, qu'on prie pour moi, de façon
anonyme par défaut, afin de recevoir un soutien réel sans avoir à
dévoiler mon identité si je ne le souhaite pas.*

- **Technos** : FastAPI (endpoint dédié à l'action opt-in), SQLAlchemy,
  un mécanisme de notification simple vers `pastoral_team_contact_email`
  (envoi d'email — pas de nouvelle dépendance lourde nécessaire pour un
  volume de signalements attendu comme faible)
- **Output** : un bouton "Prier pour moi" affiché à la fin d'une réponse
  sur un sujet sensible (déclenché par la même classification que
  US-31) → au clic, un court écran demande si la personne veut ajouter
  son prénom et/ou un mot libre (les deux optionnels) avant confirmation
  → à la confirmation, une ligne `prayer_signals` est créée et l'équipe
  pastorale est notifiée
- **Process** : afficher le bouton uniquement si `pastoral_team_contact_email`
  est renseigné pour ce pasteur (sinon la fonctionnalité reste invisible)
  → au clic, afficher l'écran de consentement avec les champs optionnels
  **et mentionner explicitement les deux destinataires** (équipe du
  pasteur + équipe support ePastor, voir note RGPD `DATA_MODEL.md` §8bis)
  → à la confirmation explicite, créer la ligne `prayer_signals` →
  notifier les deux équipes par email

### US-33 (P1) — Mise en relation avec un accompagnement humain (détresse ou besoin matériel)
*En tant que visiteur traversant une difficulté — émotionnelle,
spirituelle, ou matérielle (logement, situation administrative,
difficulté financière) — je veux pouvoir demander à être recontacté(e)
par quelqu'un de l'équipe du pasteur, en fournissant volontairement mes
coordonnées, afin d'obtenir un accompagnement humain réel au-delà de la
réponse du chatbot.*

- **Technos** : FastAPI, SQLAlchemy, même mécanisme de notification que
  US-32, avec un accès restreint renforcé sur cette table (données
  identifiantes)
- **Output** : un second bouton, distinct de US-32 ("Être recontacté(e)
  par quelqu'un de l'équipe"), affiché à la fin d'une réponse sur un
  sujet sensible **ou touchant à un besoin matériel** → un écran de
  consentement explicite précisant qui va recontacter la personne
  (équipe du pasteur + équipe support ePastor), avec quelles
  coordonnées, et pourquoi → sélection d'une catégorie de besoin
  (spirituel/émotionnel, logement, financier, administratif, autre) →
  à la confirmation, une ligne `human_contact_requests` est créée
- **Process** : afficher le bouton dans les mêmes conditions que US-32,
  étendues aux réponses touchant un besoin matériel exprimé (pas
  seulement la détresse émotionnelle de US-31) → au clic, écran de
  consentement explicite (texte clair, pas de case pré-cochée, double
  destinataire nommé) demandant le prénom (optionnel), la catégorie de
  besoin, le moyen de contact préféré et la coordonnée elle-même
  (obligatoires pour que la demande ait un sens) → à la confirmation,
  créer la ligne → notifier les deux équipes
- **Note de conception** : distincte de US-32 par nature — ici la
  personne fournit une donnée identifiante dans un contexte de détresse
  ou de besoin réel, ce qui demande le niveau de consentement le plus
  explicite du produit. Ne jamais fusionner ce formulaire avec celui de
  US-32 ni pré-remplir l'un à partir de l'autre.

---

## Proposition de séquencement pour démarrer

Pour un premier bout-à-bout fonctionnel (même basique, en CLI/scripts,
sans formulaire ni recommandation) : **US-01 → US-02 → US-03 → US-04 →
US-06 → US-08 → US-09 → US-10**.

Ça couvre : base de données → un pasteur de test en base → découverte
filtrée → transcription → indexation → question/réponse sourcée. Tout
le reste (formulaire, widget, recommandation) vient après que ce cœur
fonctionne sur le cas Sanogo.

**Sur le Data Engineering (Epic G)** : pas nécessaire pour ce premier
bout-à-bout avec un seul pasteur test — US-22 (incrémental) et US-23
(qualité) apportent de la valeur dès que tu ré-exécutes le pipeline
plusieurs fois ; US-21 (orchestration) et US-24 (monitoring) prennent
tout leur sens quand il y a plusieurs pasteurs et une exécution
récurrente, pas avant.
