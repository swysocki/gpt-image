from pygpt_disk import table, disk
import pytest

DISK_SIZE = 8 * 1024 * 1024
SECTOR_SIZE = 512
LAST_LBA = int(DISK_SIZE / SECTOR_SIZE)


@pytest.fixture
def fresh_disk(tmp_path):
    image_path = tmp_path / "table-test.img"
    return disk.Disk(DISK_SIZE, image_path)


def test_init(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)
    assert type(t.disk) == disk.Disk


def test_write_header(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)
    t._write_header()
    t.disk.buffer.seek(fresh_disk.sector_size)
    # signature
    assert t.disk.buffer.read(8) == b"EFI PART"
    # revision
    assert t.disk.buffer.read(4) == b"\x00\x00\x01\x00"
    # header size
    assert t.disk.buffer.read(4) == b"\x5C\x00\x00\x00"
    # header crc (zeroed until calculated)
    assert t.disk.buffer.read(4) == b"\x00" * 4
    # reserved
    assert t.disk.buffer.read(4) == b"\x00" * 4
    # primary header location LBA
    p_lba = 1  # for our purposes, the primary header will always be at LBA 1
    assert t.disk.buffer.read(8) == (p_lba).to_bytes(8, "little")
    # secondary header LBA
    s_lba = LAST_LBA - 1
    assert t.disk.buffer.read(8) == (s_lba).to_bytes(8, "little")
