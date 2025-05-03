import polars as pl
import datetime as dt
import numpy as np
from workalendar.europe.poland import Poland
print("Downloading data from do_oddania")
df_202301 = pl.read_csv("do_oddania/20230101-20230531.csv", separator=";",schema_overrides={"Linia": pl.Utf8, "Rzeczywisty czas przyjazdu": pl.Datetime, "Rzeczywisty czas odjazdu": pl.Datetime, "Rozkladowy czas przyjazdu": pl.Datetime, "Rozkladowy czas odjazdu": pl.Datetime, "Dzien": pl.Datetime},     null_values="NULL"
)

df_202306 = pl.read_csv("do_oddania/20230601-20231231.csv", separator=";",schema_overrides={"Linia": pl.Utf8, "Rzeczywisty czas przyjazdu": pl.Datetime, "Rzeczywisty czas odjazdu": pl.Datetime, "Rozkladowy czas przyjazdu": pl.Datetime, "Rozkladowy czas odjazdu": pl.Datetime, "Dzien": pl.Datetime}, null_values="NULL")
df_202401 = pl.read_csv("do_oddania/20240101-20240531.csv", separator=";",schema_overrides={"Linia": pl.Utf8, "Rzeczywisty czas przyjazdu": pl.Datetime, "Rzeczywisty czas odjazdu": pl.Datetime, "Rozkladowy czas przyjazdu": pl.Datetime, "Rozkladowy czas odjazdu": pl.Datetime, "Dzien": pl.Datetime},  null_values="NULL")
df_202406 = pl.read_csv("do_oddania/20240601-20250115.csv", separator=";",schema_overrides={"Linia": pl.Utf8, "Rzeczywisty czas przyjazdu": pl.Datetime, "Rzeczywisty czas odjazdu": pl.Datetime, "Rozkladowy czas przyjazdu": pl.Datetime, "Rozkladowy czas odjazdu": pl.Datetime, "Dzien": pl.Datetime}, null_values="NULL")


df = pl.concat([df_202301, df_202306, df_202401, df_202406])

def transform_date_columns(_df, cols=None):
    if not cols:
        cols  = ['Rozkladowy czas przyjazdu', 'Rozkladowy czas odjazdu', 'Rzeczywisty czas przyjazdu', 'Rzeczywisty czas odjazdu', 'Dzien']
    for c in cols:
        _df[c] = pl.to_datetime(_df[c], errors='coerce')
    return _df

print("Transforming date columns")
df = transform_date_columns(df)
print("Calculating delay")
df = df.with_columns([
    pl.when(pl.col("Lp przystanku") == 1)
    .then(
        pl.when(pl.col("Rzeczywisty czas odjazdu") <= pl.col("Rozkladowy czas odjazdu"))
        .then(-(pl.col("Rozkladowy czas odjazdu") - pl.col("Rzeczywisty czas odjazdu")).dt.total_seconds())
        .otherwise((pl.col("Rzeczywisty czas odjazdu") - pl.col("Rozkladowy czas odjazdu")).dt.total_seconds())
    )
    .otherwise(
        pl.when(pl.col("Rzeczywisty czas przyjazdu") <= pl.col("Rozkladowy czas przyjazdu"))
        .then(-(pl.col("Rozkladowy czas przyjazdu") - pl.col("Rzeczywisty czas przyjazdu")).dt.total_seconds())
        .otherwise((pl.col("Rzeczywisty czas przyjazdu") - pl.col("Rozkladowy czas przyjazdu")).dt.total_seconds())
    )
    .alias("delay")
])

print("Saving to csv")
# df.write_csv("dataset_with_delay.csv", separator=";")

import json
from typing import List, Optional, Dict

df = pl.read_csv("dataset_with_delay.csv", separator=";", schema_overrides={"Linia": pl.Utf8, "Rozkladowy czas przyjazdu": pl.Datetime, "Rozkladowy czas odjazdu": pl.Datetime, "Rzeczywisty czas przyjazdu": pl.Datetime, "Rzeczywisty czas odjazdu": pl.Datetime}, null_values="NULL")

class Stop:
    def __init__(self, stopId: int, stopCode: str, stopName: str, stopShortName: str, stopDesc: str,
                 subName: str, date: str, zoneId: int, zoneName: str, virtual: int, nonpassenger: int, depot: int,
                 ticketZoneBorder: int, onDemand: int, activationDate: str, stopLat: float, stopLon: float,
                 stopType: str, stopUrl: str, locationType: Optional[str], parentStation: Optional[str],
                 stopTimezone: Optional[str], wheelchairBoarding: Optional[str]):
        self.stopId = stopId
        self.stopCode = stopCode
        self.stopName = stopName
        self.stopShortName = stopShortName
        self.stopDesc = stopDesc
        self.subName = subName
        self.date = date
        self.zoneId = zoneId
        self.zoneName = zoneName
        self.virtual = virtual
        self.nonpassenger = nonpassenger
        self.depot = depot
        self.ticketZoneBorder = ticketZoneBorder
        self.onDemand = onDemand
        self.activationDate = activationDate
        self.stopLat = stopLat
        self.stopLon = stopLon
        self.stopType = stopType
        self.stopUrl = stopUrl
        self.locationType = locationType
        self.parentStation = parentStation
        self.stopTimezone = stopTimezone
        self.wheelchairBoarding = wheelchairBoarding

    def __repr__(self):
        return f"Stop({self.stopId}, {self.stopName},{self.stopDesc} {self.stopLat}, {self.stopLon})"


class Data:
    def __init__(self, lastUpdate: str, stops: List[Stop]):
        self.lastUpdate = lastUpdate
        self.stops = stops

    def __repr__(self):
        return f"Data({self.lastUpdate}, {len(self.stops)} stops)"


