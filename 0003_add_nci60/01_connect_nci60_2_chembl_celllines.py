#%%
import json
from os.path import join as path_join

import pandas as pd
from py2neo import Graph

from cellline2lucence_query import cellline2lucence_query

with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]

gi50 = pd.read_csv(path_join("data", "GI50.csv"))

#%% Adding them to the graph
graph = Graph("bolt://localhost:" + port, auth=(user, pswd))

results = {}
for cell_name in gi50.CELL_NAME.value_counts().keys():
    response = graph.run(
        f"""
        CALL db.index.fulltext.queryNodes('cellLineFullText', "{cellline2lucence_query(cell_name)}")
        YIELD node, score
        return node.label as label limit 10
    """
    ).data()
    results[cell_name] = [i["label"] for i in response]

with open(r"cellline_nci60_to_chembl_raw.json", "w") as f:
    json.dump(results, f)

print(
    "Look at the cellline_nci60_to_chembl_raw, manual replace the list with the best match and save it as cellline_nci60_to_chembl.json"
)
