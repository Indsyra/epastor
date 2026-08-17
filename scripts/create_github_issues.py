"""
Crée automatiquement une Issue GitHub par User Story, à partir de
docs/USER_STORIES.md — ce fichier reste la source de vérité, le script
ne fait que la parser puis appeler l'API GitHub.

Prérequis :
    pip install requests

Variables d'environnement à définir avant de lancer :
    GITHUB_TOKEN   token d'accès personnel (scope "repo")
                   → https://github.com/settings/tokens
    GITHUB_REPO    "ton-user/epastor" (owner/repo)

Usage :
    export GITHUB_TOKEN=ghp_xxx
    export GITHUB_REPO=indira/epastor
    python scripts/create_github_issues.py --dry-run   # aperçu sans rien créer
    python scripts/create_github_issues.py              # création réelle
"""
import argparse
import os
import re
import sys
from pathlib import Path

import requests

US_MD_PATH = Path(__file__).resolve().parents[1] / "docs" / "USER_STORIES.md"
API_BASE = "https://api.github.com"

# Labels utilisés — créés automatiquement s'ils n'existent pas encore.
PRIORITY_COLORS = {"P0": "d73a4a", "P1": "fbca04", "P2": "0e8a16"}
EPIC_COLOR = "5319e7"


def extract_subtasks(body: str) -> list[str]:
    """
    Repère le paragraphe '- **Process** : ...' de chaque US — qui peut
    s'étendre sur plusieurs lignes wrappées jusqu'à la ligne vide
    suivante — le rejoint en un seul bloc de texte, puis découpe sur les
    flèches '→' pour en faire une liste d'étapes. Chaque étape devient
    une sous-tâche (case à cocher GitHub).
    """
    lines = body.splitlines()
    process_lines = []
    capturing = False

    for line in lines:
        if line.strip().startswith("- **Process**"):
            capturing = True
            # Retire le préfixe "- **Process** : " de la première ligne
            first = re.sub(r"^- \*\*Process\*\*\s*:\s*", "", line.strip())
            process_lines.append(first)
            continue
        if capturing:
            if line.strip() == "":
                break  # fin du paragraphe
            process_lines.append(line.strip())

    if not process_lines:
        return []

    process_text = " ".join(process_lines)
    steps = [s.strip(" .") for s in process_text.split("→")]
    steps = [s for s in steps if s]
    return steps


def parse_user_stories(md_text: str) -> list[dict]:
    """
    Découpe le markdown en une liste de user stories.
    Repère les epics via "## Epic X — Nom" et les US via
    "### US-XX (Pn) — Titre".
    """
    stories = []
    current_epic = None

    # On découpe le fichier en blocs sur chaque "## " ou "### "
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        epic_match = re.match(r"^## Epic .+ — (.+)$", line)
        if epic_match:
            # Nettoie le nom pour en faire un label GitHub lisible
            # (retire le chemin technique entre parenthèses, ex: "(db/)")
            raw = epic_match.group(1).strip()
            current_epic = re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip()
            i += 1
            continue

        us_match = re.match(r"^### (US-\d+) \((P\d)\) — (.+)$", line)
        if us_match:
            us_id, priority, title = us_match.groups()
            body_lines = []
            i += 1
            # Accumule jusqu'au prochain "### " ou "## " (ou fin de fichier)
            while i < len(lines) and not lines[i].startswith("### ") and not lines[i].startswith("## "):
                body_lines.append(lines[i])
                i += 1
            body = "\n".join(body_lines).strip()
            subtasks = extract_subtasks(body)
            stories.append({
                "id": us_id,
                "priority": priority,
                "title": title.strip(),
                "epic": current_epic,
                "body": body,
                "subtasks": subtasks,
            })
            continue

        i += 1

    return stories


def ensure_label(repo: str, headers: dict, name: str, color: str, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] label assuré: {name}")
        return
    resp = requests.post(
        f"{API_BASE}/repos/{repo}/labels",
        headers=headers,
        json={"name": name, "color": color},
    )
    # 201 = créé, 422 = existe déjà -> les deux sont OK ici
    if resp.status_code not in (201, 422):
        print(f"  ⚠️  Erreur création label '{name}': {resp.status_code} {resp.text}", file=sys.stderr)


def build_issue_body(story: dict) -> str:
    """
    Assemble le corps final de l'issue : la description de la US telle
    quelle, suivie d'une checklist de sous-tâches dérivée de sa section
    Process (une étape 'a → b → c' devient trois cases à cocher).
    """
    body = story["body"]
    if not story["subtasks"]:
        return body

    checklist = "\n".join(f"- [ ] {step}" for step in story["subtasks"])
    return f"{body}\n\n**Sous-tâches**\n{checklist}"


