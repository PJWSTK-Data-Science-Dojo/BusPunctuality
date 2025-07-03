import streamlit as st
import pandas as pd
import polars as pl
import numpy as np
import torch
import torch.nn as nn
import joblib
from datetime import datetime
from prepare_input import prepare_input  # Zakładam, że funkcja jest w osobnym pliku

# Definicja modelu FCNN (taka sama jak w treningu)
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

# Wczytanie modelu i obiektów
model = FCNN(input_size=...)  # Podaj właściwy input_size (liczba cech, np. liczba linii + 5)
model.load_state_dict(torch.load("../fnn/fcnn_prediction_model.pth")) #WYKONAC KOD Z MODELU I STWORZYC PLIKI
model.eval()
scaler_X = joblib.load("../fnnscaler_X.pkl")
scaler_y = joblib.load("../fnnscaler_y.pkl")
encoder = joblib.load("../fnnonehot_encoder.pkl")

# Ścieżka do pliku Parquet
parquet_file_path = "../datasets/huge_delays_removed_240625.parquet"

# Interfejs Streamlit
st.title("Bus Delay Prediction")

# Formularz
stop = st.text_input("Bus Stop")
line = st.text_input("Bus Line")
date = st.date_input("Date")
time = st.time_input("Time")

if st.button("Predict"):
    try:
        # Przygotowanie danych wejściowych
        # 1. Wyodrębnij kluczowe dane do mniejszego pliku
        # Zamiast wczytywać cały plik Parquet, możemy stworzyć mniejszy plik (np. CSV, JSON lub Parquet) 
        # zawierający tylko informacje potrzebne do predykcji, czyli:

        # Unikalne linie (line).
        # Przystanki (stop_name, stop_seq, stop_lat, stop_lon) dla każdej linii.
      
        input_features = prepare_input(stop, line, date, time, parquet_file_path, encoder)
        
        # Skalowanie cech
        input_scaled = scaler_X.transform([input_features])
        
        # Konwersja na tensor
        input_tensor = torch.tensor(input_scaled, dtype=torch.float32)
        
        # Predykcja
        with torch.no_grad():
            prediction_scaled = model(input_tensor)
            prediction = scaler_y.inverse_transform(prediction_scaled.numpy())[0][0]
        
        # Wynik w minutach
        delay_minutes = prediction / 60  # Konwersja sekund na minuty
        st.success(f"Predicted delay: {delay_minutes:.2f} minutes")
    except Exception as e:
        st.error(f"Error: {str(e)}")