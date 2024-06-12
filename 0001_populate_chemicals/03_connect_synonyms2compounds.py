# %%
import gzip
import os
import re
import json
import urllib.request
from time import time

import pandas as pd
from py2neo import Graph

from encode_for_neo4j import encode2neo4j

with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]

graph = Graph("bolt://localhost:" + port, auth=(user, pswd))


def get_current_connections():
    current_connection = graph.run(
        """
        MATCH ()-[r:IS_ATTRIBUTE_OF]->() return count(r)
        """
    ).data()[0]["count(r)"]
    return current_connection


current_connection = get_current_connections()
temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)


def add_results(result_list):
    result_df = pd.DataFrame(result_list, columns=["synonymId", "compoundId"])
    result_df = result_df.drop_duplicates()
    result_df.to_csv(
        os.path.join(neo4j_import_loc, f"synom_id2nsc.csv"),
        index=False,
    )

    graph.run(
        """
        LOAD CSV  WITH HEADERS FROM 'file:///synom_id2nsc.csv' AS row 
        WITH row.compoundId as comp_id, row.synonymId as sym_id
        CALL{
            WITH comp_id, sym_id
            MATCH (sym:Synonym {pubChemSynId: sym_id})
            MATCH (comp:Compound {pubChemCompId: comp_id})
            MERGE (sym)-[:IS_ATTRIBUTE_OF]->(comp)
        }
    """
    ).data()


number = 1
synonyms_per_file = 1e4
number_synonyms = 0
number_compounds = 0
total_start_time = time()

while True:
    result_list = []
    # Get

    file_name = f"pc_synonym2compound_{str(number).zfill(6)}.ttl.gz"
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
            synonym_id_raw, _, compound = line.split("\t")
            compound = compound.lower()
            result = re.findall("(.*) .\n", compound)
            number_compounds += 1
            if synonym_id_raw == "":
                continue
            if compound == "":
                continue
            synonym_id = synonym_id_raw.replace("synonym:MD5_", "")
            number_synonyms += 1
            if number_synonyms < current_connection:
                continue
            if result:
                if len(result) > 1:
                    print(f"Multiple hits with {compound}")
                    continue
                clean_synonym = encode2neo4j(result[0])

                result_list.append([synonym_id, result[0]])
            else:
                print(f"Error with {compound}")
                continue

            if len(result_list) >= synonyms_per_file:
                print("start uploading")
                start_add = time()
                add_results(result_list)
                writing_time = time() - start_add
                print(f"total synonyms: {number_synonyms}")
                print(
                    f"Writing time: {writing_time} with {synonyms_per_file/writing_time} writes per second"
                )
                num_connections = get_current_connections()
                print(
                    f"Estimated time left (hours): {(writing_time /3600)/ (len(result_list) + 1e-17) *  (19e7 - num_connections) }"
                )
                print(f"Current connections: {num_connections}")
                print("============\n")
                result_list = []
    print("reading + writing time", time() - start)
    number += 1

print(f"total synonyms: {number_synonyms} of {number_compounds}")
