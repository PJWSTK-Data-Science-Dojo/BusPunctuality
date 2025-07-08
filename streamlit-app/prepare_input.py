import polars as pl
import numpy as np
from geopy.distance import geodesic
from datetime import datetime

def prepare_input(start_stop, end_stop, line, date, time, parquet_file_path, encoder):
    df = pl.read_parquet(parquet_file_path)

    # Wyliczenie cech czasowych
    input_datetime = datetime.combine(date, time)
    is_weekday = 1 if input_datetime.weekday() < 5 else 0
    rush_hour = 1 if input_datetime.hour in [6, 7, 8, 9, 15, 16, 17, 18] else 0

    # Czyszczenie danych wejściowych
    start_stop = start_stop.strip().lower()
    end_stop = end_stop.strip().lower()
    line = str(line).strip()

    # ⬇️ ZNALEZIENIE PRZYSTANKU STARTOWEGO
    stop_data = df.filter(
        (pl.col("Przystanek nazwa").str.strip_chars().str.to_lowercase() == start_stop) &
        (pl.col("Linia").cast(pl.Utf8).str.strip_chars() == line)
    )
    if stop_data.is_empty():
        raise ValueError(f"Nie znaleziono przystanku początkowego '{start_stop}'.")

    stop_seq = stop_data[0, "Lp przystanku"]
    stop_lat = stop_data[0, "stop_lat"]
    stop_lon = stop_data[0, "stop_lon"]

    # ⬇️ ZNALEZIENIE PRZYSTANKU KOŃCOWEGO
    end_data = df.filter(
        (pl.col("Przystanek nazwa").str.strip_chars().str.to_lowercase() == end_stop) &
        (pl.col("Linia").cast(pl.Utf8).str.strip_chars() == line)
    )
    if end_data.is_empty():
        raise ValueError(f"Nie znaleziono przystanku końcowego '{end_stop}'.")

    end_seq = end_data[0, "Lp przystanku"]

    # ⬇️ SPRAWDZENIE KIERUNKU – czy end_stop jest "dalej" na trasie
    if end_seq <= stop_seq:
        raise ValueError("Przystanek końcowy musi być dalej na trasie niż początkowy.")

    # Obliczenie dystansu do następnego przystanku
    next_stop = df.filter(
        (pl.col("Linia").cast(pl.Utf8).str.strip_chars() == line) &
        (pl.col("Lp przystanku") == stop_seq + 1)
    )

    distance = 0
    far_status = 0
    if not next_stop.is_empty():
        next_lat = next_stop[0, "stop_lat"]
        next_lon = next_stop[0, "stop_lon"]
        distance = geodesic((stop_lat, stop_lon), (next_lat, next_lon)).meters
        far_status = 1 if distance > 250 else 0

    # One-hot kodowanie linii
    line_encoded = encoder.transform([[line]]).flatten()

    # Finalny wektor cech
    input_features = np.concatenate([
        line_encoded,
        [distance, is_weekday, rush_hour, stop_seq, far_status]
    ])

    return input_features
