
from dataclasses import dataclass, field
from typing import Literal


EvaluationStatus = Literal[
    "COMPLETED",
    "NO_EVIDENCE",
    "EVALUATION_FAILED",
]


@dataclass
class RepositoryEvidence:
    repository: str
    url: str
    score: float
    matched_skills: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)


@dataclass
class GitHubEvidenceResult:
    status: EvaluationStatus
    score: float | None
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    relevant_repositories: list[RepositoryEvidence] = field(
        default_factory=list
    )
    error: str | None = None