def load_json_to_objects(file_path: str) -> Dict[int, Stop]:
    with open(file_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    stop_dict = {}

    for date, entry in input_data.items():
        for stop in entry['stops']:
            stop['stopType'] = stop['type']
            del stop['type']

            stop_obj = Stop(**stop)
            stop_dict[stop_obj.stopId] = stop_obj

    return stop_dict


file_path = 'stops.json'
stop_dict = load_json_to_objects(file_path)

print(stop_dict.get(1024))  # Example: Access stop with stopId 1024`
print(stop_dict.get(1024).stopDesc)
print(len(stop_dict))

# Convert stop_dict to a Polars DataFrame
stop_info_df = pl.DataFrame([
    {"Przystanek numer": sid, "stop_desc": s.stopDesc, "stop_lat": s.stopLat, "stop_lon": s.stopLon}
    for sid, s in stop_dict.items()
])


print("Adding stop info")
df = df.join(stop_info_df, on="Przystanek numer", how="left")



def categorize_time_of_day_expr(hour_col: pl.Expr) -> pl.Expr:
    return (
        pl.when((hour_col >= 23) | (hour_col <= 4)).then("Night")
        .when((hour_col >= 5) & (hour_col <= 7)).then("Early Morning")
        .when((hour_col >= 8) & (hour_col <= 11)).then("Morning")
        .when((hour_col >= 12) & (hour_col <= 14)).then("Afternoon")
        .when((hour_col >= 15) & (hour_col <= 18)).then("Evening")
        .otherwise("Late Evening")
    )




def prep_df_for_modelling(df: pl.DataFrame) -> pl.DataFrame:
    holidays = {d[0] for d in Poland().holidays(2023)} | \
               {d[0] for d in Poland().holidays(2024)} | \
               {d[0] for d in Poland().holidays(2025)}

    # df = df.with_columns([
    #     pl.col("Rozkladowy czas przyjazdu").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False).alias(
    #         "Rozkladowy czas przyjazdu")
    # ])
    print(df.columns)

    df = df.with_columns([
        (pl.col("Rozkladowy czas przyjazdu").dt.weekday() < 5).alias("Rozkladowy_czas_przyjazdu_is_weekday"),
        pl.col("Rozkladowy czas przyjazdu").dt.hour().alias("Rozkladowy_czas_przyjazdu_hour"),
        pl.col("Rozkladowy czas przyjazdu").dt.date().is_in(list(holidays)).alias(
            "Rozkladowy_czas_przyjazdu_is_holiday"),
        # categorize_time_of_day_expr(pl.col("Rozkladowy czas przyjazdu").dt.hour()).alias(
        #     "Rozkladowy_czas_przyjazdu_time_of_day")
    ])

    return df

print("Preparing df for modelling")
df = prep_df_for_modelling(df)

# df = pl.read_csv("df_for_modelling_polars.csv", separator=";", schema_overrides={"Linia": pl.Utf8,"Rozkladowy czas przyjazdu": pl.Datetime, "Rozkladowy czas odjazdu": pl.Datetime, "Rzeczywisty czas przyjazdu": pl.Datetime, "Rzeczywisty czas odjazdu": pl.Datetime}, null_values="NULL")

# Original column names
original_columns = [
    'Dzien', 'Linia', 'Zadanie', 'Lp przystanku', 'Przystanek nazwa', 'Przystanek numer',
    'Rozkladowy czas przyjazdu', 'Rozkladowy czas odjazdu',
    'Rzeczywisty czas przyjazdu', 'Rzeczywisty czas odjazdu',
    'Rodzaj detekcji', 'delay', 'stop_desc', 'stop_lat', 'stop_lon',
    'Rozkladowy_czas_przyjazdu_is_weekday',
    'Rozkladowy_czas_przyjazdu_hour',
    'Rozkladowy_czas_przyjazdu_is_holiday'
]

# Mapping to concise English names
rename_dict = {
    'Dzien': 'date',
    'Linia': 'line',
    'Zadanie': 'task',
    'Lp przystanku': 'stop_seq',
    'Przystanek nazwa': 'stop_name',
    'Przystanek numer': 'stop_id',
    'Rozkladowy czas przyjazdu': 'scheduled_arrival',
    'Rozkladowy czas odjazdu': 'scheduled_departure',
    'Rzeczywisty czas przyjazdu': 'actual_arrival',
    'Rzeczywisty czas odjazdu': 'actual_departure',
    'Rodzaj detekcji': 'detection_type',
    'delay': 'delay',
    'stop_desc': 'stop_desc',
    'stop_lat': 'stop_lat',
    'stop_lon': 'stop_lon',
    'Rozkladowy_czas_przyjazdu_is_weekday': 'is_weekday',
    'Rozkladowy_czas_przyjazdu_hour': 'arrival_hour',
    'Rozkladowy_czas_przyjazdu_is_holiday': 'is_holiday'
}

# Rename in a Polars DataFrame
df = df.rename(rename_dict)

# def append_weather_info(df: pl.DataFrame, weather_df: pl.DataFrame) -> pl.DataFrame:
#     return (
#         df.with_columns([
#             pl.col("actual_arrival").dt.date().alias("datetime")
#         ])
#         .join(weather_df.with_columns(pl.col("datetime").cast(pl.Date)), on="datetime", how="left")
#     )
#
#
# print("Preparing weather data")
# weather_df = pl.read_csv("Gdansk 2023-01-01 to 2025-01-15.csv")
# df = append_weather_info(df, weather_df)

print("Saving df for modelling")
df.write_csv("df_for_modelling_polars_no_weatther.csv", separator=";")
print(df.columns)

