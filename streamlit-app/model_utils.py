# FUNCTION TO PREPARE INPUT FROM UI TO PREDICTION MODEL
# convert data to required input for both neural network models

# def prepare_input(): 
import polars as pl
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
import joblib
import torch


def prepare_input(stop_name, line, date, time, parquet_file_path, encoder):
    # Wczytaj dane z pliku Parquet
    df = pl.read_parquet(parquet_file_path)

    # Połącz datę i godzinę
    input_datetime = datetime.combine(date, time)

    # Sprawdź, czy to dzień roboczy
    is_weekday = input_datetime.weekday() < 5  # Poniedziałek-Piątek

    # Sprawdź, czy to godziny szczytu
    rush_hour = 1 if input_datetime.hour in [6, 7, 8, 9, 15, 16, 17, 18] else 0

    # Znajdź informacje o przystanku i linii
    stop_data = df.filter((pl.col("stop_name") == stop_name) & (pl.col("line") == line))
    if stop_data.is_empty():
        raise ValueError(f"Nie znaleziono przystanku {stop_name} dla linii {line}.")

    # Pobierz stop_seq, stop_lat, stop_lon
    stop_seq = stop_data["stop_seq"][0]
    stop_lat = stop_data["stop_lat"][0]
    stop_lon = stop_data["stop_lon"][0]

    # Znajdź następny przystanek dla tej linii
    next_stop = df.filter(
        (pl.col("line") == line) & (pl.col("stop_seq") == stop_seq + 1)
    )
    distance = 0
    far_status = 0
    if not next_stop.is_empty():
        next_lat = next_stop["stop_lat"][0]
        next_lon = next_stop["stop_lon"][0]
        distance = geodesic((stop_lat, stop_lon), (next_lat, next_lon)).meters
        far_status = 1 if distance > 250 else 0

    # Kodowanie one-hot dla linii
    line_encoded = encoder.transform([[line]]).flatten()

    # Połącz cechy
    input_features = np.concatenate([
        line_encoded,
        [distance, is_weekday, rush_hour, stop_seq, far_status]
    ])

    return input_features