
from app.github_evidence.scoring import (
    WEIGHT_CONFIGS,
    combine_scores,
)


cases = [
    ("No GitHub evidence", 47, 0, "NO_EVIDENCE"),
    ("Moderate evidence", 47, 50, "COMPLETED"),
    ("Strong evidence", 47, 80, "COMPLETED"),
    ("Very strong evidence", 47, 100, "COMPLETED"),
    ("High ML, no evidence", 85, 0, "NO_EVIDENCE"),
]

print(f"{'Case':<25} {'Strategy':<10} {'ML':>6} {'GitHub':>8} {'Combined':>10}")
print("-" * 65)

for case_name, ml_score, gh_score, status in cases:
    for strategy in WEIGHT_CONFIGS:
        result = combine_scores(
            resume_job_score=ml_score,
            github_score=gh_score,
            github_status=status,
            strategy=strategy,
        )
        print(
            f"{case_name:<25} {strategy:<10} "
            f"{result.resume_job_score:>6.1f} "
            f"{result.github_score:>8.1f} "
            f"{result.combined_score:>10.2f}"
        )

print("\nFailure handling check:")
try:
    combine_scores(
        resume_job_score=47,
        github_score=None,
        github_status="EVALUATION_FAILED",
        strategy="80:20",
    )
except ValueError as exc:
    print("Correctly rejected failed evaluation:", exc)
