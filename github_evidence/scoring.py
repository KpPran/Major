
from dataclasses import dataclass


WEIGHT_CONFIGS = {
    "85:15": (0.85, 0.15),
    "80:20": (0.80, 0.20),
    "75:25": (0.75, 0.25),
}


@dataclass
class CombinedScore:
    strategy: str
    resume_job_score: float
    github_score: float
    combined_score: float
    github_status: str


def combine_scores(
    resume_job_score: float,
    github_score: float | None,
    github_status: str,
    strategy: str = "80:20",
) -> CombinedScore:
    if strategy not in WEIGHT_CONFIGS:
        raise ValueError(f"Unknown strategy: {strategy}")

    if not 0 <= resume_job_score <= 100:
        raise ValueError("Resume-job score must be between 0 and 100.")

    if github_status == "EVALUATION_FAILED":
        raise ValueError(
            "Cannot finalize a combined score when GitHub evaluation failed."
        )

    if github_status == "NO_EVIDENCE":
        github_score = 0.0
    elif github_status == "COMPLETED":
        if github_score is None or not 0 <= github_score <= 100:
            raise ValueError("A completed evaluation needs a score from 0 to 100.")
    else:
        raise ValueError(f"Unknown GitHub status: {github_status}")

    resume_weight, github_weight = WEIGHT_CONFIGS[strategy]

    combined = (
        resume_weight * resume_job_score
        + github_weight * github_score
    )

    return CombinedScore(
        strategy=strategy,
        resume_job_score=round(resume_job_score, 2),
        github_score=round(github_score, 2),
        combined_score=round(combined, 2),
        github_status=github_status,
    )
