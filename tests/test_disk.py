import os
from pygpt_disk import disk
import pytest

DISK_SIZE = 8 * 1024 * 1024
DISK_NAME = "test-image.img"


@pytest.fixture
def test_disk(tmp_path):
    p = tmp_path / DISK_NAME
    p.write_bytes(b"0" * DISK_SIZE)
    return p.resolve().__str__()


def test_init(test_disk):
    # init new disk
    d = disk.Disk(DISK_NAME, DISK_SIZE)
    assert d.size == DISK_SIZE
    assert d.name == DISK_NAME
    assert d.sector_size == 512
    assert d.sectors == DISK_SIZE / d.sector_size

    # init existing disk
    d = disk.Disk(test_disk)
    assert d.size == DISK_SIZE


def test_create():
    d = disk.Disk(DISK_NAME, DISK_SIZE)
    d.create()
    assert len(d.buffer.getvalue()) == DISK_SIZE


def test_write(tmp_path):
    name = tmp_path / DISK_NAME
    d = disk.Disk(name, DISK_SIZE)
    d.create()
    d.write()
    assert os.path.exists(name)
