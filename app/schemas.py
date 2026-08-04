from pydantic import BaseModel
from typing import List


class MatchRequest(BaseModel):

    resumeText: str

    jobDescription: str

    jobSkills: List[str]


class MatchResponse(BaseModel):

    matchScore: float

    matchingSkills: List[str]

    missingSkills: List[str]

    recommendedCourses: list