from models.base_model import BaseModel
import json
import numpy as np

class GNNModel(BaseModel):

    def __init__(self, model_path, scaler_x_path, scaler_y_path, encoder_path, data_path):
        self.model_path = model_path
        self.scaler_x_path = scaler_x_path
        self.scaler_y_path = scaler_y_path
        self.encoder_path = encoder_path
        self.data_path = data_path

    def load(self):
        self.loaded = True  # Symulacja załadowania modelu

    def prepare_input(self, start_stop, end_stop, line, date_input, time_input):
        return []

    def predict(self, features):
        return 56.0  # Mocked delay in seconds
