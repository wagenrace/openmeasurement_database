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
graph = Graph(neo4j_url, auth=(user, pswd))

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
    return nsc_2_synonyms.get(str(nsc), {"synonymId": None})["synonymId"]


gi50["CHEMICAL_PUBCHEM_ID"] = gi50["NSC"].apply(str).map(nsc2chemcial_name)

gi50 = gi50.fillna(value=np.nan)
gi50_filtered = gi50.dropna()
print(f"Filtered GI50 size {gi50_filtered.shape}")
#%% Save csv in import folder
csv_name = "gi50.csv"
gi50_filtered.to_csv(os.path.join(neo4j_import_loc, csv_name))
neo4j_csv_name = f"file:///{csv_name}"

#%% Create all experiment nodes

# Index experiment names
graph.run(
    """
    CREATE INDEX experimentNames IF NOT EXISTS FOR (n:Experiment) ON (n.name)
    """
)

# Index user names
graph.run(
    """
    CREATE INDEX userNames IF NOT EXISTS FOR (n:User) ON (n.name)
    """
)

# Create an experiment for every unique experiment
# Connected it (via a synonym) to the protocol, and directly to the user
response = graph.run(
    """
    MERGE (p:Synonym {name: "NCI-60 Screening Methodology"})-[:IS_ATTRIBUTE_OF]->(:Protocol {name: "NCI-60 Screening Methodology", url: "https://dtp.cancer.gov/discovery_development/nci-60/methodology.htm"})
    MERGE (nci:User {name: "National Cancer Institute"})
    WITH p, nci
    LOAD CSV WITH HEADERS FROM $csv_name AS row
    WITH DISTINCT row.EXPID as expid, p, nci
    MERGE (nci)-[:OWNS]->(e:Experiment {name: expid})-[:USES]->(p)
    """,
    csv_name=neo4j_csv_name,
).data()


#%% Create all experiment nodes
response = graph.run(
    """
    USING PERIODIC COMMIT 1000
    LOAD CSV  WITH HEADERS FROM $csv_name AS row 
    MERGE (gi50:Measurement {name: "GI50"})
    WITH row.EXPID as expid, row.CONCENTRATION_UNIT as unit, row.LOG_HI_CONCENTRATION as max_concent, row.AVERAGE as value, row.CELL_NAME_2 as cell_name, row.CHEMICAL_PUBCHEM_ID as synonym_id, gi50
    
    MATCH (chemical:Synonym {pubChemSynId: synonym_id})
    MATCH (cell:CellLine {label: cell_name})
    MATCH (exp:Experiment {name: expid})
        
    MERGE (cell)<-[:USES]-(cond)-[:USES]->(chemical)
    MERGE (exp)<-[:IS_ATTRIBUTE_OF]-(cond:Condition)-[:MEASURES {value: value}]->(gi50)
    """,
    csv_name=neo4j_csv_name,
).data()
