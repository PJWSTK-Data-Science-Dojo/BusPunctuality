import streamlit as st
from models.fcnn_model import FCNNModel
from app.config import FCNN_PATHS
from utils.ui_helpers import loading_spinner
import polars as pl
from datetime import date
import json


st.title("Buspunctuality")

# TODO not sure if this method truly returns bus stops names in bus route order
@st.cache_resource
def load_metadata():
    with open("data/line_stops_database.json", "r", encoding="utf-8") as f:
        stops_by_line = json.load(f)
    lines = sorted(stops_by_line.keys())
    return lines, stops_by_line

lines, stops_by_line = load_metadata()

# UI
line = st.selectbox("Wybierz linię", lines)
start = st.selectbox("Skąd jedziesz?", stops_by_line.get(line, []))
end = st.selectbox("Dokąd jedziesz?", stops_by_line.get(line, []))
date_input = st.date_input("Kiedy?", min_value=date.today())
time_input = st.time_input("O której?")

# Model FCNN
fcnn_model = FCNNModel(**FCNN_PATHS)

# Predict
if st.button("Predict"):
    try:
        with loading_spinner("Ładowanie modelu i predykcji..."):
            fcnn_model.load()
            features = fcnn_model.prepare_input(start, end, line, date_input, time_input)
            delay_sec = fcnn_model.predict(features)

        st.success("✅ Predykcja zakończona")
        st.metric("Opóźnienie (FCNN)", f"{delay_sec:.1f} s", f"{delay_sec/60:.2f} min")

    except Exception as e:
        st.error(f"❌ Błąd predykcji: {e}")
