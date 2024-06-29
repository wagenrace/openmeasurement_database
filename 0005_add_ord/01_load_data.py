# import requirements
import json
import os
from pathlib import Path
from typing import List
from uuid import uuid4

from google.protobuf.json_format import MessageToJson
from ord_schema.message_helpers import load_message
from ord_schema.proto import dataset_pb2
from ord_schema.proto.reaction_pb2 import CompoundIdentifier
from py2neo import Graph
from tqdm import tqdm

from ord_types import ReactionComponent

with open("config.json") as f:
    config = json.load(f)

temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

port = config["port"]
user = config["user"]
pswd = config["pswd"]
neo4j_import_loc = config["neo4j_import_loc"]

graph = Graph("bolt://localhost:" + port, auth=(user, pswd))

data_path = Path("ord-data") / "data"
temp_folder = Path("temp")
temp_folder.mkdir(exist_ok=True)


def save_error(rxn_json, error_type):
    reaction_id = rxn_json.get("reaction_id", f"no_id_{uuid4()}")
    json_path = temp_folder / "error" / error_type / f"{reaction_id}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_bytes(json.dumps(rxn_json, indent=2).encode())


# This will add 2,274,399 reactions
count = 0
total_errors = 0
all_gz_paths = [i for i in data_path.glob("*/*.pb.gz")]
for gz_path in tqdm(all_gz_paths):
    json_name = gz_path.name.replace(".pb.gz", ".json")
    dataset = load_message(
        str(gz_path),
        dataset_pb2.Dataset,
    )

    # take one reaction message from the dataset for example
    for reaction in dataset.reactions:
        count += 1
        rxn_json = json.loads(
            MessageToJson(
                message=reaction,
                including_default_value_fields=False,
                preserving_proto_field_name=True,
                indent=2,
                sort_keys=False,
                use_integers_for_enums=False,
                descriptor_pool=None,
                float_precision=None,
                ensure_ascii=True,
            )
        )

        # Reaction ID is required
        reaction_id = reaction.reaction_id

        # Inputs are required
        inputs = reaction.inputs
        input_components: List[ReactionComponent] = []

        # Identifiers need to have type InChI
        inputs_identifiers_are_inchi = True
        for input_state in inputs.keys():
            components = inputs[input_state].components
            for component in components:
                for identifier in component.identifiers:
                    if identifier.type == CompoundIdentifier.INCHI:
                        inchi = identifier.value
                if not inchi:
                    save_error(rxn_json, "inputs_identifiers")
                    total_errors += 1
                    inputs_identifiers_are_inchi = False
                    break

                input_components.append(
                    ReactionComponent(
                        state=input_state,
                        inchi=inchi,
                        amount=str(component.amount),
                        reaction_role=component.reaction_role,
                        input=True,
                        reaction_id=reaction_id,
                    )
                )

            if not inputs_identifiers_are_inchi:
                break
        if not inputs_identifiers_are_inchi:
            continue

        # outcomes are required
        outcomes = reaction.outcomes
        outcome_components: List[ReactionComponent] = []

        # Identifiers need to have type InChI
        outcomes_identifiers_are_inchi = True
        for outcome in outcomes:
            components = outcome.products
            for component in components:
                for identifier in component.identifiers:
                    if identifier.type == CompoundIdentifier.INCHI:
                        inchi = identifier.value
                if not inchi:
                    save_error(rxn_json, "outcomes_identifiers")
                    total_errors += 1
                    outcomes_identifiers_are_inchi = False
                    break

                outcome_components.append(
                    ReactionComponent(
                        state="product",
                        inchi=inchi,
                        amount="",
                        reaction_role=component.reaction_role,
                        input=False,
                        reaction_id=reaction_id,
                    )
                )

            if not outcomes_identifiers_are_inchi:
                break

        # outcomes are required
        outcomes = reaction.outcomes
    #     break
    # break
print(f"Total errors: {total_errors}")
print(f"Total reactions: {count}")
