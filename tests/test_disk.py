import json

import pytest

from gpt_image.disk import Disk
from gpt_image.partition import Partition, PartitionType

BYTE_DATA = b"\x01\x02\x03\x04"
DISK_SIZE = 4 * 1024 * 1024  # 4 MB


@pytest.fixture
def new_image(tmp_path):
    image_name = tmp_path / "test.img"
    disk = Disk(image_name)
    disk.create(DISK_SIZE)
    part1 = Partition("partition1", 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    part2 = Partition("partition2", 3 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
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
    with pytest.raises(Exception):
        Disk.open("/not/real/path.img")
    disk = Disk.open(new_image)
    assert disk.size == DISK_SIZE
    assert disk.table.primary_header.backup is False
    assert disk.table.secondary_header.backup is True
    assert disk.table.primary_header.partition_entry_lba == 2
    assert disk.table.secondary_header.partition_entry_lba == 8159
    assert len(disk.table.partitions.entries) == 2
    assert disk.table.partitions.entries[0].partition_name == "partition1"


def test_disk_info(new_image):
    disk = Disk.open(new_image)
    disk_s = str(disk)
    disk_d = json.loads(disk_s)
    assert disk_d["path"] == str(new_image)
    assert disk_d["image_size"] == DISK_SIZE
    assert not disk_d["primary_header"]["backup"]
    assert disk_d["backup_header"]["backup"]
    assert disk_d["backup_header"]["header_size"] == 92
    assert len(disk_d["partitions"]) == 2


def test_write_data(new_image):
    disk = Disk.open(new_image)
    part = disk.table.partitions.find("partition1")
    count = part.write_data(disk, BYTE_DATA)
    assert count == len(BYTE_DATA)

    with open(str(new_image), "rb") as b:
        start = part.first_lba * disk.sector_size
        byte_count = len(BYTE_DATA)
        b.seek(start)
        test_buffer = b.read(byte_count)
        assert test_buffer == BYTE_DATA


def test_read_partition(new_image):
    disk = Disk.open(new_image)
    part = disk.table.partitions.find("partition1")
    part.write_data(disk, BYTE_DATA)
    read_data = part.read(disk)
    assert read_data == BYTE_DATA
