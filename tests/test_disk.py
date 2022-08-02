import json

import pytest

from gpt_image.disk import Disk
from gpt_image.partition import Partition

BYTE_DATA = b"\x01\x02\x03\x04"
DISK_SIZE = 4 * 1024 * 1024  # 4 MB


@pytest.fixture
def new_image(tmp_path):
    image_name = tmp_path / "test.img"
    disk = Disk(image_name)
    disk.create(DISK_SIZE)
    part1 = Partition("partition1", 2 * 1024, Partition.LINUX_FILE_SYSTEM)
    part2 = Partition("partition2", 3 * 1024, Partition.LINUX_FILE_SYSTEM)
    disk.table.partitions.add(part1)
    disk.table.partitions.add(part2)
    disk.commit()
    return image_name


def test_disk_create(tmp_path):
    """Test creating a new disk image"""
    disk_path = tmp_path / "test-disk.img"
    disk = Disk(disk_path)
    assert disk.image_path == disk_path.resolve()
    assert disk.sector_size == 512
    disk.create(DISK_SIZE)


def test_disk_open(new_image):
    disk = Disk(new_image)
    disk.open()
    assert disk.size == DISK_SIZE
    assert disk.table.primary_header.backup is False
    assert disk.table.secondary_header.backup is True
    assert disk.table.primary_header.partition_entry_lba == 2
    assert disk.table.secondary_header.partition_entry_lba == 8159
    assert len(disk.table.partitions.entries) == 2
    assert disk.table.partitions.entries[0].partition_name == "partition1"


def test_disk_info(new_image):
    disk = Disk(new_image)
    disk.open()
    disk_s = str(disk)
    disk_d = json.loads(disk_s)
    assert disk_d["path"] == str(new_image)
    assert disk_d["image_size"] == DISK_SIZE
    assert not disk_d["primary_header"]["backup"]
    assert disk_d["backup_header"]["backup"]
    assert disk_d["backup_header"]["header_size"] == 92
    assert len(disk_d["partitions"]) == 2
