#%%
import gzip
import os
import json
import urllib.request
from time import time

from py2neo import Graph

"""
This code will add all the synonyms to the neo4j graph database.
But is very memory intensive.
Make sure everything is closed (even Neo4j desktop app) before starting the first part.
"""
with open("config.json") as f:
    config = json.load(f)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]


temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)


number = 1
number_synonyms = 0
synonyms_per_file = 1e6
wrong_md5 = 0
all_results = []

# Get

file_name_gz = f"chembl_cellline.ttl.gz"
file_name_tll = f"chembl_cellline.ttl"

gz_file_loc = os.path.join(temp_dir, file_name_gz)
tll_file_loc = os.path.join(temp_dir, file_name_tll)

if not os.path.exists(gz_file_loc):
    start = time()
    download_url = rf"https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBL-RDF/31.0/chembl_31.0_cellline.ttl.gz"
    print("download: ", download_url)
    urllib.request.urlretrieve(download_url, gz_file_loc)
    print("download time", time() - start)

start = time()
with gzip.open(gz_file_loc, "r") as file:
    with open(tll_file_loc, "wb") as output_file:
        output_file.write(file.read())


#%% Adding them to the graph
full_tll_path = os.path.abspath(tll_file_loc).replace("\\", "\\\\")

graph = Graph("bolt://localhost:" + port, name="test", auth=(user, pswd))

#%% create n10s unique uri constraint
graph.run(
    f"""
        CREATE CONSTRAINT n10s_unique_uri if not exists ON (r:Resource) ASSERT r.uri IS UNIQUE;
    """
)

#%% init for n10s
graph.run(
    f"""
        CALL n10s.graphconfig.init({{ handleVocabUris: "IGNORE" }});
    """
)

#%% init for n10s
graph.run(
    f"""
        CALL n10s.rdf.import.fetch("file:///{full_tll_path}","Turtle");
    """
)

#%% Add constrain
graph.run(
    """
    CREATE FULLTEXT INDEX cellLineFullText FOR (c:CellLine) ON EACH [c.description]    
    """
)
