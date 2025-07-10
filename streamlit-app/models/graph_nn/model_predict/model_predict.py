import time

import pandas as pd
import torch
from torch_geometric.loader import DataLoader

from graph_nn.data_prep import DataPreparation
from graph_nn.model import GNN
from graph_nn.training import Trainer
import pickle

line_mapping = pd.read_csv("line_encoding.csv")
print(line_mapping)


model = GNN(
    in_channels=11,
    hidden_channels=32,
    out_channels=1
)
state_dict = torch.load("model_weights.pkl")

model.load_state_dict(state_dict)
model.eval()

print(model)

print("Starting data loading...")
data_prep_obj = DataPreparation(data_path="../combined_cleaned_with_stops_and_delay_trip_start.parquet")
print("DataPreparation object created successfully.")
df = data_prep_obj.load_data(line_number=line_mapping.line_name.to_list())
print(f"Data loaded successfully., shape: {df.shape}")
line_encodings = {row['line_name']: row['line_encoded'] for _, row in line_mapping.iterrows()}
df = data_prep_obj.preprocess_data_inference(df, line_encodings=line_encodings)
print(f"Data preprocessed successfully., shape: {df.shape}")

X, y = data_prep_obj.prepare_features_and_target(df)
print(X.columns)
print(f"Features and target prepared successfully., X shape: {X.shape}, y shape: {y.shape}")

# todo if you want to genetate it:
# start_time = time.time()
# edge_list, stop_id_map = data_prep_obj.prepare_edge_list(df, X)
# # save
# with open("edge_list.pkl", "wb") as f:
#     pickle.dump(edge_list, f)
#     print(f"Edge list saved successfully., edge_list shape: {len(edge_list)}")
# with open("stop_id_map.pkl", "wb") as f:
#     pickle.dump(stop_id_map, f)
#     print(f"Stop ID map saved successfully., stop_id_map size: {len(stop_id_map)}")
# print(f"Edge list and stop ID map prepared successfully., edge_list shape: {len(edge_list)}, stop_id_map size: {len(stop_id_map)}, time taken: {time.time() - start_time} seconds")
# edge_index = data_prep_obj.prepare_edge_index(df, X, edge_list, stop_id_map)
# start_time = time.time()
# print(f"Edge index prepared successfully., edge_index shape: {edge_index.shape}, time taken: {time.time() - start_time} seconds")
# with open("edge_index.pkl", "wb") as f:
#     pickle.dump(edge_index, f)
#     print(f"Edge index saved successfully., edge_index shape: {edge_index.shape}")

stop_id_map = pickle.load(open("stop_id_map.pkl", "rb"))
edge_index = pickle.load(open("edge_index.pkl", "rb"))

#todo slice df however you want
data_list = data_prep_obj.prepare_graph_features(df[:100], stop_id_map, edge_index)

trainer_obj = Trainer(model=model)
dataloader = DataLoader(data_list, batch_size=32, shuffle=False)

out_df = trainer_obj.predict_with_debug(dataloader)
print(out_df)
print(out_df["preds"].to_list())
