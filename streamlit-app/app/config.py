import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "fnn")
DATA_DIR = os.path.join(BASE_DIR, "datasets")

FCNN_PATHS = {
    "model_path": os.path.join(MODEL_DIR, "fcnn_model.pth"),
    "scaler_x_path": os.path.join(MODEL_DIR, "scaler_X.pkl"),
    "scaler_y_path": os.path.join(MODEL_DIR, "scaler_y.pkl"),
    "encoder_path": os.path.join(MODEL_DIR, "onehot_encoder.pkl"),
    "data_path": os.path.join(DATA_DIR, "huge_delays_removed_240625.parquet"),  # jeśli niewykorzystywany, można usunąć
}


