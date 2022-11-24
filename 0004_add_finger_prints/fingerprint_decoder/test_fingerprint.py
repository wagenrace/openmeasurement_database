from fingerprint_decoder import decode_2d_fingerprint


def test_etanol():
    result = decode_2d_fingerprint(
        b"AAADcYBAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGgAACAAAAACggAICAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
    )
    assert result == [
        0,
        9,
        18,
        283,
        284,
        286,
        308,
        344,
        346,
        352,
        366,
        374,
        406,
        571,
    ]
