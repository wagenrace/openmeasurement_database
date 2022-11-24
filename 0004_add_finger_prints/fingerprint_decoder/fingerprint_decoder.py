import base64


def decode_2d_fingerprint(fp: bytes):
    decoded = base64.b64decode(fp)
    binary = "".join(["{:08b}".format(x) for x in decoded])

    fp_numbers = []
    for idx, x in enumerate(binary[32:]):
        if x == "1":
            fp_numbers.append(idx)
    return fp_numbers
