import os

import pytest
from gpt_image import disk

DISK_SIZE = 8 * 1024 * 1024
DISK_NAME = "test-image.img"


@pytest.fixture
def test_disk(tmp_path):
    p = tmp_path / DISK_NAME
    p.write_bytes(b"0" * DISK_SIZE)
    return p.resolve().__str__()


def test_geometry():
    geo = disk.Geometry(DISK_SIZE)
    assert geo.sector_size == 512
    assert geo.total_bytes == DISK_SIZE
    assert geo.total_sectors == int(DISK_SIZE / 512)
    assert geo.total_lba == int(DISK_SIZE / 512)
    assert geo.partition_last_lba == int((DISK_SIZE / 512) - 34)
    assert geo.primary_header_byte == int(1 * 512)
    assert geo.primary_array_byte == int(2 * 512)
    assert geo.backup_header_lba == int((DISK_SIZE / 512) - 1)
    assert geo.backup_header_byte == int(DISK_SIZE - 512)
    assert geo.backup_header_array_lba == int((DISK_SIZE / 512) - 33)
    assert geo.backup_header_array_byte == int(DISK_SIZE - (512 * 33))


def test_disk_init(test_disk):
    # init new disk
    d = disk.Disk(DISK_NAME, DISK_SIZE)
    assert d._size == DISK_SIZE
    assert d.name == DISK_NAME


def test_write(tmp_path):
    name = tmp_path / DISK_NAME
    d = disk.Disk(name, DISK_SIZE)
    d.write()
    assert os.path.exists(name)
