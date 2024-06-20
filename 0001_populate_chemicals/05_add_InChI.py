import gzip
import json
import os
import re
import urllib.request
from time import time

import pandas as pd
from encode_for_neo4j import encode2neo4j

from py2neo import Graph

with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]

graph = Graph("bolt://localhost:" + port, auth=(user, pswd))

temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)


number = 1

while True:
    result_list = []
    # Get

    file_name = f"pc_descr_InChI_value_{str(number).zfill(6)}.ttl.gz"
    print(file_name)
    gz_file_loc = os.path.join(temp_dir, file_name)
    if not os.path.exists(gz_file_loc):
        start = time()
        download_url = (
            rf"https://ftp.ncbi.nlm.nih.gov/pubchem/RDF/descriptor/compound/{file_name}"
        )
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
            part1, _, part3 = line.split("\t")

            raw_compounds = re.findall("descriptor:(.*)_iupac_inchi", part1.lower())
            if len(raw_compounds) > 1:
                print(f"Multiple compounds found within: {raw_compounds}")
                continue
            if len(raw_compounds) == 0:
                print(f"No compounds found within: {raw_compounds}")
                continue
            compound = "compound:" + raw_compounds[0]
            in_chi = re.findall('InChI=(.*)"@en .\n', part3)

            if len(in_chi) > 1:
                print(f"Multiple InChI found within: {in_chi}")
                continue
            if len(in_chi) == 0:
                print(f"No InChI found within: {in_chi}")
                continue

            clean_in_chi = encode2neo4j(in_chi[0])

            result_list.append({"inChI": clean_in_chi, "pubChemCompId": compound})

            if len(result_list) >= 1000:
                result_pd = pd.DataFrame(result_list)
                result_pd.to_csv(
                    os.path.join(neo4j_import_loc, f"inChI.csv"),
                    index=False,
                )
                break
        break
    #             graph.run(
    #                 f"""
    #                 LOAD CSV  WITH HEADERS FROM 'file:///inChI.csv' AS row
    #                 WITH row.pubChemCompId as comp_id, row.inChI as smiles
    #                 MATCH (comp:Compound {{pubChemCompId: comp_id}})
    #                 SET comp.inChI = smiles
    #             """
    #             ).data()
    #             print(f"Added an other {len(result_list)}")
    #             result_list = []
    # print("reading time of gz", time() - start)
    # number += 1
