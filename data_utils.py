import pandas as pd

filepath = "./etymology.csv.gz"
culled_file_path = "./filtered_etymology_db.csv.gz"


def generate_filtered_data():
    print("Generating filtered data...")
    filtered_data = []
    for chunk in pd.read_csv(filepath, compression="gzip", chunksize=100_000):
        filtered_chunk = chunk[
            (chunk["lang"].isin(["French", "English"]))
            | (chunk["related_lang"].isin(["French", "English", "Latin", "Ancient Greek", "Old French", "Medieval Latin", "Late Latin"]))
        ]
        filtered_data.append(filtered_chunk)

    df_filtered = pd.concat(filtered_data, ignore_index=True)

    df_filtered.to_csv(culled_file_path, compression="gzip", index=False)
    print(f"Filtered data saved to {culled_file_path}")
