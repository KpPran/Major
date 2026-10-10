
from app.github_evidence.evaluator import evaluate_github_evidence

result = evaluate_github_evidence(
    repositories=[
        {
            "owner": "Pranav-stl",
            "name": (
                "Integrated-Career-IntelligencePlatformForDynamicSkillGapDetection"
                "-And-RealTime-JobMatching"
            ),
        }
    ],
    required_skills=["java", "springboot", "react", "fastapi"],
)

print("Status:", result.status)
print("Score:", result.score)
print("Matched skills:", result.matched_skills)
print("Missing skills:", result.missing_skills)
print("Error:", result.error)

for repo in result.relevant_repositories:
    print("\nRepository:", repo.repository)
    print("Repository score:", repo.score)
    for item in repo.evidence:
        print(
            f"  {item['skill']}: {item['path']}:"
            f"{item['line']} — {item['snippet']}"
        )
