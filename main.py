import pandas as pd

file_path = (
    "../BDG2_Download/building-data-genome-project-2/"
    "data/meters/cleaned/electricity_cleaned.csv"
)

df = pd.read_csv(file_path, nrows=5)

print("Dataset shape (first 5 rows):", df.shape)

print("\nColumn names:")
print(df.columns.tolist()[:15])

print("\nFirst 5 rows:")
print(df.head().to_string())

print("\nData types:")
print(df.dtypes.head(15))