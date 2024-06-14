# import requirements
import gzip
from ord_schema.message_helpers import load_message, write_message
from ord_schema.proto import dataset_pb2
from pathlib import Path

data_path = (
    Path("ord-data")
    / "data"
    / "00"
    / "ord_dataset-00005539a1e04c809a9a78647bea649c.pb.gz"
)

with gzip.open(data_path, mode="rb") as f:
    for line in f:
        print(f)
        break
# load the binary ord file
# dataset = load_message(str(data_path), dataset_pb2.Dataset)
# # save the ord file as human readable text
# write_message(dataset, "output_fname.pbtxt")
