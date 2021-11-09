from pygpt_disk import table, disk
import pytest


@pytest.fixture
def fresh_disk(tmp_path):
    image_path = tmp_path / "table-test.img"
    return disk.Disk(8 * 1024 * 1024, image_path)


def test_init(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)
    t.create()
    t.disk.buffer.seek(fresh_disk.sector_size)
    assert t.disk.buffer.read(8) == b"EFI PART"
    assert t.disk.buffer.read(4) == b"\x00\x00\x01\x00"
    assert t.disk.buffer.read(4) == b"\x5C\x00\x00\x00"
    assert t.disk.buffer.read(4) == b"\x00" * 4
    assert t.disk.buffer.read(4) == b"\x00" * 4
    fresh_disk.write()
