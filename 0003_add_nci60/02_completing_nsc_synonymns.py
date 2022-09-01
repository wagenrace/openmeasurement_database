#%%
import json
import os

import requests
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
update_synonym_url = config.get(
    "updatePubchemSynonymsByNameUrl", "http://127.0.0.1:81/updatePubchemSynonymsByName/"
)
neo4j_import_loc = config["neo4j_import_loc"]

all_nsc_numbers = pd.read_csv(gi50_path, usecols=["NSC"], index_col=False).NSC.unique()
#%% Adding them to the graph
graph = Graph(neo4j_url, auth=(user, pswd))

missing_synonyms = []
synonym_without_compounds = []
results = {}
for nsc_number in tqdm(all_nsc_numbers):
    response = graph.run(
        f"""
        CALL {{
            CALL db.index.fulltext.queryNodes('synonymsFullText', "{nsc_number2lucence_query(nsc_number)}")
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

    filtered_response = []
    for r in response:
        if not (name := r.get("name", "").lower()) in [
            f"nsc{nsc_number}",
            f"nsc {nsc_number}",
            f"nsc-{nsc_number}",
        ]:
            print(f"Name {name} is not part of nsc {nsc_number}")
        if r.get("compoundId") is None:
            synonym_without_compounds.append(
                {"id": r.get("synonymId"), "nsc": int(nsc_number)}
            )
            continue
        filtered_response.append(r)

    results[int(nsc_number)] = filtered_response

with open(r"nsc_number_2_synonymn_raw.json", "w") as f:
    json.dump(results, f)

with open(r"nsc_missing_compound_raw.json", "w") as f:
    json.dump(synonym_without_compounds, f)

with open(r"nsc_missing_synonyms_raw.json", "w") as f:
    json.dump(missing_synonyms, f)

#%%
no_attribute = []
total_fails = []
for synonym in tqdm(synonym_without_compounds):
    synonym_id = synonym["id"]
    try:
        sym_url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/rdf/synonym/MD5_{synonym_id}.json"
        )

        sym_key = f"synonym/MD5_{synonym_id}"
        data = requests.get(sym_url).json()

        compounds = data[sym_key].get(
            "http://semanticscience.org/resource/is-attribute-of"
        )
        if not compounds:
            no_attribute.append(synonym)
            continue
        compounds_pubChemCompId = [
            i["value"].lower().replace("compound/cid", "compound:cid")
            for i in compounds
        ]
        for pubChemCompId in compounds_pubChemCompId:
            graph.run(
                f"""
                    MATCH (sym:Synonym {{pubChemSynId: "{synonym_id}"}})
                    MATCH (comp:Compound {{pubChemCompId: "{pubChemCompId}"}})
                    MERGE (sym)-[:IS_ATTRIBUTE_OF]->(comp);
                    """
            )
    except:
        total_fails.append(synonym)
        print(synonym)

with open(r"nsc_missing_synonyms_without_attribute.json", "w") as f:
    json.dump(no_attribute, f)

with open(r"nsc_missing_synonyms_total_fails.json", "w") as f:
    json.dump(total_fails, f)

#%% Add new synonym
still_not_found = []
nsc_numbers_to_renew = set(
    [i["nsc"] for i in no_attribute + total_fails] + missing_synonyms
)

for nsc in tqdm(nsc_numbers_to_renew):
    found = False
    for nsc_name in [f"nsc{nsc}", f"nsc {nsc}", f"nsc-{nsc}"]:
        response = requests.get(
            f"http://127.0.0.1:81/updatePubchemSynonymsByName/?synonym_name={nsc_name}"
        )
        if response.status_code != 200:
            continue
        if response.json():
            found = True
            break
    if found == False:
        still_not_found.append(nsc)

with open(r"nsc_still_missing.json", "w") as f:
    json.dump(still_not_found, f)
