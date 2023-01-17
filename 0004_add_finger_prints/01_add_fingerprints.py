#%%
import json

from py2neo import Graph

with open("config.json") as f:
    config = json.load(f)

neo4j_url = config.get("neo4jUrl", "bolt://localhost:7687")
user = config.get("user", "neo4j")
pswd = config.get("pswd", "password")

graph = Graph(neo4j_url, auth=(user, pswd))

with open("fingerprint_names.json") as f:
    fingerprints = json.load(f)

with open("fingerprint_sections.json") as f:
    fp_sections = json.load(f)

#%% Adding fp sections to the graph

response = graph.run(
    """
    UNWIND $sections as section
    MERGE (s:FpSection {name: section.name, number: section.number, description:section.description})
    return s
""",
    sections=fp_sections,
).data()
print(response)

#%%
graph.run(
    """
    CREATE index fpSectionNumber if not exists for (s:FpSection) ON s.number;
"""
)

#%% Adding fingerprints to the graph

response = graph.run(
    """
    UNWIND $fingerprints as fingerprint
    MERGE (fp:Fingerprint {name: fingerprint.name, number: fingerprint.number})

    WITH fp, fingerprint
    MATCH (s:FpSection {number: fingerprint.section})

    MERGE (fp)-[:IS_ATTRIBUTE_OF]->(s)
""",
    fingerprints=fingerprints,
)

#%%
graph.run(
    """
    CREATE index fingerprintNumber if not exists for (fp:Fingerprint) ON fp.number;
"""
)
