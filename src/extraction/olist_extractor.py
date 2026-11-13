
import pandas as pd
from pathlib import Path


def extract_csv_files(data_path="data/raw/"):
    data_folder = Path(data_path)
    csv_files = data_folder.glob("*.csv")

    dataframes = {}

    for file in csv_files:
        df = pd.read_csv(file)
        dataframes[file.stem] = df

    return dataframes


if __name__ == "__main__":
    data = extract_csv_files()

    print("Files extracted:", len(data))

    for name, df in data.items():
        print(name, df.shape)
