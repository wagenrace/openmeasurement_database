#%%
import json

from py2neo import Graph

with open("config.json") as f:
    config = json.load(f)

neo4j_url = config.get("neo4jUrl", "bolt://localhost:7687")
user = config.get("user", "neo4j")
pswd = config.get("pswd", "password")

graph = Graph(neo4j_url, auth=(user, pswd))
#%% load compound info form pug
import requests

compounds_ids_ls = range(129663809, 129664109)
compounds_ids_str = [str(i) for i in compounds_ids_ls]
compounds_ids_str = ",".join(compounds_ids_str)

properties_ls = ["Fingerprint2D", "Title"]
properties_str = ",".join(properties_ls)
url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{compounds_ids_str}/property/{properties_str}/JSON"
response = requests.get(url).json()

print(len(response["PropertyTable"]["Properties"]))
