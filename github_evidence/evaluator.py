
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path

from app.github_evidence.models import (
    GitHubEvidenceResult,
    RepositoryEvidence,
)


MAX_REPOSITORIES = 3
MAX_FILES_PER_REPOSITORY = 15
MAX_FILE_BYTES = 100_000
CACHE_TTL_SECONDS = 24 * 60 * 60

CACHE_PATH = (
    Path(__file__).resolve().parent / "cache.json"
)

# Technology aliases are used to locate evidence in source code.
# A match is only a signal, not proof of professional proficiency.
SKILL_ALIASES = {
    "java": [r"\bjava\b", r"\.java\b"],
    "springboot": [
        r"\bspring\s*boot\b",
        r"\bspring-boot\b",
        r"@SpringBootApplication",
        r"@RestController",
    ],
    "react": [
        r"\breact\b",
        r"\buseState\b",
        r"\buseEffect\b",
        r"\bjsx\b",
        r"\btsx\b",
    ],
    "python": [r"\bpython\b", r"\.py\b"],
    "fastapi": [
        r"\bfastapi\b",
        r"\bFastAPI\s*\(",
        r"@app\.(get|post|put|delete|patch)\b",
    ],
    "typescript": [r"\btypescript\b", r"\.tsx?\b"],
    "javascript": [
        r"\bjavascript\b",
        r"\.jsx?\b",
        r"\bconst\b",
        r"\bfunction\b",
    ],
    "mysql": [
        r"\bmysql\b",
        r"\bCREATE TABLE\b",
        r"\bSELECT\b.*\bFROM\b",
    ],
    "docker": [
        r"\bDockerfile\b",
        r"\bFROM\s+\w+",
        r"\bdocker-compose\b",
    ],
    "git": [r"\bgit\b", r"\.gitignore\b"],
}


# Source and configuration files only. Avoid binary files and
# unrelated generated output.
ALLOWED_SUFFIXES = {
    ".java", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".sql", ".yml", ".yaml", ".json", ".toml",
    ".xml", ".properties", ".sh", ".dockerfile",
}

PRIORITY_NAMES = {
    "package.json",
    "pom.xml",
    "requirements.txt",
    "pyproject.toml",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "application.properties",
    "application.yml"
    "main.py",
}


class GitHubEvaluationError(Exception):
    """GitHub evidence could not be evaluated reliably."""


