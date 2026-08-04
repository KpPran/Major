from pathlib import Path

# ==============================
# Base Directory
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# Model Path
# ==============================

MODEL_PATH = BASE_DIR / "models" / "resume_match_model.pkl"

# ==============================
# Dataset Paths
# ==============================

DATA_DIR = BASE_DIR / "data"

RESUME_DATASET = DATA_DIR / "final_merged_dataset2.csv"

JOB_DATASET = DATA_DIR / "cleaned_job_descriptions.csv"

RESUME_EMBEDDINGS = DATA_DIR / "final_merged_dataset2.csv.npy"

JOB_EMBEDDINGS = DATA_DIR / "job_embeddings.npy"

# ==============================
# Embedding Model
# ==============================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"