#%%
import json
import os

import numpy as np
import pandas as pd
from py2neo import Graph


gi50_path = os.path.join("data", "GI50.csv")
nsc2synonymId_path = os.path.join("data", "nsc2synom_id.csv")

with open("config.json") as f:
    config = json.load(f)

neo4j_url = config.get("neo4jUrl", "bolt://localhost:7687")
user = config.get("user", "neo4j")
pswd = config.get("pswd", "password")
neo4j_import_loc = config["neo4j_import_loc"]

result_dir = os.path.join("results", "completing_nscs")
os.makedirs(result_dir, exist_ok=True)

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
print(f"GI50 size {gi50.shape}")
with open(os.path.join(result_dir, r"nsc_number_2_single_synonym.json")) as f:
    nsc_2_synonyms_part_1 = json.load(f)

with open(os.path.join(result_dir, r"nsc_number_2_common_synonyms.json")) as f:
    nsc_2_synonyms_part_2 = json.load(f)

nsc_2_synonyms = nsc_2_synonyms_part_1 | nsc_2_synonyms_part_2
# gi50.to_csv(os.path.join(neo4j_import_loc, "gi50.csv"))

with open(r"cellline_nci60_to_chembl.json") as f:
    cell_line_lookup = json.load(f)

gi50["CELL_NAME_2"] = gi50["CELL_NAME"].map(cell_line_lookup)


def nsc2chemcial_name(nsc: int):
    return nsc_2_synonyms.get(str(nsc), {"name": None})["name"]


gi50["CHEMICAL_NAME"] = gi50["NSC"].apply(str).map(nsc2chemcial_name)

gi50 = gi50.fillna(value=np.nan)
gi50_filtered = gi50.dropna()
print(f"Filtered GI50 size {gi50_filtered.shape}")
#%% Adding them to the graph
graph = Graph(neo4j_url, auth=(user, pswd))

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
