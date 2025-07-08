import pandas as pd

# Jeśli masz zainstalowany pyarrow lub fastparquet, to pandas może wczytać plik parquet:
df = pd.read_parquet('../datasets/huge_delays_removed_240625.parquet')


print(df.head())