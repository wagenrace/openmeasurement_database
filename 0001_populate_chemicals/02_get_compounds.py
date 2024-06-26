# %%
import gzip
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

with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]

graph = Graph("bolt://localhost:" + port, auth=(user, pswd))

# %% Create compound constrain
response = graph.run(
    f"""
        CREATE constraint compoundId if not exists for (c:Compound) require c.pubChemCompId is unique;
    """
).data()
print(response)

temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)


number = 1

while True:
    result_list = []

    file_name = f"pc_synonym2compound_{str(number).zfill(6)}.ttl.gz"
    print(file_name)
    gz_file_loc = os.path.join(temp_dir, file_name)
    if os.path.exists(gz_file_loc):
        print(f"{gz_file_loc} already exists")
    else:
        start = time()
        download_url = rf"https://ftp.ncbi.nlm.nih.gov/pubchem/RDF/synonym/{file_name}"
        print("download: ", download_url)
        try:
            urllib.request.urlretrieve(download_url, gz_file_loc)
        except:
            print(f"Could not download {download_url}")
            break
        print("download time", time() - start)

    start = time()
    with gzip.open(gz_file_loc, "r") as f:
        for line in f:
            line = line.decode("utf-8")
            if line.startswith("@prefix"):
                continue
            synonym_id, _, compound = line.split("\t")
            compound = compound.lower()
            result = re.findall("(.*) .\n", compound)
            if result:
                if len(result) > 1:
                    print(f"Multiple hits with {compound}")
                    continue
                clean_synonym = encode2neo4j(result[0])

                result_list.append(result[0])
            else:
                print(f"Error with {compound}")

    print("reading time", time() - start)

    print(f"new compounds: {len(result_list)}\n")

    split_size = 1e6
    number_files = 0
    for i in tqdm(range(ceil(len(result_list) / split_size))):
        result_df = pd.DataFrame(
            result_list[int(i * split_size) : int((i + 1) * split_size)],
            columns=["compound"],
        )
        result_df = result_df.drop_duplicates()
        result_df.to_csv(
            os.path.join(neo4j_import_loc, f"compounds.csv"),
            index=False,
        )
        number_files += 1

        graph.run(
            f"""
            LOAD CSV  WITH HEADERS FROM 'file:///compounds.csv' AS row
            WITH row.compound as comp_id
            CALL {{
                WITH comp_id
                MERGE (comp:Compound {{pubChemCompId: comp_id}})
            }} IN TRANSACTIONS OF 10000 ROWS
        """
        ).data()
    del result_list
    number += 1
