import polars as pl

file_path = "/kaggle/input/buspunctuality/przejazdy_5_12_stycznia_2025.csv"

try:
    df = pl.read_csv(
        file_path,
        separator=";",
        null_values="NULL",
        schema_overrides={
            "date": pl.Datetime,
            "line": pl.Utf8,
            "task": pl.Utf8,
            "stop_seq": pl.Int64,
            "stop_name": pl.Utf8,
            "stop_id": pl.Int64,
            "scheduled_arrival": pl.Datetime,
            "scheduled_departure": pl.Datetime,
            "actual_arrival": pl.Datetime,
            "actual_departure": pl.Datetime,
            "detection_type": pl.Utf8,
            "delay": pl.Float64,
            "stop_desc": pl.Utf8,
            "stop_lat": pl.Float64,
            "stop_lon": pl.Float64,
            "is_weekday": pl.Boolean,
            "arrival_hour": pl.Int64,
            "is_holiday": pl.Boolean
        }
    )
    print(df["line"].unique().to_list())
    unique_lines = df["line"].unique().to_list()
    print(f"Liczba unikalnych linii: {len(unique_lines)}")



except FileNotFoundError:
    print(f"Plik {file_path} nie został znaleziony.")
except Exception as e:
    print(f"Wystąpił błąd podczas wczytywania pliku: {e}")


import polars as pl
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.model_selection import KFold
from geopy.distance import geodesic

file_path = "/kaggle/input/bus-punctuality-dataset/df_for_modelling_v2.csv"
print("Rozpoczęto wczytywanie danych...")
df = pl.read_csv(
    file_path,
    separator=";",
    null_values="NULL",
    schema_overrides={
        "date": pl.Datetime,
        "line": pl.Utf8,
        "task": pl.Utf8,
        "stop_seq": pl.Int64,
        "stop_name": pl.Utf8,
        "stop_id": pl.Int64,
        "scheduled_arrival": pl.Datetime,
        "scheduled_departure": pl.Datetime,
        "actual_arrival": pl.Datetime,
        "actual_departure": pl.Datetime,
        "detection_type": pl.Utf8,
        "delay": pl.Float64,
        "stop_desc": pl.Utf8,
        "stop_lat": pl.Float64,
        "stop_lon": pl.Float64,
        "is_weekday": pl.Boolean,
        "arrival_hour": pl.Int64,
        "is_holiday": pl.Boolean
    }
)
print(f"Dane wczytane pomyślnie. Liczba wierszy: {len(df)}")

print("Obliczanie Trip Time...")
df = df.with_columns(
    (pl.col("actual_arrival") - pl.col("date")).dt.total_seconds().alias("trip_time")
)
print("Trip Time obliczony.")

print("Analiza danych: statystyki Trip Time przed filtracją...")
trip_time_stats = df["trip_time"].describe()
print(trip_time_stats)

print("Filtracja Trip Time...")
df = df.filter(pl.col("trip_time") < 7200)  # tylko <2h, tymczasowo bez >0
print(f"Po filtracji: {len(df)} wierszy.")
if len(df) == 0:
    print("BŁĄD: Ramka danych jest pusta po filtracji trip_time. Sprawdź dane w kolumnie trip_time.")
    exit()

print("Obliczanie odległości między przystankami...")
df = df.sort(["line", "task", "stop_seq"])
df = df.with_columns(
    pl.col("stop_lat").shift(-1).alias("next_stop_lat"),
    pl.col("stop_lon").shift(-1).alias("next_stop_lon")
)
df = df.with_columns(
    pl.when(pl.col("next_stop_lat").is_not_null())
    .then(
        pl.struct(["stop_lat", "stop_lon", "next_stop_lat", "next_stop_lon"])
        .map_elements(
            lambda x: geodesic(
                (x["stop_lat"], x["stop_lon"]),
                (x["next_stop_lat"], x["next_stop_lon"])
            ).meters,
            return_dtype=pl.Float64
        )
    )
    .otherwise(None)
    .alias("distance")
)
print("Odległości obliczone.")

print("Dodawanie cechy rush_hour...")
df = df.with_columns(
    pl.col("arrival_hour").is_in([6, 7, 8, 9, 15, 16, 17, 18]).cast(pl.Int8).alias("rush_hour")
)
print("Cechą rush_hour dodana.")

print("Dodawanie cechy far_status...")
df = df.with_columns(
    (pl.col("distance") > 250).cast(pl.Int8).alias("far_status")
)
print("Cechą far_status dodana.")

