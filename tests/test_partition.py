from gpt_image.partition import Partition, PartitionEntryArray
from gpt_image.geometry import Geometry
import uuid

PART_NAME = "test-part"


def test_partition_init_blank():
    part = Partition()
    # everything should be zeroed
    assert part.type_guid.data == b"\x00" * 16
    assert part.partition_guid.data == b"\x00" * 16
    assert part.first_lba.data == b"\x00" * 8
    assert part.last_lba.data == b"\x00" * 8
    assert part.attribute_flags.data == b"\x00" * 8
    assert part.partition_name.data == b"\x00" * 72


def test_partition_init_real():
    part = Partition(PART_NAME, 2 * 1024)
    assert type(uuid.UUID(bytes=part.type_guid.data)) is uuid.UUID
    assert type(uuid.UUID(bytes=part.partition_guid.data)) is uuid.UUID
    assert PART_NAME in part.partition_name.data.decode("utf_16_le")
    assert part.size == 2 * 1024


def test_add():
    geo = Geometry(8 * 1024 * 1024)
    pa = PartitionEntryArray(geo)
    new_part = Partition(PART_NAME, 2 * 1024)
    pa.add(new_part)
    assert PART_NAME in pa.entries[0].partition_name.data.decode("utf_16_le")


def test_get_next_partition():
    geo = Geometry(8 * 1024 * 1024)
    pa = PartitionEntryArray(geo)
    next = pa._get_next_partition()
    assert next == 0
    new_part = Partition(PART_NAME, 2 * 1024)
    pa.add(new_part)
    next = pa._get_next_partition()
    assert next == 1
