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
  actuel), une ligne par vidéo découverte
- **Process** : lire les `channels` d'un pasteur depuis la base (plus
  depuis `config.py`) → appeler `yt-dlp` en mode `extract_flat` par
  chaîne → mapper chaque résultat vers le modèle `Video` → insérer en
  base avec `channel_id`/`pastor_id`

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

- **Technos** : FastAPI (endpoint déclencheur), une file de tâches en
  arrière-plan (Celery + Redis, ou plus simple : `BackgroundTasks` de
  FastAPI pour la v1 vu le faible volume)
- **Output** : endpoint `POST /pastors/{id}/ingest` qui lance US-03 →
  US-06 → US-08 en séquence, en tâche de fond
- **Process** : encapsuler les 3 scripts existants en fonctions
  appelables → les chaîner dans une tâche de fond déclenchée par
  l'endpoint → mettre à jour un statut consultable (US-05 étendu)

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

## Proposition de séquencement pour démarrer

Pour un premier bout-à-bout fonctionnel (même basique, en CLI/scripts,
sans formulaire ni recommandation) : **US-01 → US-02 → US-03 → US-04 →
US-06 → US-08 → US-09 → US-10**.

Ça couvre : base de données → un pasteur de test en base → découverte
filtrée → transcription → indexation → question/réponse sourcée. Tout
le reste (formulaire, widget, recommandation) vient après que ce cœur
fonctionne sur le cas Sanogo.
