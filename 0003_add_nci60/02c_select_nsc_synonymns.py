#%%
import json
import os

from tqdm import tqdm
import requests

gi50_path = os.path.join("data", "GI50.csv")
nsc2synonymId_path = os.path.join("data", "nsc2synom_id.csv")

result_dir = os.path.join("results", "completing_nscs")
os.makedirs(result_dir, exist_ok=True)

with open(os.path.join(result_dir, r"nsc_number_2_synonyms.json"), "r") as f:
    nsc_numbers_2_synonyms = json.load(f)

#%% Pick the NSC number
no_pick = {}
filtered_nsc_number = {}
single_compound = 0
perfect_connected = 0

for nsc_number in tqdm(list(nsc_numbers_2_synonyms.keys())[:]):
    found_match = False
    synonyms = nsc_numbers_2_synonyms[nsc_number]
    all_compounds = [s["compoundId"] for s in synonyms]

    # Single compound
    if len(set(all_compounds)) == 1:
        filtered_nsc_number[nsc_number] = synonyms[0]
        single_compound += 1
        continue

    # Make sure the synonyms are up-to-date
    # And get the updated compounds
    synonyms2compounds = {}
    for synonym in synonyms:
        nsc_name = synonym["name"]
        try:
            response = requests.get(
                f"http://127.0.0.1:81/updatePubchemSynonymsByName/?synonym_name={nsc_name}",
                timeout=60,
            )
        except:
            synonyms2compounds[nsc_name] = synonym
            continue

        if response.status_code != 200:
            synonyms2compounds[nsc_name] = synonym
            continue
        matched_compounds = response.json()

        results = []
        all_compound_ids = ["compound:cid" + str(i["CID"]) for i in matched_compounds]

        synonyms2compounds[nsc_name] = {
            "name": synonym["name"],
            "synonymId": synonym["synonymId"],
            "compounds": all_compound_ids,
        }

    # Single perfect connected
    all_compounds = []
    for s in synonyms2compounds:
        all_compounds += synonyms2compounds[s].get("compounds", [])
    all_compounds = set(all_compounds)

    for i in synonyms2compounds:
        if len((synonyms2compounds[i].get("compounds", []))) == len(all_compounds):
            filtered_nsc_number[nsc_number] = synonyms2compounds[i]
            found_match = True
            perfect_connected += 1
            break

    if found_match:
        continue

    no_pick[nsc_number] = synonyms

print("single_compound", single_compound)
print("perfect_connected", perfect_connected)
print("no_pick", len(no_pick))

with open(os.path.join(result_dir, r"nsc_number_2_single_synonym.json"), "w") as f:
    json.dump(filtered_nsc_number, f)

with open(os.path.join(result_dir, r"nsc_number_not_matched.json"), "w") as f:
    json.dump(no_pick, f)
