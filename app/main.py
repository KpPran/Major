from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    MatchRequest,
    MatchResponse
)

from app.predict import (
    predict_resume_job_match
)
from dataclasses import asdict

from pydantic import BaseModel, Field

from app.github_evidence.evaluator import evaluate_github_evidence

class GitHubRepositoryRequest(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)


class GitHubEvidenceRequest(BaseModel):
    repositories: list[GitHubRepositoryRequest] = Field(
        default_factory=list,
        max_length=3,
    )
    required_skills: list[str] = Field(min_length=1)
app = FastAPI(
    title="AI Resume Matching Service",
    description="Resume Screening & Course Recommendation API",
    version="1.0.0"
)

# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Change later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Health Check
# =====================================================

@app.get("/")
def health_check():

    return {
        "status": "Running",
        "service": "AI Resume Matching API"
    }


@app.get("/health")
def health():

    return {
        "status": "Healthy"
    }


# =====================================================
# Resume Matching Endpoint
# =====================================================

@app.post(
    "/match",
    response_model=MatchResponse
)
def match_resume(
    request: MatchRequest
):

    result = predict_resume_job_match(

        resume_text=request.resumeText,

        job_description=request.jobDescription,

        job_skills=request.jobSkills

    )

    return result

# =====================================================
# GitHub Evidence Evaluation Endpoint
# =====================================================

@app.post("/github-evidence")
def evaluate_github_repositories(request: GitHubEvidenceRequest):
    result = evaluate_github_evidence(
        repositories=[
            repository.model_dump()
            for repository in request.repositories
        ],
        required_skills=request.required_skills,
        max_repositories=3,
    )

    return asdict(result)