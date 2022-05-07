import pytest
from gpt_image.entry import Entry


def test_data_types():
    with pytest.raises(ValueError):
        _ = Entry(1, 1, [])


def test_setter_int():
    # test integer conversion
    int_entry = Entry(0, 1, 44)
    assert int_entry.offset == 0
    assert int_entry.length == 1
    # 44 is "," in bytes
    assert int_entry.data_bytes == b","
    int_entry.data = 33
    assert int_entry.data_bytes == b"!"


def test_setter_str():
    str_entry = Entry(0, 8, "python")
    assert str_entry.offset == 0
    assert str_entry.length == 8
    assert str_entry.data_bytes == b"python\x00\x00"
    # test that string cannot be longer than length
    with pytest.raises(ValueError):
        _ = Entry(0, 2, "python")


def test_setter_bytes():
    test_bytes = b"\x91\x02\x03\x04"

    byte_entry = Entry(0, 4, test_bytes)
    assert byte_entry.offset == 0
    assert byte_entry.length == 4
    assert byte_entry.data_bytes == test_bytes
    byte_entry_padded = Entry(0, 8, test_bytes)
    assert byte_entry_padded.data_bytes == test_bytes + b"\x00" * 4
    # test that bytes cannot be longer than length
    with pytest.raises(ValueError):
        _ = Entry(0, 2, test_bytes)
