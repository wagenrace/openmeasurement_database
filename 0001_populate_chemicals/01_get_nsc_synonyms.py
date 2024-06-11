# %%
import gzip
import hashlib
import json
import os
import re
import urllib.request
from math import ceil
from time import time

import pandas as pd
from encode_for_neo4j import encode2neo4j
from py2neo import Graph
from tqdm import tqdm

"""
This code will add all the synonyms to the neo4j graph database.
But is very memory intensive.
Make sure everything is closed (even Neo4j desktop app) before starting the first part.
"""
with open("config.json") as f:
    config = json.load(f)

port = str(config["port"])
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]


temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)


number = 1
number_synonyms = 0
synonyms_per_file = 1e6
wrong_md5 = 0

graph = Graph("bolt://localhost:" + port, auth=(user, pswd))
graph.run(
    """
        CREATE constraint synonymId if not exists for (c:Synonym) require c.pubChemSynId is unique;
    """
)

while True:
    all_results = []

    # Get
    file_name = f"pc_synonym_value_{str(number).zfill(6)}.ttl.gz"
    print(file_name)
    gz_file_loc = os.path.join(temp_dir, file_name)
    if not os.path.exists(gz_file_loc):
        start = time()
        download_url = rf"https://ftp.ncbi.nlm.nih.gov/pubchem/RDF/synonym/{file_name}"
        print("download: ", download_url)
        try:
            urllib.request.urlretrieve(download_url, gz_file_loc)
        except:
            break
        print("download time", time() - start)

    start = time()
    with gzip.open(gz_file_loc, "r") as f:
        for line in f:
            line = line.decode("utf-8")
            if line.startswith("@prefix"):
                continue
            synonym_id_raw, _, synonym = line.split("\t")
            if synonym_id_raw == "":
                continue

            synonym_id = synonym_id_raw.replace("synonym:MD5_", "")
            number_synonyms += 1
            synonym = synonym.lower()
            result = re.findall('"(.*)"', synonym)
            if result:
                if len(result) > 1:
                    print(f"Multiple hits with {synonym}")
                    continue

                # If the md5_id and md5 synonym mismatch there is something wrong
                # Most of the time it is a weird encode-decode bug
                if hashlib.md5(result[0].encode("utf-8")).hexdigest() == synonym_id:
                    all_results.append(result[0])
                else:
                    wrong_md5 += 1
            else:
                print(f"Error with {synonym}")
    print("reading time", time() - start)
    number += 1

    print(f"total synonyms: {len(all_results)} of {number_synonyms}")
    print(f"MD5 mismatch: {wrong_md5}")
    # total synonyms: 198741219 of 198747084
    # %% Remove duplicates
    all_results.sort()

    # %%
    split_size = 1e6
    number_files = 0
    prev_result = ""
    for i in range(ceil(len(all_results) / split_size)):
        part_results = []
        for syn in all_results[int(i * split_size) : int((i + 1) * split_size)]:
            if syn == prev_result:
                continue
            part_results.append(syn)
            prev_result = syn
        result_df = pd.DataFrame(
            map(encode2neo4j, part_results),
            columns=["synonym"],
        )
        result_df["synonym_id"] = [
            hashlib.md5(val.encode("utf-8")).hexdigest() for val in result_df["synonym"]
        ]
        result_df.to_csv(
            os.path.join(neo4j_import_loc, f"synonyms_{i}.csv"),
            index=False,
        )
        number_files += 1

    # Save your memory
    del all_results

    for i in tqdm(range(number_files)):
        graph.run(
            f"""
            LOAD CSV  WITH HEADERS FROM 'file:///synonyms_{i}.csv' AS row 
            WITH distinct row.synonym_id as id, row.synonym as synonym
            CALL {{
                WITH id, synonym
                MERGE (sym:Synonym {{pubChemSynId: id}})
                SET sym.name = synonym
            }} IN TRANSACTIONS OF 10000 ROWS
        """
        ).data()
