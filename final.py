import joblib

saved = joblib.load("resume_match_model.pkl")

model = saved["model"]

print("\n===== MODEL STATISTICS =====")
print(f"MAE               : {saved['mae']:.4f}")
print(f"RMSE              : {saved['rmse']:.4f}")
print(f"R²                : {saved['r2']:.4f}")
print(f"Correlation       : {saved['corr']:.4f}")
print(f"Training Samples  : {saved['train_samples']}")
print(f"Testing Samples   : {saved['test_samples']}")



