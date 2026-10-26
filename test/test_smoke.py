from corvo_nfse import VERSION, __version__


def test_version() -> None:
    assert VERSION == "0.2.0"
    assert __version__ == VERSION
