# %%
import json
import os
from pathlib import Path

from ord_schema.message_helpers import load_message
from ord_schema.proto import dataset_pb2
from ord_schema.proto.reaction_pb2 import CompoundIdentifier
from rdkit import Chem
from tqdm import tqdm

temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

data_path = Path("ord-data") / "data"
temp_folder = Path("temp")
temp_folder.mkdir(exist_ok=True)


# %%
def check_component(component):
    inchi, smiles = get_component_identifiers(component)

    if inchi is None or smiles is None:
        # Cannot compare SMILES to InChI
        return None

    inchi_from_smiles = get_inchi_from_smiles(component)

    if inchi == inchi_from_smiles:
        return True
    else:
        return False


def get_inchi_from_smiles(component):
    _, smiles = get_component_identifiers(component)
    chem = Chem.MolFromSmiles(smiles)
    inchi = Chem.MolToInchi(chem)
    return inchi


def get_component_summary(component):
    inchi, smiles = get_component_identifiers(component)
    inchi_from_smiles = get_inchi_from_smiles(component)
    return {f"InChI": inchi, "SMILES": smiles, "InChI from SMILES": inchi_from_smiles}


def get_component_identifiers(component):
    inchi = None
    smiles = None
    for identifier in component.identifiers:
        if identifier.type == CompoundIdentifier.INCHI:
            inchi = identifier.value
        if identifier.type == CompoundIdentifier.SMILES:
            smiles = identifier.value
    return inchi, smiles


# %%
num_correct_components = 0
num_incorrect_components = 0
all_incorrect_components = []

all_gz_paths = [i for i in data_path.glob("*/*.pb.gz")]
for gz_path in tqdm(all_gz_paths):
    json_name = gz_path.name.replace(".pb.gz", ".json")
    dataset = load_message(
        str(gz_path),
        dataset_pb2.Dataset,
    )

    # take one reaction message from the dataset for example
    for reaction in dataset.reactions:
        # Reaction ID is required
        reaction_id = reaction.reaction_id

        # Inputs are required
        inputs = reaction.inputs

        # Identifiers need to have type InChI
        for input_state in inputs.keys():
            components = inputs[input_state].components
            for component in components:
                result = check_component(component)
                if result is None:
                    # Cannot compare SMILES to InChI
                    continue

                if result:
                    num_correct_components += 1
                else:
                    num_incorrect_components += 1
                    all_incorrect_components.append(get_component_summary(component))

# %%
with open(temp_folder / "incorrect_components.json", "w") as f:
    json.dump(
        {
            "number_correct": num_correct_components,
            "number_incorrect": num_incorrect_components,
            "incorrect": all_incorrect_components,
        },
        f,
        indent=2,
    )

# %%
print(f"correct components: {num_correct_components}")
print(f"incorrect components: {num_incorrect_components}")
