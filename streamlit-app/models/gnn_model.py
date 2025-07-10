# instance of gnn model
from datetime import datetime
import random
import joblib

from models.base_model import BaseModel
import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from models.graph_nn.data_prep import DataPreparation
from models.graph_nn.model import GNN
from models.graph_nn.training import Trainer
import pickle
from torch_geometric.data import Data
import polars as pl
import logging

logging.basicConfig(level=logging.WARNING)

class GNNModel(BaseModel):
    def __init__(self, gnn_model_path:str, edge_index_path:str, stop_id_map_path:str, line_encoding_path:str, edge_list_path:str, scaler_gnn_path:str):
        print(line_encoding_path)
        self.model_path = gnn_model_path
        self.edge_index_path = edge_index_path
        self.stop_id_map_path = stop_id_map_path
        self.line_encoding_path = line_encoding_path
        self.edge_list_path = edge_list_path
        self.scaler_gnn_path = scaler_gnn_path
        self.logger = logging.getLogger(__name__)

    def load(self, ):
        self.line_mapping = pd.read_csv(self.line_encoding_path)
        self.model = GNN(
            in_channels=11,
            hidden_channels=32,
            out_channels=1
        )

        self.state_dict = torch.load(self.model_path)

        self.model.load_state_dict(self.state_dict)
        self.model.eval()
        self.stop_id_map = pickle.load(open(self.stop_id_map_path, "rb"))
        self.edge_index = pickle.load(open(self.edge_index_path, "rb"))
        self.scaler = joblib.load(open(self.scaler_gnn_path, "rb"))


    def prepare_input(self, start, end, line, date_input, time_input):
        if line not in self.line_mapping['line_name'].values:
            raise ValueError(f"Gnn model can't predict for line {line}. Available lines: {self.line_mapping['line_name'].unique().tolist()}")

        datetime_input = datetime.combine(date_input, time_input)
        data_prep_obj = DataPreparation(data_path="")
        row_dict = {
            "Dzien": date_input,
            "Linia": line,
            "Zadanie": "", # unimportant
            "Lp przystanku": random.randint(1, 26),
            "Przystanek nazwa": start, # unimportant
            "Przystanek numer": 2169, # unimportant
            "Rozkladowy czas przyjazdu": datetime(2023, 1, 1, 4, 11, 0),
            "Rozkladowy czas odjazdu": datetime(2023, 1, 1, 4, 11, 0),
            "Rzeczywisty czas przyjazdu": datetime(2023, 1, 1, 4, 10, 7),
            "Rzeczywisty czas odjazdu": datetime(2023, 1, 1, 4, 10, 7),
            "Rodzaj detekcji": 1, # unimportant
            "Primary Key": "a", # unimportant
            "stop_desc": start,
            "stop_lat": 54,
            "stop_lon": 18.67434,
            "delay": 0, # unimportant
            "scheduled_trip_start": datetime_input,
        }

        df = pl.DataFrame([row_dict])
        self.logger.debug(f"Data loaded successfully., shape: {df.shape}")
        line_encodings = {row['line_name']: row['line_encoded'] for _, row in self.line_mapping.iterrows()}
        df = data_prep_obj.preprocess_data_inference(df, line_encodings=line_encodings)
        self.logger.debug(f"Data preprocessed successfully., shape: {df.shape}")

        X, y = data_prep_obj.prepare_features_and_target(df)
        self.logger.debug(f"Features and target prepared successfully., X shape: {X.shape}, y shape: {y.shape}")
        data_list = data_prep_obj.prepare_graph_features(df, self.stop_id_map, self.edge_index)

        self.trainer_obj = Trainer(model=self.model)
        dataloader = DataLoader(data_list, batch_size=32, shuffle=False)
        return dataloader

    def predict(self, dataloader):
        out_df = self.trainer_obj.predict_with_debug(dataloader)
        if out_df.shape[0] == 0:
            return None
        print(out_df["preds"].to_list()[0])
        return out_df["preds"].to_list()[0]