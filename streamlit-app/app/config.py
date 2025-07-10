import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

MODEL_DIR = os.path.join(BASE_DIR, "fnn")
GRAPH_NN_MODEL_DIR = os.path.join(BASE_DIR, "streamlit-app\models\graph_nn\model_predict")
DATA_DIR = os.path.join(BASE_DIR, "datasets")

FCNN_PATHS = {
    "model_path": os.path.join(MODEL_DIR, "fcnn_model.pth"),
    "scaler_x_path": os.path.join(MODEL_DIR, "scaler_X.pkl"),
    "scaler_y_path": os.path.join(MODEL_DIR, "scaler_y.pkl"),
    "encoder_path": os.path.join(MODEL_DIR, "onehot_encoder.pkl"),
    "data_path": os.path.join(DATA_DIR, "huge_delays_removed_240625.parquet"),  # jeśli niewykorzystywany, można usunąć

}

GNN_PATHS = {
    "gnn_model_path": os.path.join(GRAPH_NN_MODEL_DIR, "model_weights.pkl"),
    "edge_index_path": os.path.join(GRAPH_NN_MODEL_DIR, "edge_index.pkl"),
    "stop_id_map_path": os.path.join(GRAPH_NN_MODEL_DIR, "stop_id_map.pkl"),
    "line_encoding_path": os.path.join(GRAPH_NN_MODEL_DIR, "line_encoding.csv"),
    "edge_list_path": os.path.join(GRAPH_NN_MODEL_DIR, "edge_list.pkl"),
    "scaler_gnn_path": os.path.join(GRAPH_NN_MODEL_DIR, "scaler.joblib"),

}

