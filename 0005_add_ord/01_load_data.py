# import requirements
import json

from ord_schema.message_helpers import load_message, write_message
from ord_schema.proto import dataset_pb2
from google.protobuf.json_format import MessageToJson

from pathlib import Path

data_path = (
    Path("ord-data")
    / "data"
    / "00"
    / "ord_dataset-00005539a1e04c809a9a78647bea649c.pb.gz"
)

dataset = load_message(
    str(data_path),
    dataset_pb2.Dataset,
)

# take one reaction message from the dataset for example
rxn = dataset.reactions[0]
rxn_json = json.loads(
    MessageToJson(
        message=rxn,
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
