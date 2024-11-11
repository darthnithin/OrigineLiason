import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from pyvis.network import Network
from collections import deque

from data_utils import generate_filtered_data

CULLED_FILE_PATH = "filtered_etymology_db.csv.gz"

IMPORTANT_LANGUAGE_LIST = [
                        "French",
                        "Latin",
                        "Ancient Greek",
                        "Old French",
                        "Medieval Latin",
                        "Late Latin",
                    ]

def plot_word_graph(df, word):
    # filter
    sub_df = df[(df["term"] == word) | (df["related_term"] == word)]

    G = nx.DiGraph()

    for _, row in sub_df.iterrows():
        if row["term"] == word:
            G.add_edge(row["term"], row["related_term"], relationship=row["reltype"])
        else:
            G.add_edge(row["related_term"], row["term"], relationship=row["reltype"])

    plt.figure(figsize=(10, 6))
    pos = nx.spring_layout(G)
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=3000,
        node_color="lightblue",
        font_size=10,
        font_weight="bold",
        arrows=True,
    )

    # Draw edge labels for relationships
    edge_labels = {(u, v): d["relationship"] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")

    # Show the plot
    plt.title(f"Graph of '{word}' and Related Terms")
    plt.show()


def plot_word_graph_pyvis(df, word):
    net = Network(
        notebook=False,
        height="750px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        select_menu=True,
        filter_menu=True,
    )
    searched = set()
    #add_word(df, word, net, searched)
    add_word_bfs(df, word, net, searched)

    net.show_buttons()
    html_content = net.generate_html()
    with open("word_graph.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    # net.show("word_graph.html")
    print("done")

def add_word_bfs(df, word, net, searched_words):
    queue = deque([word])
    

    while queue and net.num_nodes() < 125:
        current_word = queue.popleft()
        if current_word in searched_words:
            continue
        print(current_word)
        sub_df = df[(df["term"] == current_word) | (df["related_term"] == current_word)]
        for _, row in sub_df.iterrows():

            term, related_term = str(row["term"]), str(row["related_term"])
            relationship = str(row["reltype"])

            if "of" in relationship or "from" in relationship or relationship.startswith("has"):
                edge_start, edge_end = related_term, term
            else:
                #edge_start, edge_end = word_to_add, related_to_add
                edge_start, edge_end = term, related_term
            
            term_color_condition = (row["lang"] != "English" and edge_start == term)
            related_term_color_condition = (row["related_lang"] != "English" and edge_start == related_term)

            if term not in searched_words:
                net.add_node(
                    term,
                    label=term,
                    title=str(row["lang"]),
                    color="red" if term_color_condition else "blue",
                )
            if related_term not in searched_words:
                net.add_node(
                    related_term,
                    label=related_term,
                    title=str(row["related_lang"]),
                    color="red" if related_term_color_condition else "blue",
                )
            if relationship == "etymologically_related_to":
                net.add_edge(edge_start, edge_end, title=relationship)
            elif relationship not in ["group_derived_root", "cognate_of"]:
                net.add_edge(edge_start, edge_end, title=relationship, arrows="to")
                
            
            if (term not in queue) and (term not in searched_words):
                print(term)
                if str(row['lang']) in IMPORTANT_LANGUAGE_LIST and term == edge_start:
                #if str(row['related_lang']) in IMPORTANT_LANGUAGE_LIST:
                    queue.appendleft(term)
                else:
                    queue.append(term)

            if (related_term not in queue) and (related_term not in searched_words):
                #if str(row['related_lang']) in IMPORTANT_LANGUAGE_LIST and related_term == edge_start:
                print(related_term)

                if str(row['related_lang']) in IMPORTANT_LANGUAGE_LIST and related_term == edge_start:
                    #print(searched_words)
                    queue.appendleft(related_term)
                else:
                    queue.append(related_term)
        searched_words.add(current_word)


def add_word(df, word, net, searched_words):
    sub_df = df[((df["term"] == word) | (df["related_term"] == word))]
    for _, row in sub_df.iterrows():
        # Add nodes and edges

        if (net.num_nodes() < 100) and (
            (row["term"], row["related_term"]) not in searched_words
        ):
            # print(row)
            if pd.notna(row["related_term"]):
                # if term is not english and has an arrow leaving, color red
                if (row["lang"] != "English") and (
                    not (
                        (str(row["reltype"]).split("_")[1] == "of")
                        or (str(row["reltype"].split("_")[0] == "has"))
                    )
                ):
                    net.add_node(
                        row["term"],
                        label=row["term"],
                        title=f"{row['lang']}\n{str(row['position'])}\n{str(row['group_tag'])}",
                        color="red",
                    )
                else:
                    net.add_node(
                        row["term"],
                        label=row["term"],
                        title=f"{row['lang']}\n{str(row['position'])}\n{str(row['group_tag'])}",
                    )
                if (row["related_lang"] != "English") and (
                    (
                        (str(row["reltype"]).split("_")[1] == "of")
                        or (str(row["reltype"].split("_")[0] == "has"))
                    )
                ):
                    net.add_node(
                        row["related_term"],
                        label=row["related_term"],
                        title=row["related_lang"],
                        color="red",
                    )
                else:
                    net.add_node(
                        row["related_term"],
                        label=row["related_term"],
                        title=row["related_lang"],
                    )
                if (str(row["reltype"]).split("_")[1] == "of") or (
                    str(row["reltype"].split("_")[0] == "has")
                ):
                    net.add_edge(
                        row["related_term"],
                        row["term"],
                        title=row["reltype"],
                        arrows="to",
                    )
                else:
                    net.add_edge(
                        row["term"],
                        row["related_term"],
                        title=row["reltype"],
                        arrows="to",
                    )
                searched_words.append((row["term"], row["related_term"]))
                if row["lang"] != "English":
                    add_word(df, row["term"], net, searched_words)
    # print(net.num_nodes(), len(searched_words))


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
            for i, row in result.iterrows():
                print(i, ": ", row)
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
    # search_word(df)
    # plot_word_graph(df, "donation")
    plot_word_graph_pyvis(df, "text")


# Only run main if this script is executed directly
if __name__ == "__main__":
    main()
