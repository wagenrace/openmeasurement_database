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

# Default are for local testing
neo4j_url = config.get("neo4jUrl", "bolt://localhost:7687")
user = config.get("user", "neo4j")
pswd = config.get("pswd", "password")

all_nsc_numbers = pd.read_csv(gi50_path, usecols=["NSC"], index_col=False).NSC.unique()

result_dir = os.path.join("results", "completing_nscs")
os.makedirs(result_dir, exist_ok=True)

#%% Adding them to the graph
graph = Graph(neo4j_url, auth=(user, pswd))

synonym_without_compounds = []
missing_nsc_number = []
wrong_synonyms = {}
results = {}
for nsc_number in tqdm(all_nsc_numbers):
    response = graph.run(
        f"""
        CALL {{
            CALL db.index.fulltext.queryNodes('synonymsFullText', "{nsc_number2lucence_query(nsc_number)}")
            YIELD node, score
            return node limit 10
        }}
        MATCH (node)-[:IS_ATTRIBUTE_OF]->(c:Compound)
        RETURN node.name as name, node.pubChemSynId as synonymId, c.pubChemCompId as compoundId limit 5
    """
    ).data()
    if len(response) == 0:
        missing_nsc_number.append(int(nsc_number))
        continue

    filtered_response = []
    for r in response:
        if not (name := r.get("name", "").lower()) in [
            f"nsc{nsc_number}",
            f"nsc {nsc_number}",
            f"nsc-{nsc_number}",
        ]:
            continue
        if r.get("compoundId") is None:
            continue
        filtered_response.append(r)

    if filtered_response:
        results[int(nsc_number)] = filtered_response
    else:
        missing_nsc_number.append(int(nsc_number))

with open(os.path.join(result_dir, r"nsc_number_2_synonyms.json"), "w") as f:
    json.dump(results, f)

with open(os.path.join(result_dir, r"nsc_number_no_connection.json"), "w") as f:
    json.dump(missing_nsc_number, f)
