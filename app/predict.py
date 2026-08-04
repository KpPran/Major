import joblib
import numpy as np

from sentence_transformers import SentenceTransformer

from app.config import (
    MODEL_PATH,
    EMBEDDING_MODEL
)

from app.utils import (
    clean_resume,
    clean_job,
    find_matching_and_missing_skills
)

from app.course_recommender import recommend_courses


# =====================================================
# Load Embedding Model (Loads Once)
# =====================================================

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


# =====================================================
# Load Trained XGBoost Model
# =====================================================

saved_model = joblib.load(MODEL_PATH)

if isinstance(saved_model, dict):
    match_model = saved_model["match_model"]
else:
    match_model = saved_model


# =====================================================
# Prediction Function
# =====================================================

def predict_resume_job_match(
        resume_text: str,
        job_description: str,
        job_skills: list
):

    # -----------------------------------------
    # Clean Inputs
    # -----------------------------------------

    cleaned_resume = clean_resume(
        resume_text
    )

    cleaned_job = clean_job(
        job_description
    )

    # -----------------------------------------
    # Generate Embeddings
    # -----------------------------------------

    resume_embedding = embedding_model.encode(
        cleaned_resume,
        convert_to_numpy=True
    )

    job_embedding = embedding_model.encode(
        cleaned_job,
        convert_to_numpy=True
    )

    # -----------------------------------------
    # Create Feature Vector
    # -----------------------------------------

    features = np.concatenate(
        [
            resume_embedding,
            job_embedding
        ]
    ).reshape(1, -1)

    # -----------------------------------------
    # Predict Match Score
    # -----------------------------------------

    predicted_score = float(

        match_model.predict(
            features
        )[0]

    )

    # -----------------------------------------
    # Skill Matching
    # -----------------------------------------

    matching_skills, missing_skills = \
        find_matching_and_missing_skills(
            cleaned_resume,
            job_skills
        )

    # -----------------------------------------
    # Recommend Courses
    # -----------------------------------------

    recommended_courses = recommend_courses(
        missing_skills
    )

    # -----------------------------------------
    # Response
    # -----------------------------------------

    return {

        "matchScore": round(
            predicted_score,
            2
        ),

        "matchingSkills": matching_skills,

        "missingSkills": missing_skills,

        "recommendedCourses": recommended_courses

    }

if __name__ == "__main__":

    result = predict_resume_job_match(

        resume_text="""
        Java Developer
        Spring Boot
        MySQL
        REST API
        Docker
        """,

        job_description="""
        Looking for Java Backend Developer
        with Spring Boot and MySQL
        """,

        job_skills=[
            "Java",
            "Spring Boot",
            "MySQL",
            "REST API",
            "AWS"
        ]
    )

    print(result)