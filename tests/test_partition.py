import json
import uuid

from gpt_image.geometry import Geometry
from gpt_image.partition import (Partition, PartitionAttribute,
                                 PartitionEntryArray)

PART_NAME = "test-part"
PART_NAME_2 = "partition-2"
PART_UUID = "26be6d04-85fe-4fae-ba9c-1f47cf16f8d8"


def test_partition_init_guid():
    part = Partition(PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM)
    assert isinstance(uuid.UUID(part.partition_guid), uuid.UUID)
    del part
    part = Partition(PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM, PART_UUID)
    assert part.partition_guid == PART_UUID


def test_partition_repr():
    part = Partition(PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM)
    part.attribute_flags = PartitionAttribute.READ_ONLY
    part_s = str(part)
    assert PART_NAME in part_s
    # attributes with leading underscore should not be in __repr__
    assert "_attribute" not in part_s
    part_d = json.loads(part_s)
    assert part_d.get("partition_name") == PART_NAME
    assert part_d.get("attribute_flags") == [PartitionAttribute.READ_ONLY.value]


def test_partition_attribute():
    part = Partition(PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM)
    # flags are set to NONE by default
    assert part.attribute_flags == []

    # setting the READ_ONLY flag sets bit 60 which will have an
    # integer value
    part.attribute_flags = PartitionAttribute.READ_ONLY
    assert part.attribute_flags == [PartitionAttribute.READ_ONLY]
    part.attribute_flags = PartitionAttribute.HIDDEN
    # this should return 2 values, HIDDEN and READ_ONLY
    assert part.attribute_flags == [
        PartitionAttribute.HIDDEN,
        PartitionAttribute.READ_ONLY,
    ]

    # setting NONE should clear all flags
    part.attribute_flags = PartitionAttribute.NONE
    assert part.attribute_flags == []


def test_partition_marshal():
    part = Partition(
        PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM, partition_guid=PART_UUID
    )
    part.attribute_flags = PartitionAttribute.READ_ONLY
    part_bytes = part.marshal()
    assert part_bytes[0:16] == uuid.UUID(Partition.LINUX_FILE_SYSTEM).bytes_le
    assert part_bytes[16:32] == uuid.UUID(PART_UUID).bytes_le
    assert part_bytes[32:40] == b"\x00" * 8
    assert part_bytes[40:48] == b"\x00" * 8
    assert part_bytes[48:56] == (2**PartitionAttribute.READ_ONLY.value).to_bytes(
        8, byteorder="little"
    )
    # pad this to 72 bytes
    assert part_bytes[56:128] == bytes(PART_NAME, encoding="utf_16_le").ljust(
        72, b"\x00"
    )


def test_partition_read():
    geo = Geometry(8 * 1024 * 1024)
    part_array = PartitionEntryArray(geo)
    part = Partition(
        PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM, partition_guid=PART_UUID
    )
    part_array.add(part)
    part_bytes = part.marshal()
    new_part = Partition.unmarshal(part_bytes, geo.sector_size)
    assert new_part.partition_name == PART_NAME
    assert new_part.size == 2 * 1024
    assert new_part.type_guid.upper() == Partition.LINUX_FILE_SYSTEM
    assert new_part.partition_guid == PART_UUID
    # @TODO: read attributes from existing partitions


def test_partition_entry_add():
    geo = Geometry(8 * 1024 * 1024)
    part_array = PartitionEntryArray(geo)
    part1 = Partition(PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM)
    part_array.add(part1)
    # check partition LBAs. The default alignment is 8 sectors so the
    # first LBA will always be a factor of 8
    assert part1.first_lba == 40
    assert part1.last_lba == 43
    part2 = Partition(PART_NAME_2, 3 * 1024, Partition.LINUX_FILE_SYSTEM)
    part_array.add(part2)
    assert part2.first_lba == 48
    assert part2.last_lba == 53

    assert len(part_array.entries) == 2


def test_get_first_lba():
    pass


def test_get_last_lba():
    pass


def test_partition_entry_marshall():
    geo = Geometry(8 * 1024 * 1024)
    part_array = PartitionEntryArray(geo)
    part1 = Partition(PART_NAME, 2 * 1024, Partition.LINUX_FILE_SYSTEM)
    part2 = Partition(PART_NAME_2, 3 * 1024, Partition.LINUX_FILE_SYSTEM)
    part_array.add(part1)
    part_array.add(part2)

    part_array_bytes = part_array.marshal()
    assert (
        len(part_array_bytes)
        == PartitionEntryArray.EntryCount * PartitionEntryArray.EntryLength
    )
    part1_bytes = part_array_bytes[:128]
    part2_bytes = part_array_bytes[128:256]
    part1_unmarshal = Partition.unmarshal(part1_bytes, geo.sector_size)
    part2_unmarshal = Partition.unmarshal(part2_bytes, geo.sector_size)
    assert part1_unmarshal.partition_name == PART_NAME
    assert part2_unmarshal.partition_name == PART_NAME_2
