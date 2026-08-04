# AI Resume Matching Service

## Start

python -m venv .venv

pip install -r requirements.txt

python -m uvicorn app.main:app --reload

Server:

http://localhost:8000

Swagger:

http://localhost:8000/docs

Endpoint:

POST /match

Request:

{
  "resumeText": "...",
  "jobDescription": "...",
  "jobSkills": ["Java", "Spring Boot", "MySQL"]
}

Response:

{
  "matchScore": 91.2,
  "matchingSkills": [...],
  "missingSkills": [...],
  "recommendedCourses": [...]
}