def _load_cache():
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = CACHE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(cache, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(CACHE_PATH)



def _github_get(path, token):
    url = "https://api.github.com" + path
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Recruitment-GitHub-Evidence",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining == "0":
                reset_at = response.headers.get("X-RateLimit-Reset")
                if reset_at:
                    raise GitHubEvaluationError(
                        "GitHub API quota is exhausted. "
                        f"Rate limit resets at Unix timestamp {reset_at}."
                    )

            return data

    except urllib.error.HTTPError as exc:
        remaining = exc.headers.get("X-RateLimit-Remaining")
        reset_at = exc.headers.get("X-RateLimit-Reset")
        retry_after = exc.headers.get("Retry-After")

        if exc.code == 401:
            raise GitHubEvaluationError(
                "GitHub authentication failed. Check the configured token."
            ) from exc

        if exc.code in (403, 429):
            details = "GitHub API rate limit or permission restriction."
            if remaining == "0" and reset_at:
                details += f" Rate limit resets at Unix timestamp {reset_at}."
            elif retry_after:
                details += f" Retry after {retry_after} seconds."
            raise GitHubEvaluationError(details) from exc

        if exc.code == 404:
            raise GitHubEvaluationError(
                "Repository or requested GitHub resource was not found "
                "or is not accessible."
            ) from exc

        raise GitHubEvaluationError(
            f"GitHub API request failed (HTTP {exc.code})."
        ) from exc

    except (urllib.error.URLError, TimeoutError) as exc:
        raise GitHubEvaluationError(
            "Could not reach GitHub API."
        ) from exc



def _normalize_skill(skill):
    value = re.sub(r"[^a-z0-9+#.]", "", str(skill).lower())
    return value


def _patterns_for_skill(skill):
    normalized = _normalize_skill(skill)
    aliases = SKILL_ALIASES.get(normalized)

    if aliases:
        return aliases

    # For an unknown skill, use a literal whole-word match.
    # Do not treat arbitrary regular expressions as user input.
    escaped = re.escape(str(skill).strip())
    return [rf"(?i)(?<!\w){escaped}(?!\w)"] if escaped else []




def _select_files(tree):
    candidates = []

    source_suffixes = {
        ".java", ".py", ".js", ".jsx", ".ts", ".tsx", ".sql"
    }

    excluded_dirs = {
        "node_modules", "vendor", "dist", "build",
        ".git", "__pycache__", "target", ".venv", "venv",
    }

    for item in tree.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        name = path.rsplit("/", 1)[-1]
        suffix = Path(name).suffix.lower()
        parts = path.lower().split("/")

        if any(part in excluded_dirs for part in parts):
            continue

        if name.lower() not in PRIORITY_NAMES and suffix not in ALLOWED_SUFFIXES:
            continue

        if item.get("size", 0) > MAX_FILE_BYTES:
            continue

        # Prefer implementation code over configuration files.
        if suffix in source_suffixes:
            # Give Java, frontend, and Python source equal priority,
            # then prefer files closer to the project root.
            language_priority = {
                ".java": 0,
                ".jsx": 1,
                ".tsx": 1,
                ".js": 1,
                ".ts": 1,
                ".py": 2,
                ".sql": 3,
            }.get(suffix, 4)

            priority = (0, language_priority, path.count("/"), path)
        else:
            priority = (1, 0, path.count("/"), path)

        candidates.append((priority, path, item.get("sha")))

    candidates.sort(key=lambda row: row[0])

    # Reserve a portion for each source-language group where available.
    selected = []
    selected_paths = set()

    for suffixes in (
            {".java"},
            {".jsx", ".tsx", ".js", ".ts"},
            {".py"},
            {".sql"},
    ):
        group = [
            row for row in candidates
            if Path(row[1]).suffix.lower() in suffixes
        ]

        if suffixes == {".py"}:
            # Prefer FastAPI application entry points within Python files.
            group.sort(
                key=lambda row: (
                    0 if row[1].lower().endswith(
                        ("ai-service/main.py", "ai-service/app/main.py")
                    ) else 1,
                    row[0],
                )
            )

        for row in group[:4]:
            if row[1] not in selected_paths:
                selected.append(row)
                selected_paths.add(row[1])
        group = [
            row for row in candidates
            if Path(row[1]).suffix.lower() in suffixes
        ]

        for row in group[:4]:
            if row[1] not in selected_paths:
                selected.append(row)
                selected_paths.add(row[1])

    # Fill remaining slots with the highest-priority unselected files.
    for row in candidates:
        if len(selected) >= MAX_FILES_PER_REPOSITORY:
            break

        if row[1] not in selected_paths:
            selected.append(row)
            selected_paths.add(row[1])

    selected = selected[:MAX_FILES_PER_REPOSITORY]

    return [
        (0, path, sha)
        for _, path, sha in selected
    ]




def _decode_blob(blob):
    if blob.get("encoding") != "base64":
        return ""

    try:
        raw = base64.b64decode(blob.get("content", ""))
        return raw.decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return ""


def _find_skill_evidence(skill, file_contents):
    """Return a source-code signal appropriate for this skill."""
    normalized = _normalize_skill(skill)

    rules = {
        "java": {
            "suffixes": {".java"},
            "patterns": [
                r"^\s*package\s+[\w.]+\s*;",
                r"^\s*public\s+(?:abstract\s+)?class\s+\w+",
                r"^\s*public\s+interface\s+\w+",
                r"^\s*(?:public\s+)?record\s+\w+",
            ],
        },
        "springboot": {
            "suffixes": {".java"},
            "patterns": [
                r"import\s+org\.springframework\.",
                r"@SpringBootApplication\b",
                r"@RestController\b",
                r"@Service\b",
                r"@Repository\b",
                r"@GetMapping\b",
                r"@PostMapping\b",
            ],
        },
        "react": {
            "suffixes": {".jsx", ".tsx", ".js", ".ts"},
            "patterns": [
                r"import\s+.*\s+from\s+['\"]react['\"]",
                r"\buseState\s*\(",
                r"\buseEffect\s*\(",
                r"^\s*export\s+default\s+function\s+\w+",
                r"^\s*function\s+\w+\s*\([^)]*\)\s*\{",
            ],
        },
        "fastapi": {
            "suffixes": {".py"},
            "patterns": [
                r"^\s*from\s+fastapi\s+import\b",
                r"^\s*import\s+fastapi\b",
                r"^\s*@\w+\.(?:get|post|put|delete|patch)\(",
                r"^\s*@app\.(?:get|post|put|delete|patch)\b",
            ],
        },
    }

    rule = rules.get(normalized)

    # Unknown skills are not automatically considered verified.
    if not rule:
        return None

    for path, content in file_contents:
        if Path(path).suffix.lower() not in rule["suffixes"]:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()

            # Exclude obvious comment and blank lines.
            if not stripped or stripped.startswith(
                ("//", "#", "*", "<!--")
            ):
                continue

            if any(
                re.search(pattern, line)
                for pattern in rule["patterns"]
            ):
                return {
                    "skill": skill,
                    "path": path,
                    "line": line_number,
                    "snippet": stripped[:240],
                }

    return None



def _inspect_repository(repository, required_skills, token, cache):
    owner = str(repository.get("owner", "")).strip()
    name = str(repository.get("name", "")).strip()

    if not owner or not name or "/" in owner or "/" in name:
        raise GitHubEvaluationError("Invalid repository owner or name.")

    encoded_repo = (
        urllib.parse.quote(owner, safe="")
        + "/"
        + urllib.parse.quote(name, safe="")
    )
    repo_info = _github_get(f"/repos/{encoded_repo}", token)

    if repo_info.get("private") and not repo_info.get("permissions", {}).get("pull"):
        raise GitHubEvaluationError(
            f"Repository {owner}/{name} is not readable by this token."
        )

    branch = repo_info.get("default_branch")
    if not branch:
        raise GitHubEvaluationError(
            f"Repository {owner}/{name} has no default branch."
        )

    branch_encoded = urllib.parse.quote(branch, safe="")
    commit_info = _github_get(
        f"/repos/{encoded_repo}/commits/{branch_encoded}",
        token,
    )
    revision = commit_info.get("sha")

    if not revision:
        raise GitHubEvaluationError(
            f"Could not resolve revision for {owner}/{name}."
        )

    # Include the required skills in the cache key so different jobs
    # cannot accidentally reuse the same evaluation result.
    normalized_skills = sorted({
        str(skill).strip().lower()
        for skill in required_skills
        if str(skill).strip()
    })
    EVALUATOR_VERSION = "2"

    cache_key = (
        f"{owner}/{name}@{revision}"
        f"|skills:{','.join(normalized_skills)}"
        f"|evaluator:{EVALUATOR_VERSION}"
    )

    cached = cache.get(cache_key)
    if cached and time.time() - cached.get("cached_at", 0) < CACHE_TTL_SECONDS:
        return RepositoryEvidence(**cached["result"])

    revision_encoded = urllib.parse.quote(revision, safe="")
    tree = _github_get(
        f"/repos/{encoded_repo}/git/trees/{revision_encoded}?recursive=1",
        token,
    )

    selected_files = _select_files(tree)
    print("\nSelected files for inspection:")
    for _, path, _ in selected_files:
        print(f"  {path}")
    file_contents = []

    # Download selected files first.
    for _, path, blob_sha in selected_files:
        if not blob_sha:
            continue

        blob = _github_get(
            f"/repos/{encoded_repo}/git/blobs/"
            f"{urllib.parse.quote(blob_sha, safe='')}",
            token,
        )
        content = _decode_blob(blob)

        if content:
            file_contents.append((path, content))

    # Evaluate each required skill exactly once across the collected files.
    matched = []
    evidence_items = []

    for skill in normalized_skills:
        found = _find_skill_evidence(skill, file_contents)

        if found:
            matched.append(skill)

            duplicate = any(
                item["skill"].lower() == found["skill"].lower()
                and item["path"] == found["path"]
                and item["line"] == found["line"]
                for item in evidence_items
            )

            if not duplicate:
                evidence_items.append(found)

    total_skills = len(normalized_skills)
    score = round(100 * len(matched) / total_skills, 2) if total_skills else 0.0

    result = RepositoryEvidence(
        repository=f"{owner}/{name}",
        url=repo_info.get(
            "html_url",
            f"https://github.com/{owner}/{name}",
        ),
        score=score,
        matched_skills=matched,
        evidence=evidence_items,
    )

    cache[cache_key] = {
        "cached_at": time.time(),
        "result": {
            "repository": result.repository,
            "url": result.url,
            "score": result.score,
            "matched_skills": result.matched_skills,
            "evidence": result.evidence,
        },
    }
    _save_cache(cache)

    return result


def evaluate_github_evidence(
    repositories,
    required_skills,
    max_repositories=MAX_REPOSITORIES,
):
    """
    Evaluate candidate repositories against required job skills.

    repositories: list of {"owner": "account", "name": "repo"}
    required_skills: list of required skill names

    The score measures observable skill coverage in inspected files.
    It is not a measure of overall engineering ability.
    """
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        return GitHubEvidenceResult(
            status="EVALUATION_FAILED",
            score=None,
            error="GITHUB_TOKEN environment variable is not configured.",
        )

    skills = list(dict.fromkeys(
        str(skill).strip()
        for skill in (required_skills or [])
        if str(skill).strip()
    ))

    if not skills:
        return GitHubEvidenceResult(
            status="EVALUATION_FAILED",
            score=None,
            error="No required skills were provided.",
        )

    if not repositories:
        return GitHubEvidenceResult(
            status="NO_EVIDENCE",
            score=0.0,
            missing_skills=skills,
        )

    limit = max(1, min(int(max_repositories), MAX_REPOSITORIES))
    cache = _load_cache()
    evaluated = []

    try:
        for repository in repositories[:limit]:
            evaluated.append(
                _inspect_repository(repository, skills, token, cache)
            )
    except GitHubEvaluationError as exc:
        # Never convert an API failure into a zero evidence score.
        return GitHubEvidenceResult(
            status="EVALUATION_FAILED",
            score=None,
            error=str(exc),
        )

    matched = sorted({
        skill
        for repo in evaluated
        for skill in repo.matched_skills
    }, key=str.lower)

    matched_keys = {skill.lower() for skill in matched}
    missing = [
        skill for skill in skills
        if skill.lower() not in matched_keys
    ]

    overall_score = round(100 * len(matched_keys) / len({
        skill.lower() for skill in skills
    }), 2)

    return GitHubEvidenceResult(
        status="COMPLETED" if matched else "NO_EVIDENCE",
        score=overall_score,
        matched_skills=matched,
        missing_skills=missing,
        relevant_repositories=sorted(
            evaluated,
            key=lambda repo: repo.score,
            reverse=True,
        ),
    )
