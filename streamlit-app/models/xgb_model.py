from datetime import datetime
import pandas as pd
from pycaret.regression import load_model
from models.base_model import BaseModel
from utils.xgb_utils import extract_departure_features, assign_time_of_day

class XGBModel(BaseModel):
    def __init__(self, model_path, data_path=None, scaler_x_path=None, scaler_y_path=None, encoder_path=None):
        """
        model_path: path to the saved PyCaret model (.pkl)
        data_path: path to mapping CSV with triplet_to_seq data
        encoder_path: not used in this implementation
        """
        self.model_path = model_path
        self.data_path = data_path
        self.encoder_path = encoder_path
        self.df_mapping = None

    def load(self):
        """
        Load the pretrained pipeline saved by PyCaret and mapping CSV.
        """
        self.model = load_model(self.model_path)

        if self.data_path:
            self.df_mapping = pd.read_csv(
                self.data_path,
                parse_dates=['scheduled_departure'],
                infer_datetime_format=True
            )
        else:
            raise ValueError("data_path must be provided to load stop sequence mapping.")

    def find_closest_stop_seq(
        self,
        line: str,
        stop_name: str,
        departure_time: datetime
    ) -> int:
        """
        Finds the closest upcoming stop_seq based on provided line, stop name and departure time.
        """
        if self.df_mapping is None:
            raise RuntimeError("Mapping DataFrame not loaded. Call load() first.")

        matches = self.df_mapping[
            (self.df_mapping['line'] == line) &
            (self.df_mapping['stop_name'] == stop_name) &
            (self.df_mapping['scheduled_departure'] >= departure_time)
        ]

        if matches.empty:
            print(f"[WARN] No match found for: line={line}, stop_name={stop_name}, time={departure_time}")
            return -1

        closest_row = matches.sort_values(by='scheduled_departure').iloc[0]
        return int(closest_row['stop_seq'])

    def prepare_data(
        self,
        stop_name: str,
        line_number: str,
        departure_time: datetime
    ) -> pd.DataFrame:
        """
        Prepares input features for delay prediction based on stop, line, and scheduled time.
        """
        df = pd.DataFrame([{
            'stop_name': stop_name,
            'line': line_number,
            'scheduled_departure': departure_time,
            'date': departure_time
        }])

        df = extract_departure_features(df)
        df['time_of_day'] = df['departure_decimal_hour'].apply(assign_time_of_day)
        df['stop_seq'] = self.find_closest_stop_seq(line_number, stop_name, departure_time)
        df = df.drop(columns=['scheduled_departure', 'date'])

        return df

    def prepare_input(
        self,
        start_stop,
        end_stop,
        line,
        date_input,
        time_input
    ) -> pd.DataFrame:
        """
        Prepare input features DataFrame for prediction.
        """
        departure_dt = datetime.combine(date_input, time_input)
        return self.prepare_data(start_stop, line, departure_dt)

    def predict(self, features: pd.DataFrame) -> float:
        """
        Run inference on the prepared feature DataFrame.
        Returns the predicted delay in seconds as a float.
        """
        preds = self.model.predict(features)
        return float(preds[0])
