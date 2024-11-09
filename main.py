import os
import pandas as pd
from data_utils import generate_filtered_data

CULLED_FILE_PATH = "filtered_etymology_db.csv.gz"


def search_word(df):
    while True:
        word = input("Enter a word to search (or type 'quit' to exit): ").strip()
        if word.lower() == "quit":
            print("Exiting the search.")
            break

        # Search for the word in both the 'term' and 'related_term' columns
        result = df[(df["term"] == word) | (df["related_term"] == word)]

        if not result.empty:
            print("Results found:")
            print(result)
        else:
            print(f"No results found for '{word}'. Please try another word.")


def main():
    # Check if filtered file exists, generate if it doesn't
    if not os.path.exists(CULLED_FILE_PATH):
        generate_filtered_data()

    # Load the filtered data and proceed with main functionality
    df = pd.read_csv(CULLED_FILE_PATH, compression="gzip")
    print(df.head())


# Only run main if this script is executed directly
if __name__ == "__main__":
    main()
