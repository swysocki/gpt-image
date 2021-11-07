import os
from pygpt_disk import disk

DISK_SIZE = 8 * 1024 * 1024
DISK_NAME = "test-image.img"


def test_init():
    d = disk.Disk(DISK_SIZE, DISK_NAME)
    assert d.size == DISK_SIZE
    assert d.name == DISK_NAME


def test_create():
    d = disk.Disk(DISK_SIZE, DISK_NAME)
    d.create()
    assert len(d.disk.getvalue()) == DISK_SIZE


def test_write(tmp_path):
    name = tmp_path / DISK_NAME
    d = disk.Disk(DISK_SIZE, name)
    d.create()
    d.write()
    assert os.path.exists(name)
