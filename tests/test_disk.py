import uuid

import pytest
from gpt_image.disk import Disk
from gpt_image.partition import Partition

BYTE_DATA = b"\x01\x02\x03\x04"
DISK_SIZE = 2 * 1024 * 1024


@pytest.fixture
def new_image(tmp_path):
    image_size = DISK_SIZE
    image_name = tmp_path / "test.img"
    abs_path = image_name.resolve()
    disk = Disk(str(abs_path), image_size, fresh_disk=True)
    return disk


def test_disk_new(new_image: Disk):
    """Test creating a new disk image"""
    new_image.update_table()
    assert new_image.size == DISK_SIZE


def test_write_data(new_image: Disk):
    part = Partition("test-part", 1024, uuid.uuid4(), 1)
    new_image.table.partitions.add(part)
    new_image.update_table()
    new_image.write_data(BYTE_DATA, part, 0)
    with open(new_image.image_path, "r+b") as f:
        f.seek(int.from_bytes(part.first_lba.data, "little") * new_image.sector_size)
        assert f.read(4) == BYTE_DATA
