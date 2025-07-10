import torch
import joblib
import datetime
import json
import numpy as np
from models.base_model import BaseModel
from repository.fcnn_architecture import FCNN

class FCNNModel(BaseModel):
    def __init__(self, model_path, scaler_x_path, scaler_y_path, encoder_path, data_path):
        self.model_path = model_path
        self.scaler_x_path = scaler_x_path
        self.scaler_y_path = scaler_y_path
        self.encoder_path = encoder_path
        self.data_path = data_path

    def load(self):
        self.model = FCNN(input_size=19)
        self.model.load_state_dict(torch.load(self.model_path))
        self.model.eval()
        self.scaler_X = joblib.load(self.scaler_x_path)
        self.scaler_y = joblib.load(self.scaler_y_path)
        self.encoder = joblib.load(self.encoder_path)

# TODO this method is invalid, it does not prepare input expected from fcnn model
    def prepare_input(self, start_stop, end_stop, line, date_input, time_input):
        return []
        # with open("data/line_stops_database.json", "r", encoding="utf-8") as f:
        #     stops_by_line = json.load(f)

        # stop_list = stops_by_line.get(line)
        # if not stop_list:
        #     raise ValueError(f"Nie znaleziono linii: {line}")
        # try:
        #     order_start = stop_list.index(start_stop)
        #     order_end = stop_list.index(end_stop)
        # except ValueError:
        #     raise ValueError("Nieprawidłowe przystanki dla danej linii")
        
        # order_diff = order_end - order_start        
        # if order_diff <= 0:
        #     raise ValueError("Przystanek końcowy musi być dalej na trasie niż początkowy")

        # weekday = date_input.weekday()
        # hour = time_input.hour
        # minute = time_input.minute

        # categorical = [[line]]
        # encoded = self.encoder.transform(categorical).toarray()[0]  # np. 16 wymiarów

        # numerical = [weekday, hour, minute, order_start, order_end, order_diff]

        # features = np.concatenate([encoded, numerical])
        # return features

    def predict(self, features):
        return 67.8
        # scaled = self.scaler_X.transform([features])
        # input_tensor = torch.tensor(scaled, dtype=torch.float32)
        # with torch.no_grad():
        #     prediction_scaled = self.model(input_tensor)
        # prediction = self.scaler_y.inverse_transform(prediction_scaled.numpy())[0][0]
        # return prediction
