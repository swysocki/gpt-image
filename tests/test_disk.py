import pytest
from gpt_image.disk import Disk
from gpt_image.partition import Partition

BYTE_DATA = b"\x01\x02\x03\x04"
DISK_SIZE = 2 * 1024 * 1024
OFFSET = 32


@pytest.fixture
def new_image(tmp_path):
    image_name = tmp_path / "test.img"
    disk = Disk(image_name)
    disk.create(DISK_SIZE * 2)
    part1 = Partition("partition1", 2 * 1024 * 1024)
    part2 = Partition("partition2", 3 * 1024 * 1024)
    disk.table.partitions.add(part1)
    disk.table.partitions.add(part2)
    disk.write()
    return image_name


def test_disk_create(tmp_path):
    """Test creating a new disk image"""
    disk_path = tmp_path / "test-disk.img"
    disk = Disk(disk_path)
    assert disk.image_path == disk_path.resolve()
    assert disk.sector_size == 512
    disk.create(DISK_SIZE)
    assert disk.table.primary_header.signature.data == b"EFI PART"
    assert disk.table.primary_header.backup is False


def test_disk_open(new_image):
    disk = Disk(new_image)
    disk.open()
    assert disk.size == DISK_SIZE * 2
    assert disk.table.primary_header.backup is False
    assert disk.table.secondary_header.backup is True
    assert disk.table.primary_header.partition_entry_lba.data == 2
    assert disk.table.secondary_header.partition_entry_lba.data == 8159
    assert len(disk.table.partitions.entries) == 2
    assert disk.table.partitions.entries[0].partition_name.data == "partition1"


# def test_write_data_default(new_image: Disk):
#     part = Partition("test-part", 1024, uuid.uuid4(), 1)
#     new_image.table.partitions.add(part)
#     new_image.update_table()
#     new_image.write_data(BYTE_DATA, part)
#     with open(new_image.image_path, "r+b") as f:
#         f.seek(part.first_lba.data * new_image.sector_size)
#         assert f.read(4) == BYTE_DATA
#
#
# def test_write_data_offset(new_image: Disk):
#     part = Partition("test-part", 1024, uuid.uuid4(), 1)
#     new_image.table.partitions.add(part)
#     new_image.update_table()
#     new_image.write_data(BYTE_DATA, part, OFFSET)
#     new_image.write_data(BYTE_DATA, part, OFFSET + OFFSET)
#     with open(new_image.image_path, "r+b") as f:
#         f.seek(part.first_lba.data * new_image.sector_size + OFFSET)
#         assert f.read(4) == BYTE_DATA
#         f.seek(part.first_lba.data * new_image.sector_size + OFFSET + OFFSET)
#         assert f.read(4) == BYTE_DATA
#
#
# def test_write_data_type_error(new_image: Disk):
#     part = Partition("test-part", 1024, uuid.uuid4())
#     with pytest.raises(ValueError):
#         new_image.write_data(str("foobar"), part)  # type: ignore
