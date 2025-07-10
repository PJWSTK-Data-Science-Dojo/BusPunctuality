import streamlit as st
from models.fcnn_model import FCNNModel
from models.gnn_model import GNNModel
from models.xgb_model import XGBModel
from app.config import FCNN_PATHS, GNN_PATHS, XGB_PATHS
from datetime import date, datetime
import json

st.title("Buspunctuality")

@st.cache_resource
def load_metadata():
    with open("data/line_stops_database.json", "r", encoding="utf-8") as f:
        stops_by_line = json.load(f)
    return sorted(stops_by_line.keys()), stops_by_line


def predict_pipeline(model_name, model, start, end, line, date_input, time_input, state_key):
    """Ładuje model, przygotowuje input, robi predict i zapisuje status w session_state."""
    st.session_state[state_key] = {"status": "loading"}
    try:
        with st.spinner(f"⏳ Obliczanie opóźnienia ({model_name})..."):
            model.load()
            features = model.prepare_input(start, end, line, date_input, time_input)
            delay = model.predict(features)
            st.session_state[state_key] = {"status": "success", "delay": round(delay, 1)}
    except Exception as e:
        st.session_state[state_key] = {"status": "error", "message": str(e)}


def display_model_column(model_name, state_key):
    state = st.session_state.get(state_key, {})
    st.markdown(f"**{model_name}**")
    if state.get("status") == "loading":
        st.spinner(f"⏳ Obliczanie opóźnienia ({model_name})...")
    elif state.get("status") == "success":
        total_seconds = state['delay']
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        delay_min = minutes + seconds / 60
        if delay_min > 5:
            bg_color = '#eb4d4b'
            text_color = '#dff9fb'
        elif delay_min > 1:
            bg_color = '#f9ca24'
            text_color = '#2f3640'
        else:
            bg_color = '#6ab04c'
            text_color = '#2f3640'
        # Format display
        time_str = f"{minutes} min {seconds} s" if minutes > 0 else f"{seconds} s"
        st.markdown(
            f"<div style='background-color:{bg_color}; color:{text_color}; padding:10px; border-radius:5px;'>"
            f"Przewidywane opóźnienie: <br> <strong>{time_str}</strong>"
            "</div>",
            unsafe_allow_html=True
        )
    elif state.get("status") == "error":
        st.error("❌ Nie udało się obliczyć opóźnienia.")
        st.code(state.get("message", "Brak szczegółów błędu"))
    else:
        st.info("Kliknij 'Predict', aby rozpocząć obliczenia.")


# Initialize session state for each model
for model in ["GNN", "XGB", "FCNN"]:
    key = f"{model}_state"
    if key not in st.session_state:
        st.session_state[key] = {}

lines, stops_by_line = load_metadata()

# UI
line = st.selectbox("Wybierz linię", lines)
all_stops = stops_by_line.get(line, [])
start = st.selectbox("Skąd jedziesz?", all_stops)
end_candidates = all_stops[all_stops.index(start) + 1:] if start in all_stops else []
end = st.selectbox("Dokąd jedziesz?", end_candidates)
date_input = st.date_input("Kiedy?", min_value=date.today())
time_input = st.time_input("O której?")

if start == end and start != "":
    st.warning("🚫 Przystanki początkowy i końcowy nie mogą być takie same.")

# Instantiate models
fcnn_model = FCNNModel(**FCNN_PATHS)
gnn_model  = GNNModel(**GNN_PATHS)
xgb_model  = XGBModel(**XGB_PATHS)

# Predict button
if st.button("Predict") and start != end:
    predict_pipeline("GNN",  gnn_model,  start, end, line, date_input, time_input, "GNN_state")
    predict_pipeline("XGB",  xgb_model,  start, end, line, date_input, time_input, "XGB_state")
    predict_pipeline("FCNN", fcnn_model, start, end, line, date_input, time_input, "FCNN_state")

# Display results section
if start != end:
    datetime_str = datetime.combine(date_input, time_input).strftime("%Y-%m-%d %H:%M")
    st.subheader("Wyniki predykcji")
    st.markdown(
        f"Przewidywane opóźnienie z **{start}** do **{end}** na **{datetime_str}**",
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        display_model_column("GNN",  "GNN_state")
    with col2:
        display_model_column("XGB",  "XGB_state")
    with col3:
        display_model_column("FCNN", "FCNN_state")
