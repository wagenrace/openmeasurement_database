#%%
import json
import os

import pandas as pd
from py2neo import Graph
from tqdm import tqdm

from nsc_number2lucence_query import nsc_number2lucence_query

gi50_path = os.path.join("data", "GI50.csv")
nsc2synonymId_path = os.path.join("data", "nsc2synom_id.csv")

with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]

all_nsc_numbers = pd.read_csv(gi50_path, usecols=["NSC"], index_col=False).NSC.unique()
#%% Adding them to the graph
graph = Graph("bolt://localhost:" + port, auth=(user, pswd))

missing_synonyms = []
missing_attribute = []
results = {}
for nsc_number in tqdm(all_nsc_numbers):
    response = graph.run(
        f"""
        CALL {{
            CALL db.index.fulltext.queryNodes('synonymsFullText', "nsc123127 OR (nsc AND 123127)")
            YIELD node, score
            return node limit 10
        }}
        OPTIONAL MATCH (node)-[:IS_ATTRIBUTE_OF]->(c:Compound)
        RETURN node.name as name, node.pubChemSynId as synonymId, c.pubChemCompId as compoundId limit 5
    """
    ).data()
    if len(response) == 0:
        missing_synonyms.append(int(nsc_number))
        continue
    
    for r in response:
        if r.get("compoundId")
    results[int(nsc_number)] = response

with open(r"nsc_number_2_synonymn_raw.json", "w") as f:
    json.dump(results, f)
