import os
import pandas as pd

from flask import Flask, render_template_string
from flask_caching import Cache
from pyvis.network import Network
from collections import deque
from io import BytesIO

from data_utils import generate_filtered_data

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = 'cache'

cache = Cache(app)


CULLED_FILE_PATH = "filtered_etymology_db.csv.gz"
if not os.path.exists(CULLED_FILE_PATH):
    generate_filtered_data()

df = pd.read_csv(CULLED_FILE_PATH, compression="gzip")
IMPORTANT_LANGUAGE_LIST = [
                        "French",
                        "Latin",
                        "Ancient Greek",
                        "Old French",
                        "Medieval Latin",
                        "Late Latin",
                    ]




@app.route('/words/<path:words>')
@cache.cached(timeout=300, query_string=True) # 5 min
def plot_word_graph_pyvis(words):
    #print(words)
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

    word_list = words.split('/')
    last_word_or_number = word_list[-1]
    if last_word_or_number.isdigit():
        nodes = int(word_list.pop())
    else:
        nodes = 20
    for (node_mult, word) in enumerate(word_list):
        add_word_bfs(word, net, searched, (node_mult+1)*nodes + net.num_nodes(), word_list, nodes_per=nodes)

    net.show_buttons()
    html_content = net.generate_html()
    html_content = html_content.replace('href="lib/', 'href="/static/lib/')
    html_content = html_content.replace('src="lib/', 'src="/static/lib/')

    #with open(f"./words/{word}word_graph.html", "w", encoding="utf-8") as f:
    #    f.write(html_content)
    print("done")



    return render_template_string(html_content)

def add_word_bfs(word, net, searched_words, node_count, wordlist, nodes_per):
    queue = deque([word])
    path = "/".join(wordlist)
    while queue and (net.num_nodes() < node_count):

        current_word = queue.popleft()
        if current_word in searched_words:
            continue
        #print(current_word)
        sub_df = df[(df["term"] == current_word) | (df["related_term"] == current_word)]
        for _, row in sub_df.iterrows():
            if net.num_nodes() > node_count:
                break
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
                #print(f'{path}/{term}/{nodes_per}')
                net.add_node(
                    term,
                    label=term,
                    #title=str(row["lang"]),
                    title=f'<a href="{path}/{term}/{nodes_per}">{term} ({row["lang"]})</a>',
                    color="red" if term_color_condition else "blue",
                )
            if related_term not in searched_words:
                net.add_node(
                    related_term,
                    label=related_term,
                    #title=str(row["related_lang"]),
                    title=f'<a href="{path}/{related_term}/{nodes_per}">{related_term} ({row["related_lang"]})</a>',
                    color="red" if related_term_color_condition else "blue",
                )
            if relationship == "etymologically_related_to":
                net.add_edge(edge_start, edge_end, title=relationship)
            elif relationship not in ["group_derived_root", "cognate_of"]:
                net.add_edge(edge_start, edge_end, title=relationship, arrows="to")
                
            
            if (term not in queue) and (term not in searched_words):
                #print(term)
                if str(row['lang']) in IMPORTANT_LANGUAGE_LIST and term == edge_start:
                #if str(row['related_lang']) in IMPORTANT_LANGUAGE_LIST:
                    queue.appendleft(term)
                else:
                    queue.append(term)

            if (related_term not in queue) and (related_term not in searched_words):
                #if str(row['related_lang']) in IMPORTANT_LANGUAGE_LIST and related_term == edge_start:
                #print(related_term)

                if str(row['related_lang']) in IMPORTANT_LANGUAGE_LIST and related_term == edge_start:
                    #print(searched_words)
                    queue.appendleft(related_term)
                else:
                    queue.append(related_term)
        searched_words.add(current_word)

@app.route('/clear_cache')
def clear_cache():
    cache.clear()
    print("Cleared Cache!")
    return "Cache Cleared!"





# Only run main if this script is executed directly
if __name__ == "__main__":
    app.run(debug=True)
