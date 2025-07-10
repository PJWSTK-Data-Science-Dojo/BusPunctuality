from datetime import datetime
import pandas as pd


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
    df = df.copy()
    df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    dt = df['scheduled_departure']
    df['departure_year'] = dt.dt.year
    df['departure_month'] = dt.dt.month
    df['departure_day'] = dt.dt.day
    df['departure_decimal_hour'] = dt.dt.hour + dt.dt.minute / 60
    df['departure_dow'] = df['date'].dt.dayofweek

    return df


def assign_time_of_day(hour: float) -> str:
    """
    Categorizes the time of day based on decimal hour.

    Args:
        hour (float): Hour in decimal format.

    Returns:
        str: One of the categories: 'night', 'morning', 'afternoon', 'evening', 'late_evening', or 'unknown'.
    """
    if pd.isna(hour):
        return 'unknown'
    if hour <= 5:
        return 'night'
    if hour <= 11:
        return 'morning'
    if hour <= 17:
        return 'afternoon'
    if hour <= 21:
        return 'evening'
    return 'late_evening'