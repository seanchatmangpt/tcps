from tcps.blake3_ref import hexdigest


def _official_input(length: int) -> bytes:
    # Official BLAKE3 test-vector input repeats bytes 0..250.
    return bytes(index % 251 for index in range(length))


def test_blake3_empty_vector():
    assert hexdigest(b"") == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"


def test_blake3_abc_vector():
    assert hexdigest(b"abc") == "6437b3ac38465133ffb63b75273a8db548c558465d79db03fd359c6cd5bd9d85"


def test_blake3_official_block_boundary_vector():
    assert hexdigest(_official_input(64)) == "4eed7141ea4a5cd4b788606bd23f46e212af9cacebacdc7d1f4c6dc7f2511b98"


def test_blake3_official_chunk_boundary_vector():
    assert hexdigest(_official_input(1024)) == "42214739f095a406f3fc83deb889744ac00df831c10daa55189b5d121c855af"


def test_blake3_official_first_tree_transition_vector():
    assert hexdigest(_official_input(1025)) == "d00278ae47eb27b34faecf67b4fe263f82d5412916c1ffd97c8cb7fb814b8444"


def test_blake3_official_two_chunk_tree_vector():
    assert hexdigest(_official_input(2048)) == "e776b6028c7cd22a4d0ba182a8bf62205d2ef576467e838ed6f2529b85fba24a"
