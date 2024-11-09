import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from data_utils import generate_filtered_data

CULLED_FILE_PATH = "filtered_etymology_db.csv.gz"


def plot_word_graph(df, word):
    #filter
    sub_df = df[(df['term'] == word) | (df['related_term'] == word)]

    G = nx.DiGraph()

    for _, row in sub_df.iterrows():
        if row['term'] == word:
            G.add_edge(row['term'], row['related_term'], relationship=row['reltype'])
        else:
            G.add_edge(row['related_term'], row['term'], relationship=row['reltype'])
    
    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color="lightblue", font_size=10, font_weight="bold", arrows=True)
    
    # Draw edge labels for relationships
    edge_labels = {(u, v): d['relationship'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")

    # Show the plot
    plt.title(f"Graph of '{word}' and Related Terms")
    plt.show()

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
            for (i, row) in result.iterrows():
                print(i,": ", row)
            selection = int(input("Select an index: ").strip())
            print(selection)
            selected_word = result.loc[selection]
            print(selected_word)
        else:
            print(f"No results found for '{word}'. Please try another word.")


def main():
    # Check if filtered file exists, generate if it doesn't
    if not os.path.exists(CULLED_FILE_PATH):
        generate_filtered_data()

    # Load the filtered data and proceed with main functionality
    df = pd.read_csv(CULLED_FILE_PATH, compression="gzip")
    #search_word(df)
    plot_word_graph(df, "donation")


# Only run main if this script is executed directly
if __name__ == "__main__":
    main()
