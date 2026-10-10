import json
import unittest
import urllib.error
from email.message import Message
from unittest.mock import patch
from app.github_evidence.evaluator import _github_get
import os
import unittest
from unittest.mock import patch

from app.github_evidence.evaluator import (
    evaluate_github_evidence,
    GitHubEvaluationError,
)


class TestGitHubEvidence(unittest.TestCase):

    def setUp(self):
        self.token_patch = patch.dict(
            os.environ, {"GITHUB_TOKEN": "test-token"}
        )
        self.token_patch.start()
        self.addCleanup(self.token_patch.stop)

    def test_missing_repositories_returns_zero(self):
        result = evaluate_github_evidence(
            repositories=[],
            required_skills=["java", "react"],
        )

        self.assertEqual(result.status, "NO_EVIDENCE")
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.missing_skills, ["java", "react"])

    def test_missing_token_is_evaluation_failure(self):
        with patch.dict(os.environ, {}, clear=True):
            result = evaluate_github_evidence(
                repositories=[{"owner": "demo", "name": "repo"}],
                required_skills=["python"],
            )

        self.assertEqual(result.status, "EVALUATION_FAILED")
        self.assertIsNone(result.score)

    def test_api_failure_is_not_zero_score(self):
        with patch(
            "app.github_evidence.evaluator._inspect_repository",
            side_effect=GitHubEvaluationError("simulated rate limit"),
        ):
            result = evaluate_github_evidence(
                repositories=[{"owner": "demo", "name": "repo"}],
                required_skills=["python"],
            )

        self.assertEqual(result.status, "EVALUATION_FAILED")
        self.assertIsNone(result.score)
        self.assertIn("rate limit", result.error)

    def test_empty_required_skills_fails(self):
        result = evaluate_github_evidence(
            repositories=[{"owner": "demo", "name": "repo"}],
            required_skills=[],
        )

        self.assertEqual(result.status, "EVALUATION_FAILED")
        self.assertIsNone(result.score)

    def test_invalid_repository_returns_failure(self):
        result = evaluate_github_evidence(
            repositories=[{"owner": "", "name": ""}],
            required_skills=["python"],
        )

        self.assertEqual(result.status, "EVALUATION_FAILED")
        self.assertIsNone(result.score)

    def test_only_matched_skills_contribute_to_score(self):
        # Simulate a repository inspection result without network access.
        from app.github_evidence.models import RepositoryEvidence

        fake_repo = RepositoryEvidence(
            repository="demo/repo",
            url="https://github.com/demo/repo",
            score=50.0,
            matched_skills=["python"],
            evidence=[
                {
                    "skill": "python",
                    "path": "app.py",
                    "line": 1,
                    "snippet": "def run():",
                }
            ],
        )

        with patch(
            "app.github_evidence.evaluator._inspect_repository",
            return_value=fake_repo,
        ):
            result = evaluate_github_evidence(
                repositories=[{"owner": "demo", "name": "repo"}],
                required_skills=["python", "java"],
            )

        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.score, 50.0)
        self.assertEqual(result.matched_skills, ["python"])
        self.assertEqual(result.missing_skills, ["java"])

    def test_duplicate_skills_do_not_inflate_score(self):
        from app.github_evidence.models import RepositoryEvidence

        fake_repo = RepositoryEvidence(
            repository="demo/repo",
            url="https://github.com/demo/repo",
            score=100.0,
            matched_skills=["python"],
            evidence=[],
        )

        with patch(
            "app.github_evidence.evaluator._inspect_repository",
            return_value=fake_repo,
        ):
            result = evaluate_github_evidence(
                repositories=[{"owner": "demo", "name": "repo"}],
                required_skills=["python", "python", "java"],
            )

        self.assertEqual(result.score, 50.0)

    def test_repository_limit_is_capped_at_three(self):
        from app.github_evidence.models import RepositoryEvidence

        fake_repo = RepositoryEvidence(
            repository="demo/repo",
            url="https://github.com/demo/repo",
            score=0.0,
            matched_skills=[],
            evidence=[],
        )

        with patch(
            "app.github_evidence.evaluator._inspect_repository",
            return_value=fake_repo,
        ) as inspect:
            result = evaluate_github_evidence(
                repositories=[
                    {"owner": "demo", "name": f"repo{i}"}
                    for i in range(5)
                ],
                required_skills=["python"],
                max_repositories=5,
            )

        self.assertLessEqual(inspect.call_count, 3)
        self.assertEqual(result.status, "NO_EVIDENCE")


    def test_duplicate_matched_skills_are_deduplicated(self):
        from app.github_evidence.models import RepositoryEvidence

        fake_repo = RepositoryEvidence(
            repository="demo/repo",
            url="https://github.com/demo/repo",
            score=100.0,
            matched_skills=["python", "python"],
            evidence=[
                {
                    "skill": "python",
                    "path": "app.py",
                    "line": 1,
                    "snippet": "import fastapi",
                }
            ],
        )

        with patch(
            "app.github_evidence.evaluator._inspect_repository",
            return_value=fake_repo,
        ):
            result = evaluate_github_evidence(
                repositories=[{"owner": "demo", "name": "repo"}],
                required_skills=["python"],
            )

        self.assertEqual(result.matched_skills, ["python"])
        self.assertEqual(result.score, 100.0)


    def test_github_get_success(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"login": "demo"}'
        )
        response.__enter__.return_value.headers = {
            "X-RateLimit-Remaining": "10"
        }

        with patch(
            "app.github_evidence.evaluator.urllib.request.urlopen",
            return_value=response,
        ):
            result = _github_get("/user", "test-token")

        self.assertEqual(result, {"login": "demo"})

    def test_github_get_401_reports_authentication_failure(self):
        headers = Message()
        error = urllib.error.HTTPError(
            url="https://api.github.com/user",
            code=401,
            msg="Unauthorized",
            hdrs=headers,
            fp=None,
        )

        with patch(
            "app.github_evidence.evaluator.urllib.request.urlopen",
            side_effect=error,
        ):
            with self.assertRaises(GitHubEvaluationError) as context:
                _github_get("/user", "invalid-token")

        self.assertIn("authentication failed", str(context.exception).lower())

    def test_github_get_404_reports_missing_resource(self):
        error = urllib.error.HTTPError(
            url="https://api.github.com/repos/demo/missing",
            code=404,
            msg="Not Found",
            hdrs=Message(),
            fp=None,
        )

        with patch(
            "app.github_evidence.evaluator.urllib.request.urlopen",
            side_effect=error,
        ):
            with self.assertRaises(GitHubEvaluationError) as context:
                _github_get("/repos/demo/missing", "test-token")

        self.assertIn("not found", str(context.exception).lower())

    def test_github_get_429_reports_rate_limit(self):
        headers = Message()
        headers["Retry-After"] = "30"

        error = urllib.error.HTTPError(
            url="https://api.github.com/user",
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=None,
        )

        with patch(
            "app.github_evidence.evaluator.urllib.request.urlopen",
            side_effect=error,
        ):
            with self.assertRaises(GitHubEvaluationError) as context:
                _github_get("/user", "test-token")

        self.assertIn("retry after 30 seconds", str(context.exception).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
