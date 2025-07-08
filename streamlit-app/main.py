import os
import streamlit as st
import torch
import torch.nn as nn
import numpy as np
import joblib
import polars as pl
from prepare_input import prepare_input
from datetime import datetime, date
# ❌ NIE działa na Python 3.13:
# from pycaret.functions import prepare_data, load_model, predict_model

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# ===== FCNN MODEL =====
class FCNN(nn.Module):
    def __init__(self, input_size):
        super(FCNN, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.layers(x)

# ===== Ścieżki do modeli i danych =====
MODEL_PATH = os.path.join(BASE_DIR, "fnn","fcnn_model.pth")
SCALER_X_PATH = os.path.join(BASE_DIR, "fnn","scaler_X.pkl")
SCALER_Y_PATH = os.path.join(BASE_DIR, "fnn","scaler_y.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "fnn","onehot_encoder.pkl")
PARQUET_PATH = os.path.join(BASE_DIR, "data", "huge_delays_removed_240625.parquet")

# ❌ PyCaret model – odkomentuj TYLKO jeśli masz Python <= 3.10
# XGB_MODEL_PATH = os.path.join(BASE_DIR, "pycaret", "xgboost.pkl")
# model_xgb = load_model(XGB_MODEL_PATH)

# ===== Wczytanie modeli FCNN =====
model_fcnn = FCNN(input_size=19)
model_fcnn.load_state_dict(torch.load(MODEL_PATH))
model_fcnn.eval()

scaler_X = joblib.load(SCALER_X_PATH)
scaler_y = joblib.load(SCALER_Y_PATH)
encoder = joblib.load(ENCODER_PATH)

# ===== Wczytanie danych przystankowych z cache =====
@st.cache_resource
def load_data():
    df = pl.read_parquet(PARQUET_PATH)
    return df

df_all = load_data()
available_lines = sorted(df_all["Linia"].unique().to_list())

@st.cache_resource
def get_stops_by_line(df: pl.DataFrame):
    stops_dict = {}
    for line in df["Linia"].unique():
        line_df = df.filter(pl.col("Linia") == line).sort("Lp przystanku")
        stops = line_df["Przystanek nazwa"].unique().to_list()
        stops_dict[line] = stops
    return stops_dict

stops_by_line = get_stops_by_line(df_all)

# ===== Interfejs użytkownika =====
st.title("Bus Delay Prediction")

line = st.selectbox("Wybierz linię", available_lines)
start_stop = st.selectbox("Skąd jedziesz?", stops_by_line.get(line, []))
end_stop = st.selectbox("Dokąd jedziesz?", stops_by_line.get(line, []))
date_input = st.date_input("Kiedy?", min_value=date.today())
time_input = st.time_input("O której?")

if st.button("Predict"):
    try:
        # ===== FCNN Predict =====
        input_features_fcnn = prepare_input(start_stop, end_stop, line, date_input, time_input, PARQUET_PATH, encoder)
        input_scaled_fcnn = scaler_X.transform([input_features_fcnn])
        input_tensor = torch.tensor(input_scaled_fcnn, dtype=torch.float32)

        with torch.no_grad():
            prediction_scaled_fcnn = model_fcnn(input_tensor)
            prediction_fcnn = scaler_y.inverse_transform(prediction_scaled_fcnn.numpy())[0][0]

        # ===== PyCaret Predict – zakomentowane, bo NIE działa na Py 3.13 =====
        # selected_datetime = datetime.combine(date_input, time_input)
        # input_df_xgb = prepare_data(start_stop, line, selected_datetime)
        # prediction_xgb = predict_model(model_xgb, data=input_df_xgb)
        # predicted_xgb = prediction_xgb["prediction_label"].values[0]

        # ===== Wyświetlenie wyników =====
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Predykcja FCNN")
            st.metric("Czas przejazdu", f"{prediction_fcnn:.1f} s ({prediction_fcnn/60:.2f} min)")

        with col2:
            st.subheader("Predykcja XGBoost (PyCaret)")
            st.write("❌ Niedostępne – wymaga Python ≤ 3.10 + PyCaret")
            # st.metric("Opóźnienie", f"{predicted_xgb:.1f} s ({predicted_xgb/60:.2f} min)")

    except Exception as e:
        st.error(f"Wystąpił błąd: {e}")
