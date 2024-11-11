import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import dash_cytoscape as cyto
import dash


from dash import dcc, html, Input, Output
from pyvis.network import Network

from data_utils import generate_filtered_data

CULLED_FILE_PATH = "filtered_etymology_db.csv.gz"
# Check if filtered file exists, generate if it doesn't
if not os.path.exists(CULLED_FILE_PATH):
    generate_filtered_data()

# Load the filtered data and proceed with main functionality
df = pd.read_csv(CULLED_FILE_PATH, compression="gzip")
def create_cytoscape_elements(word, existing_elements=None):
    elements = existing_elements or []
    
    # Filter rows where the term or related term matches the input word
    sub_df = df[(df['term'] == word) | (df['related_term'] == word)]
    
    # Create nodes and edges for Cytoscape
    for _, row in sub_df.iterrows():
        # Add the term node if not already added
        if not any(el.get('data', {}).get('id') == row['term'] for el in elements):
            elements.append({'data': {'id': row['term'], 'label': row['term']}})
        
        # Add the related_term node if not already added
        if not any(el.get('data', {}).get('id') == row['related_term'] for el in elements):
            elements.append({'data': {'id': row['related_term'], 'label': row['related_term']}})
        
        # Add an edge with the relationship type as the label
        elements.append({
            'data': {
                'source': row['term'],
                'target': row['related_term'],
                'label': row['reltype']
            }
        })
    
    return elements
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Interactive Network Graph with Dash Cytoscape"),
    dcc.Input(id='input-word', type='text', value='please', placeholder="Enter a word"),
    html.Button('Update Graph', id='submit-button', n_clicks=0),
    cyto.Cytoscape(
        id='cytoscape-network',
        elements=create_cytoscape_elements('please'),
        layout={'name': 'cose'},  # 'cose' is a physics-based layout
        style={'width': '100%', 'height': '600px', "background-color":'black'},
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'content': 'data(label)',
                    'background-color': '#0074D9',
                    'text-valign': 'center',
                    'color': 'white',
                    'font-size': 8,
                    'width': 15,
                    'height': 15
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'width': 3,
                    'line-color': '#888',
                    'target-arrow-color': '#888',
                    'target-arrow-shape': 'triangle',
                    #'label': 'data(label)',  # Show the relationship type on the edge
                    'font-size': 10
                }
            }
        ]
    ),
    html.Div(id='output-click', style={"marginTop": 20})
])

@app.callback(
    Output('cytoscape-network', 'elements'),
    Output('output-click', 'children'),
    Input('submit-button', 'n_clicks'),
    Input('input-word', 'value'),
    Input('cytoscape-network', 'tapNodeData')
)
def update_graph(n_clicks, word, tapNodeData):
    if tapNodeData:
        clicked_word = tapNodeData['id']
        existing_elements = create_cytoscape_elements(clicked_word, existing_elements=app.layout['cytoscape-network'].elements)
        return existing_elements, f'Expanded on: {clicked_word}'
    else:  # If the update button was clicked
        return create_cytoscape_elements(word), f'Showing graph for: {word}'


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
    searched = []
    add_word(df, word, net, searched)

    net.show_buttons()
    html_content = net.generate_html()
    with open("word_graph.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    # net.show("word_graph.html")
    print("done")


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

    # search_word(df)
    # plot_word_graph(df, "donation")
    #plot_word_graph_pyvis(df, "text")
    app.run_server(debug=True)



# Only run main if this script is executed directly
if __name__ == "__main__":
    main()
