import pandas as pd
import torch
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, root_mean_squared_error
from typing import Dict, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import wandb
import polars as pl

class Evaluator:
    def __init__(self, save_path: str = "results", wandb_run: wandb.sdk.wandb_run.Run | None = None):
        """
        Initialize the evaluator.

        Args:
            save_path (str): Path to save evaluation results
        """
        self.save_path = Path(save_path)
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.wandb_run = wandb_run

    def calculate_metrics(
            self,
            y_true: np.ndarray,
            y_pred: np.ndarray,
            metric_prefix: str = "test"
    ) -> Dict[str, float]:
        """
        Calculate regression metrics.

        Args:
            y_true (torch.Tensor): True values
            y_pred (torch.Tensor): Predicted values

        Returns:
            Dict[str, float]: Dictionary of metrics
        """

        metrics = {
            f"{metric_prefix}_mse": mean_squared_error(y_true, y_pred),
            f"{metric_prefix}_rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            f"{metric_prefix}_mae": mean_absolute_error(y_true, y_pred),
            f"{metric_prefix}_r2": r2_score(y_true, y_pred)
        }

        self.wandb_run.log(metrics)

        return metrics

    def plot_predictions(
            self,
            y_true: np.ndarray,
            y_pred: np.ndarray,
            title: str = "Predicted vs Actual Delays",
            metric_prefix: str = "test",
            save_name: Optional[str] = f"predictions_vs_actuals_plot"
    ):
        """
        Create scatter plot of predicted vs actual values.

        Args:
            y_true (torch.Tensor): True values
            y_pred (torch.Tensor): Predicted values
            title (str): Plot title
            save_name (str, optional): Name to save the plot
        """
        plt.figure(figsize=(10, 8))


        # Create scatter plot
        sns.scatterplot(x=y_true, y=y_pred, alpha=0.5)

        # plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')

        plt.xlabel("Actual Delay")
        plt.ylabel("Predicted Delay")
        plt.title(title)
        plt.legend()

        if save_name:
            plt.savefig(f"output/{save_name}_{metric_prefix}.png")
            plt.close()
            self.wandb_run.log({f"output/{save_name}_{metric_prefix}_plot": wandb.Image(f"output/{save_name}_{metric_prefix}.png")})
        else:
            plt.show()

    def plot_error_distribution(
            self,
            y_true: np.ndarray,
            y_pred: np.ndarray,
            title: str = "Prediction Error Distribution",
            metric_prefix: str = "test",
            save_name: Optional[str] = "error_distribution_plot"
    ):
        """
        Plot distribution of prediction errors.

        Args:
            y_true (torch.Tensor): True values
            y_pred (torch.Tensor): Predicted values
            title (str): Plot title
            save_name (str, optional): Name to save the plot
        """
        plt.figure(figsize=(10, 6))

        # Calculate errors

        errors = (np.array(y_pred) - np.array(y_true))

        # Create distribution plot
        sns.histplot(errors, kde=True)
        plt.axvline(x=0, color='r', linestyle='--', label='Zero Error')

        plt.xlabel("Prediction Error")
        plt.ylabel("Count")
        plt.title(title)
        plt.legend()

        plt.savefig(f"output/{save_name}_{metric_prefix}.png")
        self.wandb_run.log({f"{save_name}_{metric_prefix}_plot": wandb.Image(f"output/{save_name}_{metric_prefix}.png")})
        plt.close()


    def plot_training_history(
            self,
            history: Dict[str, list],
            save_name: Optional[str] = None
    ):
        """
        Plot training and validation metrics over epochs.

        Args:
            history (Dict[str, list]): Training history
            save_name (str, optional): Name to save the plot
        """
        plt.figure(figsize=(12, 5))

        # Plot loss
        plt.subplot(1, 2, 1)
        plt.plot(history['train_loss'], label='Train Loss')
        plt.plot(history['val_loss'], label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training and Validation Loss')
        plt.legend()

        # Plot RMSE
        plt.subplot(1, 2, 2)
        plt.plot(history['train_rmse'], label='Train RMSE')
        plt.plot(history['val_rmse'], label='Validation RMSE')
        plt.xlabel('Epoch')
        plt.ylabel('RMSE')
        plt.title('Training and Validation RMSE')
        plt.legend()

        plt.tight_layout()

        if save_name:
            plt.savefig(self.save_path / f"{save_name}.png")
            self.wandb_run.log({f"{save_name}_plot": wandb.Image(f"{save_name}.png")})
            plt.close()
        else:
            plt.show()

    def plot_per_feature_rmse(
            self,
            feature_stats: pl.dataframe,
            metric_prefix: str = "test",
            save_name: Optional[str] = "output/metrics_per_feature"
    ):
        """
            Plot MAE and RMSE per feature value.
            :param feature_stats: dict from predict_test with structure:
                                  { "hour=6": {"targets": [...], "preds": [...]}, ... }
            """

        feature_stats = feature_stats.with_columns(
            (pl.col("preds") - pl.col("targets")).pow(2).sqrt().alias("RMSE")
        )

        for feature in feature_stats.columns:
            if feature not in ["targets", "preds", "RMSE"]:

                rmse_per_value = feature_stats.group_by(feature).agg(
                    pl.col("RMSE").mean().alias("mean_RMSE"),
                    pl.col("targets").count().alias("Count")
                )

                if feature in ["arrival_hour", "line_type", "weekday"]:
                    rmse_per_value = rmse_per_value.sort(feature)
                else:
                    rmse_per_value = rmse_per_value.sort("mean_RMSE", descending=True)

                plt.figure(figsize=(12, 6))
                sns.barplot(x=rmse_per_value.get_column(feature).to_list(), y=rmse_per_value.get_column("mean_RMSE").to_list())
                plt.title(f"RMSE per {feature}")
                plt.xlabel(feature)
                if len(rmse_per_value.get_column(feature).to_list()) > 25:
                    plt.xticks(rotation=90)

                plt.ylabel("Root Mean Squared Error")
                plt.tight_layout()
                plt.savefig(f"{save_name}_{metric_prefix}_{feature}_rmse_plot.png")
                self.wandb_run.log({f"{save_name}_{metric_prefix}_{feature}_rmse_plot": wandb.Image(f"{save_name}_{metric_prefix}_{feature}_rmse_plot.png")})
                plt.close()


