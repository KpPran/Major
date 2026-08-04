import re
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# =====================================================
# Resume Cleaning
# =====================================================

def clean_resume(text: str) -> str:

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = re.sub(r'http\S+|www\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'\+?\d[\d\s()-]{8,}\d', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)

    text = text.replace("c++", "cplusplus")
    text = text.replace("c#", "csharp")
    text = text.replace(".net", "dotnet")
    text = text.replace("node.js", "nodejs")
    text = text.replace("react.js", "reactjs")
    text = text.replace("asp.net", "aspdotnet")

    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# =====================================================
# Job Cleaning
# =====================================================

def clean_job(text: str) -> str:

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"\+?\d[\d\s\-()]{8,}\d", " ", text)
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =====================================================
# Skill Overlap
# =====================================================

def skill_overlap(resume_skills, job_skills):

    if pd.isna(resume_skills):
        resume = set()

    else:

        try:

            if isinstance(resume_skills, str):

                resume = {
                    skill.strip().lower()
                    for skill in str(resume_skills).replace(",", " ").split()
                    if skill.strip()
                }

                if not isinstance(resume, list):
                    resume = str(resume_skills).split(",")

            else:
                resume = resume_skills

        except:
            resume = str(resume_skills).split(",")

        resume = {
            str(skill).strip().lower()
            for skill in resume
            if str(skill).strip()
        }

    if pd.isna(job_skills):

        job = set()

    else:

        job = {
            skill.strip().lower()
            for skill in str(job_skills).split(",")
            if skill.strip()
        }

    if len(job) == 0:
        return 0

    common = resume.intersection(job)

    return (len(common) / len(job)) * 100


# =====================================================
# Semantic Similarity
# =====================================================

def semantic_similarity(resume_embedding, job_embedding):

    similarity = cosine_similarity(

        resume_embedding.reshape(1, -1),

        job_embedding.reshape(1, -1)

    )[0][0]

    return similarity * 100


# =====================================================
# Final Match Score
# =====================================================

def final_label(skill_score, semantic_score):

    return (0.7 * skill_score) + (0.3 * semantic_score)


# =====================================================
# Better Skill Matching for Inference
# =====================================================

def find_matching_and_missing_skills(
    cleaned_resume,
    job_skills
):

    resume_text = cleaned_resume.lower()

    matching = []

    missing = []

    for skill in job_skills:

        skill = skill.strip()

        if skill.lower() in resume_text:

            matching.append(skill)

        else:

            missing.append(skill)

    return matching, missing