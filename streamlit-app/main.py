import streamlit as st
from models.fcnn_model import FCNNModel
from models.gnn_model import GNNModel
from models.xgb_model import XGBModel
from app.config import FCNN_PATHS, GNN_PATHS
from datetime import date, datetime
import json

st.title("Buspunctuality")


@st.cache_resource
def load_metadata():
    with open("data/line_stops_database.json", "r", encoding="utf-8") as f:
        stops_by_line = json.load(f)
    return sorted(stops_by_line.keys()), stops_by_line


def predict_single_model(model_name, model, features, state_key):
    try:
        with st.spinner(f"⏳ Obliczanie opóźnienia ({model_name})..."):
            model.load()
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
        st.success(f"Przewidywane opóźnienie: **{state['delay']} s**")
    elif state.get("status") == "error":
        st.error("❌ Przykro mi, nie udało się obliczyć opóźnienia.")
        st.code(state.get("message", "Brak szczegółów błędu"))
    else:
        st.info("Kliknij 'Predict', aby rozpocząć obliczenia.")


for model in ["GNN", "XGB", "FCNN"]:
    key = f"{model}_state"
    if key not in st.session_state:
        st.session_state[key] = {}

lines, stops_by_line = load_metadata()

line = st.selectbox("Wybierz linię", lines)
all_stops = stops_by_line.get(line, [])
start = st.selectbox("Skąd jedziesz?", all_stops)

# Przystanki końcowe tylko późniejsze niż start
end_candidates = all_stops[all_stops.index(start) + 1 :] if start in all_stops else []
end = st.selectbox("Dokąd jedziesz?", end_candidates)

date_input = st.date_input("Kiedy?", min_value=date.today())
time_input = st.time_input("O której?")

if start == end and start != "":
    st.warning("🚫 Początkowy i końcowy przystanek nie mogą być takie same.")

fcnn_model = FCNNModel(**FCNN_PATHS)
gnn_model = GNNModel(**GNN_PATHS)
xgb_model = XGBModel(**FCNN_PATHS)

if st.button("Predict") and start != end:
    for model in ["GNN", "XGB", "FCNN"]:
        st.session_state[f"{model}_state"] = {"status": "loading"}
        gnn_model.load()

    try:
        features = fcnn_model.prepare_input(start, end, line, date_input, time_input)
        features_gnn = gnn_model.prepare_input(start, end, line, date_input, time_input)

        predict_single_model("GNN", gnn_model, features_gnn, "GNN_state")
        predict_single_model("XGB", xgb_model, features, "XGB_state")
        predict_single_model("FCNN", fcnn_model, features, "FCNN_state")

    except Exception as e:
        st.error(f"❌ Błąd przygotowania danych: {e}")

if start != end:
    datetime_str = datetime.combine(date_input, time_input).strftime("%Y-%m-%d %H:%M")

    st.subheader("Wyniki predykcji")
    st.markdown(
        f"Przewidywane opóźnienie z **{start}** do **{end}** na dzień **{datetime_str}**",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        display_model_column("GNN", "GNN_state")

    with col2:
        display_model_column("XGB", "XGB_state")

    with col3:
        display_model_column("FCNN", "FCNN_state")
