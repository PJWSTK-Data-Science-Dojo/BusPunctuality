import numpy as np
import torch

import wandb
from data_prep import DataPreparation
from evaluator import Evaluator
from training import Trainer
from model import GNN
import time


def init_wandb(project: str = "bus-delay-prediction"):
    """
    Initialize Weights & Biases logging.

    Args:
        project (str): Name of the W&B project
    """
    return wandb.init(
        project=project
    )

run = init_wandb()
print("Starting data loading...")
data_prep_obj = DataPreparation(data_path="combined_cleaned_with_stops_and_delay_trip_start.parquet", wandb_run=run)
print("DataPreparation object created successfully.")
df = data_prep_obj.load_data(line_number=["126", "210", "10"])[:1000]
print(f"Data loaded successfully., shape: {df.shape}")
df = data_prep_obj.preprocess_data(df)
print(f"Data preprocessed successfully., shape: {df.shape}")

X, y = data_prep_obj.prepare_features_and_target(df)
print(f"Features and target prepared successfully., X shape: {X.shape}, y shape: {y.shape}")

start_time = time.time()
edge_list, stop_id_map = data_prep_obj.prepare_edge_list(df, X)
#todo save
print(f"Edge list and stop ID map prepared successfully., edge_list shape: {len(edge_list)}, stop_id_map size: {len(stop_id_map)}, time taken: {time.time() - start_time} seconds")
edge_index = data_prep_obj.prepare_edge_index(df, X, edge_list, stop_id_map)
start_time = time.time()
print(f"Edge index prepared successfully., edge_index shape: {edge_index.shape}, time taken: {time.time() - start_time} seconds")
data_prep_obj.plot_graph(df, edge_list_ids=edge_list)
#todo save edge index

start_time = time.time()
data_list = data_prep_obj.prepare_graph_features(df, stop_id_map, edge_index)
print(f"Graph features prepared successfully., data_list length: {len(data_list)}, time taken: {time.time() - start_time} seconds")

train_data, val_data, test_data = data_prep_obj.split_data(data_list)
print(f"Data split into train, validation, and test sets., train_data length: {len(train_data)}, val_data length: {len(val_data)}, test_data length: {len(test_data)}")

data_prep_obj.visualize_features_in_train_val_test_splits(train_data, val_data, test_data)

model = GNN(in_channels=train_data[0].x.shape[1], hidden_channels=32, out_channels=1)

trainer_obj = Trainer(model=model, train_data=train_data, val_data=val_data, test_data=test_data, wandb_run=run)
trainer_obj.train(num_epochs=50)
print("Training completed successfully.")

evaluator_obj = Evaluator(wandb_run=run)
for (dataloader, metric_prefix) in zip([trainer_obj.train_loader, trainer_obj.val_loader, trainer_obj.test_loader],
                                       ["train", "val", "test"]):

    out_df = trainer_obj.predict_with_debug(dataloader)
    print(out_df)

    evaluator_obj.calculate_metrics(
        y_true=np.array(out_df.get_column('targets')),
        y_pred=np.array(out_df.get_column('preds')),
        metric_prefix=metric_prefix,
    )
    evaluator_obj.plot_predictions(
        y_true=np.array(out_df.get_column('targets')),
        y_pred=np.array(out_df.get_column('preds')),
        metric_prefix=metric_prefix,


    )
    evaluator_obj.plot_error_distribution(
        y_true=np.array(out_df.get_column('targets')),
        y_pred=np.array(out_df.get_column('preds')),
        metric_prefix=metric_prefix,
    )

    evaluator_obj.plot_per_feature_rmse(
        feature_stats=out_df,
        metric_prefix=metric_prefix,
    )


run.finish()