def list_existing_issues(repo: str, headers: dict) -> dict[str, int]:
    """
    Récupère toutes les issues déjà présentes sur le repo (ouvertes et
    fermées) et construit un mapping {us_id: numéro_issue}, basé sur le
    préfixe "US-XX:" en début de titre.

    On matche sur le préfixe plutôt que le titre complet : si le libellé
    d'une US change dans USER_STORIES.md mais que son id reste le même,
    on doit quand même retrouver l'issue existante pour la mettre à jour
    (et non en créer une deuxième).
    """
    existing = {}
    page = 1
    while True:
        resp = requests.get(
            f"{API_BASE}/repos/{repo}/issues",
            headers=headers,
            params={"state": "all", "per_page": 100, "page": page},
        )
        if resp.status_code != 200:
            print(f"  ⚠️  Erreur en listant les issues: {resp.status_code} {resp.text}", file=sys.stderr)
            break

        batch = resp.json()
        if not batch:
            break

        for issue in batch:
            if "pull_request" in issue:
                continue  # les PR apparaissent aussi dans cet endpoint, on les ignore
            match = re.match(r"^(US-\d+):", issue["title"])
            if match:
                existing[match.group(1)] = issue["number"]

        page += 1

    return existing


def upsert_issue(repo: str, headers: dict, story: dict, existing: dict[str, int], dry_run: bool):
    title = f"{story['id']}: {story['title']}"
    labels = [story["priority"]]
    if story["epic"]:
        labels.append(story["epic"])
    body = build_issue_body(story)

    issue_number = existing.get(story["id"])

    if dry_run:
        action = f"mise à jour de #{issue_number}" if issue_number else "création"
        print(f"  [dry-run] {action}: {title}  (labels: {labels}, {len(story['subtasks'])} sous-tâches)")
        for step in story["subtasks"]:
            print(f"      - [ ] {step}")
        return

    if issue_number:
        resp = requests.patch(
            f"{API_BASE}/repos/{repo}/issues/{issue_number}",
            headers=headers,
            json={"title": title, "body": body, "labels": labels},
        )
        if resp.status_code == 200:
            print(f"  🔄 mise à jour: {title} -> {resp.json()['html_url']}")
        else:
            print(f"  ⚠️  Échec mise à jour '{title}': {resp.status_code} {resp.text}", file=sys.stderr)
    else:
        resp = requests.post(
            f"{API_BASE}/repos/{repo}/issues",
            headers=headers,
            json={"title": title, "body": body, "labels": labels},
        )
        if resp.status_code == 201:
            print(f"  ✅ créée: {title} -> {resp.json()['html_url']}")
        else:
            print(f"  ⚠️  Échec création '{title}': {resp.status_code} {resp.text}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Aperçu sans rien créer sur GitHub")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")

    if not args.dry_run and (not token or not repo):
        print("❌ GITHUB_TOKEN et GITHUB_REPO doivent être définis (sauf en --dry-run).", file=sys.stderr)
        sys.exit(1)

    if not US_MD_PATH.exists():
        print(f"❌ Fichier introuvable: {US_MD_PATH}", file=sys.stderr)
        sys.exit(1)

    md_text = US_MD_PATH.read_text(encoding="utf-8")
    stories = parse_user_stories(md_text)
    print(f"📋 {len(stories)} user stories trouvées dans {US_MD_PATH.name}\n")

    headers = {
        "Authorization": f"Bearer {token}" if token else "",
        "Accept": "application/vnd.github+json",
    }

    if not args.dry_run:
        print("🏷️  Vérification des labels...")
        for p, color in PRIORITY_COLORS.items():
            ensure_label(repo, headers, p, color, args.dry_run)
        epics = {s["epic"] for s in stories if s["epic"]}
        for epic in epics:
            ensure_label(repo, headers, epic, EPIC_COLOR, args.dry_run)
        print()

    print("🔍 Recherche des issues déjà existantes...")
    existing = {} if args.dry_run else list_existing_issues(repo, headers)
    if existing:
        print(f"   {len(existing)} US déjà présentes sur le repo -> seront mises à jour")
    print()

    print("📝 Création / mise à jour des issues...")
    for story in stories:
        upsert_issue(repo, headers, story, existing, args.dry_run)


if __name__ == "__main__":
    main()
