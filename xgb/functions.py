import datetime
import pandas as pd
from datetime import datetime

df_mapping = pd.read_csv(
    "/teamspace/studios/this_studio/triplet_to_seq.csv",
    parse_dates=["scheduled_departure"]
)

def extract_departure_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds temporal features based on the 'scheduled_departure' column:
    - departure_year, departure_month, departure_day
    - departure_decimal_hour: hour in decimal format (e.g., 14.5 for 14:30)
    - departure_dow: day of the week (0=Monday, ..., 6=Sunday)

    Args:
        df (pd.DataFrame): Input DataFrame with 'scheduled_departure' and 'date' columns.

    Returns:
        pd.DataFrame: DataFrame with additional temporal features.
    """
    df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df['departure_year'] = df['scheduled_departure'].dt.year
    df['departure_month'] = df['scheduled_departure'].dt.month
    df['departure_day'] = df['scheduled_departure'].dt.day
    df['departure_decimal_hour'] = (
        df['scheduled_departure'].dt.hour +
        df['scheduled_departure'].dt.minute / 60
    )
    df['departure_dow'] = df['date'].dt.dayofweek

    return df

def assign_time_of_day(hour):
    """
    Categorizes the time of day based on decimal hour.

    Args:
        hour (float): Hour in decimal format.

    Returns:
        str: One of the categories: 'night', 'morning', 'afternoon', 'evening', 'late_evening', or 'unknown'.
    """
    if pd.isna(hour):
        return 'unknown'
    elif hour <= 5:
        return 'night'
    elif hour <= 11:
        return 'morning'
    elif hour <= 17:
        return 'afternoon'
    elif hour <= 21:
        return 'evening'
    else:
        return 'late_evening'

def find_closest_stop_seq(line: str, stop_name: str, departure_time: datetime) -> int:
    """
    Finds the closest upcoming stop_seq based on provided line, stop name and departure time.

    Args:
        line (str): Bus line number.
        stop_name (str): Bus stop name.
        departure_time (datetime): Scheduled departure time.

    Returns:
        int: Corresponding stop sequence number or -1 if not found.
    """
    matches = df_mapping[
        (df_mapping['line'] == line) &
        (df_mapping['stop_name'] == stop_name) &
        (df_mapping['scheduled_departure'] >= departure_time)
    ]

    if matches.empty:
        print(f"[WARN] No match found for: line={line}, stop_name={stop_name}, time={departure_time}")
        return -1

    closest_row = matches.sort_values(by='scheduled_departure').iloc[0]
    return closest_row['stop_seq']

def prepare_data(stop_name: str, line_number: str, departure_time: datetime) -> pd.DataFrame:
    """
    Prepares input features for delay prediction based on stop, line, and scheduled time.

    Args:
        stop_name (str): Name of the bus stop.
        line_number (str): Bus line number.
        departure_time (datetime): Scheduled departure datetime.

    Returns:
        pd.DataFrame: A single-row DataFrame ready for prediction.
    """
    df = pd.DataFrame([{
        'stop_name': stop_name,
        'line': line_number,
        'scheduled_departure': departure_time,
        'date': departure_time
    }])

    df = extract_departure_features(df)
    df['time_of_day'] = df['departure_decimal_hour'].apply(assign_time_of_day)
    stop_seq = find_closest_stop_seq(line_number, stop_name, departure_time)
    df['stop_seq'] = stop_seq
    df = df.drop(columns=['scheduled_departure', 'date'])

    return df