print("Analiza brakujących danych przed drop_nulls...")
null_counts = df.select(pl.all().is_null().sum()).to_dicts()
print("Liczba nulli w każdej kolumnie:", null_counts)

print("Usuwanie brakujących danych w kluczowych kolumnach...")
df = df.drop_nulls(subset=["line", "trip_time", "distance", "stop_seq", "is_weekday", "rush_hour", "far_status"])
print(f"Po drop_nulls: {len(df)} wierszy.")
if len(df) == 0:
    print("BŁĄD: Ramka danych jest pusta po drop_nulls. Sprawdź brakujące wartości w kluczowych kolumnach.")
    exit()

print("Analiza danych: statystyki po czyszczeniu...")
print(df[["trip_time", "distance", "stop_seq"]].describe())

print("Kodowanie one-hot dla linii...")
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
line_encoded = encoder.fit_transform(df[["line"]].to_numpy())
line_encoded_cols = [f"line_{val}" for val in encoder.categories_[0]]
line_encoded_df = pl.DataFrame(line_encoded, schema=line_encoded_cols)
print(f"Kodowanie one-hot zakończone: {len(line_encoded_cols)} linii.")

print("Przygotowanie cech wejściowych...")
features = line_encoded_cols + ["distance", "is_weekday", "rush_hour", "stop_seq", "far_status"]
X = pl.concat([line_encoded_df, df.select(["distance", "is_weekday", "rush_hour", "stop_seq", "far_status"])], how="horizontal").to_numpy()
y = df["trip_time"].to_numpy().reshape(-1, 1)
print("Cechy wejściowe przygotowane.")

print("Skalowanie cech i Trip Time...")
scaler_X = MinMaxScaler()
X_scaled = scaler_X.fit_transform(X)
scaler_y = MinMaxScaler()
y_scaled = scaler_y.fit_transform(y)
print("Cechy i Trip Time przeskalowane.")

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

print("Inicjalizacja walidacji krzyżowej...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
kf = KFold(n_splits=5, shuffle=True, random_state=42)
rmse_scores = []
print(f"Walidacja krzyżowa zainicjalizowana (5 foldów), urządzenie: {device}.")

for fold, (train_idx, val_idx) in enumerate(kf.split(X_scaled)):
    print(f"\nRozpoczęto fold {fold+1}...")
    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
    y_train, y_val = y_scaled[train_idx], y_scaled[val_idx]
    
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).to(device)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32).to(device)
    y_val_tensor = torch.tensor(y_val, dtype=torch.float32).to(device)
    
    model = FCNN(input_size=X_scaled.shape[1]).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    
    num_epochs = 200
    batch_size = 64
    patience = 10
    best_loss = float('inf')
    epochs_no_improve = 0
    print(f"Trening folda {fold+1} rozpoczęty (max 200 epok, early stopping po {patience} epok)...")
    
    for epoch in range(num_epochs):
        model.train()
        for i in range(0, len(X_train), batch_size):
            batch_X = X_train_tensor[i:i+batch_size]
            batch_y = y_train_tensor[i:i+batch_size]
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
        
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val_tensor)
            val_loss = criterion(val_outputs, y_val_tensor).item()
        
        if val_loss < best_loss:
            best_loss = val_loss
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping w epoce {epoch+1}.")
                break
    
    print(f"Trening folda {fold+1} zakończony. Ewaluacja...")
    model.eval()
    with torch.no_grad():
        val_outputs = model(X_val_tensor)
        val_outputs_unscaled = scaler_y.inverse_transform(val_outputs.cpu().numpy())
        y_val_unscaled = scaler_y.inverse_transform(y_val)
        mse = np.mean((val_outputs_unscaled - y_val_unscaled) ** 2)
        rmse = np.sqrt(mse)
        rmse_scores.append(rmse)
        print(f"Fold {fold+1}, RMSE: {rmse:.2f} seconds")

print("\nWszystkie foldy zakończone.")
print(f"Średnie RMSE z walidacji krzyżowej: {np.mean(rmse_scores):.2f} ± {np.std(rmse_scores):.2f} seconds")

# Po treningu modelu (na końcu kodu)
import joblib

# Zapisz model
torch.save(model.state_dict(), "fcnn_model.pth")

# Zapisz skalery i encoder
joblib.dump(scaler_X, "scaler_X.pkl")
joblib.dump(scaler_y, "scaler_y.pkl")
joblib.dump(encoder, "onehot_encoder.pkl")

print("Model, skalery i encoder zapisane.")