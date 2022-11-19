import base64

fp = "AAADcYBAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGgAACAAAAACggAICAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="


def decode_2d_fingerprint(fp):
    fp = fp.encode("utf-8")
    decoded = base64.b64decode(fp)
    binary = "".join(["{:08b}".format(x) for x in decoded])

    fp_numbers = []
    for idx, x in enumerate(binary[32:]):
        if x == "1":
            fp_numbers.append(idx)
    return fp
