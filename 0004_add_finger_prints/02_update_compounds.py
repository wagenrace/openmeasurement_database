#%%
import json
import time

import requests
from py2neo import Graph

from fingerprint_decoder import decode_2d_fingerprint

with open("config.json") as f:
    config = json.load(f)

neo4j_url = config.get("neo4jUrl", "bolt://localhost:7687")
user = config.get("user", "neo4j")
pswd = config.get("pswd", "password")

graph = Graph(neo4j_url, auth=(user, pswd))

#%%
# Get compounds from database
step_size = 300
while True:
    start = time.time()
    response = graph.run(
        """
        MATCH (n:Compound) 
        WHERE n.hasFingerprint IS null AND n.name is null
        RETURN n.pubChemCompId as compoundId LIMIT $limit
    """,
        limit=step_size,
    ).data()
    print(f"total time: {time.time() - start}| get compounds")
    # Get all compound ids
    all_ids = []

    if len(response) == 0:
        break
    for i in response:
        if type(i["compoundId"]) == int:
            compound_id = str(i["compoundId"])
        else:
            compound_id = i["compoundId"].replace("compound:cid", "")
        all_ids.append(compound_id)

    # Get fingerprints and title from pug endpoint
    compounds_ids_str = ",".join(all_ids)
    properties_ls = ["Fingerprint2D", "Title"]
    properties_str = ",".join(properties_ls)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{compounds_ids_str}/property/{properties_str}/JSON"

    response_raw = requests.get(url)
    if response_raw.status_code == 200:
        response = response_raw.json()
    else:
        time.sleep(1)
        response_raw = requests.get(url)
        response = response_raw.json()

    print(f"total time: {time.time() - start}| PUG request")

    # Add fingerprint data
    clean_data = []
    for compound in response["PropertyTable"]["Properties"]:
        clean_compound = {}
        clean_compound["Fingerprint2D"] = decode_2d_fingerprint(
            compound["Fingerprint2D"]
        )
        clean_compound["Title"] = compound.get("Title")
        clean_compound["Id"] = compound["CID"]
        clean_compound["OldId"] = f"compound:cid{compound['CID']}"
        clean_data.append(clean_compound)

    # Update database
    graph.run(
        """
        UNWIND $compoundData as compoundData
        CALL{
            WITH compoundData
            MATCH (n:Compound)
            WHERE n.pubChemCompId in [compoundData.OldId, toInteger(compoundData.Id)]
            SET n.hasFingerprint = true
            SET n.name = compoundData.Title
            SET n.pubChemCompId = toInteger(compoundData.Id)
            
            WITH compoundData, n
            UNWIND compoundData.Fingerprint2D as fp_num
            MATCH (fp:Fingerprint {number: fp_num})
            MERGE (n)-[:HAS_FINGERPRINT]->(fp)
        } IN TRANSACTIONS OF 25 ROWS
    """,
        compoundData=clean_data,
    )
    print(
        f"total time: {time.time() - start}| Total time for Compounds {clean_data[0]['Id']} - {clean_data[-1]['Id']}\n"
    )
