# ePastor — Specs v1

## 1. Vision

Une plateforme à deux faces :

- **Côté opérateur** : tout pasteur/serviteur/église peut créer une instance
  configurée sur son propre contenu YouTube (et plus tard livres), via un
  formulaire web — sans toucher au code.
- **Côté public** : n'importe quel visiteur pose une question en langage
  naturel et reçoit une réponse sourcée (vidéo + timestamp), avec un renvoi
  vers un livre du catalogue si pertinent.

## 2. Utilisateurs cibles

| Rôle | Qui | Besoin |
|---|---|---|
| Opérateur | Pasteur, apôtre, église, ministère | Configurer son instance sans coder |
| Visiteur | Toute personne cherchant une réponse | Poser une question, obtenir une réponse sourcée et fiable |
| (Toi) Admin plateforme | Indira | Superviser les instances, gérer l'infra partagée |

## 3. Décisions d'architecture actées

- **Multi-tenant, base unique** avec `tenant_id` sur chaque donnée
  (transcript, chunk, vecteur, catalogue livre). Une seule base à faire
  évoluer, quel que soit le nombre de pasteurs.
- **Config via interface web**, pas de fichier YAML à éditer à la main
  (le `config.py` actuel devient une donnée en base, pas du code).
- Le moteur de traitement (découverte vidéo, transcription, chunking,
  RAG) est **le même pour toutes les instances** — seule la config change.

## 4. Ce qu'une instance (tenant = un pasteur) contient

- `tenant_id`, **nom du pasteur** (c'est l'identité publique, pas la chaîne
  YouTube — celle-ci reste un détail technique en interne), nom de
  l'église/ministère (optionnel)
- Une ou plusieurs chaînes YouTube rattachées à ce pasteur, chacune avec :
  - `requires_speaker_filter: bool` (chaîne perso vs chaîne multi-orateurs)
  - mots-clés de reconnaissance (nom, variantes) si filtre activé
- Un catalogue livres optionnel (peut être vide au départ)
- Langue(s) de contenu prioritaire(s)

## 4bis. Ce que le profil d'un visiteur contient (app générale uniquement)

- `visitor_id` (anonyme ou compte, à trancher plus tard)
- Liste de `tenant_id` (pasteurs) marqués "préféré"
- Historique implicite (quels pasteurs consultés, même sans marquage explicite)
  — c'est ce signal qui alimente la recommandation "pasteurs associés"

## 5. Deux parcours visiteur distincts

Il y a deux façons d'accéder à ePastor, avec un modèle différent à chaque fois :

### 5a. Intégration à un site web (widget dédié)
Un pasteur/église intègre le chatbot sur son propre site. Dans ce cas :
- L'instance est **fixe et unique** (celle du pasteur propriétaire du site)
- Pas de sélection de pasteurs, pas de recommandations d'autres pasteurs
- Le visiteur ne sait même pas qu'ePastor existe en tant que plateforme —
  c'est transparent, intégré à l'expérience du site

### 5b. Application ePastor générale (point d'entrée unique)
Le visiteur arrive sur l'app ePastor elle-même. Dans ce cas :
- Il choisit un ou plusieurs **pasteurs préférés** (pas des chaînes YouTube —
  la notion de "chaîne" reste un détail d'implémentation invisible pour lui)
- L'app lui suggère **2-3 pasteurs "associés"**, déterminés par recommandation
  collaborative : les pasteurs les plus souvent suivis par les visiteurs qui
  suivent déjà ses pasteurs préférés (logique proche de "les gens qui aiment
  X aiment aussi Y")
- Quand il pose une question, la réponse pioche dans **préférés + associés**,
  avec une **priorité donnée aux préférés** (ex: retrieval pondéré, ou sources
  préférées citées en premier)

### Opérateur (commun aux deux parcours)
1. Crée un compte / une instance via formulaire
2. Renseigne : son nom, une ou plusieurs chaînes YouTube, mots-clés si besoin
   de filtrage par intervenant
3. Lance la découverte + ingestion (bouton, pas de CLI)
4. Voit un état d'avancement (X vidéos trouvées, Y retenues, Z transcrites)
5. Obtient :
   - un lien/widget d'intégration pour son propre site (5a)
   - une visibilité automatique dans l'app générale (5b), sujette à
     recommandation une fois qu'il y a assez de visiteurs pour ça

### Le problème du "cold start" (à garder en tête, pas à résoudre maintenant)
La recommandation "pasteurs associés" a besoin de données de visiteurs
existantes pour fonctionner. Avec un seul pasteur (Sanogo) en v1, il n'y a
pas encore assez de signal. À traiter en v2 — voir section 7.

## 6. Hors périmètre v1 (explicitement exclu pour l'instant)

- Ingestion de livres en texte intégral (droits d'auteur — voir décision antérieure)
- Authentification avancée / paiement / plans payants
- Modération de contenu par l'opérateur (édition manuelle des réponses)
- Support d'autres plateformes que YouTube (podcasts, Facebook, etc.)
- Instance isolée par pasteur (tranché : base unique dès la v1)
- Le moteur de recommandation "pasteurs associés" par co-occurrence réelle
  (nécessite un volume de visiteurs qu'on n'aura pas en v1 avec un seul
  pasteur) — la structure de données (4bis) est prévue dès la v1, mais le
  calcul algorithmique est repoussé à une v2, quand il y aura plusieurs
  pasteurs et assez de trafic pour que ça ait un sens

## 7. Questions encore ouvertes

- [x] ~~Le visiteur choisit-il une instance explicitement...~~ → Tranché :
      deux parcours (5a intégration = instance fixe, 5b app générale =
      pasteurs préférés + associés)
- [ ] Qui valide qu'un opérateur est légitime (empêcher qu'on crée une
      instance au nom de quelqu'un d'autre sans autorisation) ?
- [ ] Fréquence de mise à jour du contenu (nouvelle vidéo publiée → délai
      avant qu'elle soit interrogeable) ?
- [ ] Modèle économique — gratuit / payant / limité en usage ? → Hors
      périmètre v1 (voir section 6)
- [ ] **Cold start recommandation** : comment suggérer des "pasteurs
      associés" avant d'avoir assez de visiteurs pour calculer des
      co-occurrences ? (fallback possible : associations manuelles au
      départ, bascule vers l'algo une fois assez de données — à traiter
      en v2, pas bloquant pour la v1 avec un seul pasteur)
- [ ] Comment pondérer concrètement "préférés" vs "associés" dans le
      retrieval (score boosté ? sources associées seulement si les
      préférés ne suffisent pas à répondre ? affichage différencié dans
      la réponse) ?

## 8. Cible concrète pour valider la v1

Sanogo reste le premier cas réel utilisé pour construire et tester le
pipeline (découverte multi-chaînes + filtrage par intervenant + catalogue
livres), car il couvre le cas le plus complexe. Une fois validé sur lui,
le même moteur doit fonctionner pour un cas plus simple (un seul orateur,
pas de catalogue) sans changement de code — seulement de config.
