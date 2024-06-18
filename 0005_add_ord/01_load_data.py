# import requirements
import json

from ord_schema.message_helpers import load_message
from ord_schema.proto import dataset_pb2
from google.protobuf.json_format import MessageToJson

from pathlib import Path

data_path = (
    Path("ord-data")
    / "data"
    / "00"
    / "ord_dataset-00005539a1e04c809a9a78647bea649c.pb.gz"
)

data_path = Path("ord-data") / "data"
temp_folder = Path("temp")
temp_folder.mkdir(exist_ok=True)

for gz_path in data_path.glob("*/*.pb.gz"):
    json_name = gz_path.name.replace(".pb.gz", ".json")
    dataset = load_message(
        str(gz_path),
        dataset_pb2.Dataset,
    )

    # take one reaction message from the dataset for example
    for reaction in dataset.reactions:
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

        with open(temp_folder / json_name, "w") as fp:
            json.dump(rxn_json, fp, indent=4)
