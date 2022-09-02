#%%
import json
import os

import pandas as pd
from py2neo import Graph


gi50_path = os.path.join("data", "GI50.csv")
nsc2synonymId_path = os.path.join("data", "nsc2synom_id.csv")

with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]

gi50 = pd.read_csv(
    gi50_path,
    usecols=[
        "NSC",
        "EXPID",
        "CONCENTRATION_UNIT",
        "LOG_HI_CONCENTRATION",
        "PANEL_NAME",
        "CELL_NAME",
        "AVERAGE",
    ],
)
gi50.to_csv(os.path.join(neo4j_import_loc, "gi50.csv"))
nsc2synonymId = pd.read_csv(nsc2synonymId_path)
nsc2synonymId.synonym_id = nsc2synonymId.synonym_id.str.replace("synonym:MD5_", "")
nsc2synonymId.head()

merged_gi50 = pd.merge(gi50, nsc2synonymId)
#%% Adding them to the graph
graph = Graph("bolt://localhost:" + port, name="test", auth=(user, pswd))

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
