import struct
import uuid

from gpt_image.geometry import Geometry
from gpt_image.partition import Partition, PartitionEntryArray

PART_NAME = "test-part"


def test_partition_init_blank():
    part = Partition()
    # everything should be zeroed
    assert part.type_guid.data_bytes == b"\x00" * 16
    assert part.partition_guid.data_bytes == b"\x00" * 16
    assert part.first_lba.data_bytes == b"\x00" * 8
    assert part.last_lba.data_bytes == b"\x00" * 8
    assert part.attribute_flags.data_bytes == b"\x00" * 8
    assert part.partition_name.data_bytes == b"\x00" * 72


def test_partition_init_real():
    part = Partition(PART_NAME, 2 * 1024)
    assert type(uuid.UUID(bytes=part.type_guid.data)) is uuid.UUID
    assert type(uuid.UUID(bytes=part.partition_guid.data)) is uuid.UUID
    assert part.partition_name.data_bytes == struct.pack(
        "<72s", bytes(PART_NAME, encoding="utf_16_le")
    )
    assert part.partition_name.data == bytes(PART_NAME, encoding="utf_16_le")

    assert part.size == 2 * 1024


def test_add():
    geo = Geometry(8 * 1024 * 1024)
    pa = PartitionEntryArray(geo)
    new_part = Partition(PART_NAME, 2 * 1024)
    pa.add(new_part)
    # name is encoded with utf_16_le
    assert PART_NAME == pa.entries[0].partition_name.data.decode(encoding="utf_16_le")


def test_unmarshal():
    part = Partition(PART_NAME, 4 * 1024)
    part_b = part.as_bytes()

    part2 = Partition()
    part2.read(part_b)
    assert len(part2.partition_name.data_bytes) == part2.partition_name.length
    assert part2.partition_name.data == PART_NAME
