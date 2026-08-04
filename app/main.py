from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    MatchRequest,
    MatchResponse
)

from app.predict import (
    predict_resume_job_match
)

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