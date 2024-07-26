import json
import uuid

import pytest

from gpt_image.geometry import Geometry
from gpt_image.partition import (
    Partition,
    PartitionAttribute,
    PartitionEntryArray,
    PartitionEntryError,
    PartitionType,
)

PART_NAME = "test-part"
PART_NAME_2 = "partition-2"
PART_NAME_3 = "partition3"
PART_UUID = "26be6d04-85fe-4fae-ba9c-1f47cf16f8d8"
PART_UUID_2 = "68ce2c22-d5a3-4246-b245-74190dec5582"


@pytest.fixture
def geo():
    return Geometry(8 * 1024 * 1024)


@pytest.fixture
def partitions():
    return [
        Partition(PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value),
        Partition(PART_NAME_2, 3 * 1024, PartitionType.LINUX_FILE_SYSTEM.value),
        Partition(PART_NAME_3, 6 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    ]


@pytest.fixture
def part_array(geo, partitions):
    array = PartitionEntryArray(geo)
    for part in partitions:
        array.add(part)
    return array


def test_partition_init_guid():
    part = Partition(PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    assert isinstance(uuid.UUID(part.partition_guid), uuid.UUID)
    del part
    part = Partition(
        PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value, PART_UUID
    )
    assert part.partition_guid == PART_UUID


def test_partition_repr():
    part = Partition(PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    part.attribute_flags = PartitionAttribute.READ_ONLY
    part_s = str(part)
    assert PART_NAME in part_s
    # attributes with leading underscore should not be in __repr__
    assert "_attribute" not in part_s
    part_d = json.loads(part_s)
    assert part_d.get("partition_name") == PART_NAME
    assert part_d.get("attribute_flags") == [PartitionAttribute.READ_ONLY.value]


def test_partition_attribute():
    part = Partition(PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
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
        PART_NAME,
        2 * 1024,
        PartitionType.LINUX_FILE_SYSTEM.value,
        partition_guid=PART_UUID,
    )
    part.attribute_flags = PartitionAttribute.READ_ONLY
    part_bytes = part.marshal()
    assert part_bytes[0:16] == uuid.UUID(PartitionType.LINUX_FILE_SYSTEM.value).bytes_le
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


def test_partition_read(geo):
    part_array = PartitionEntryArray(geo)
    part = Partition(
        PART_NAME,
        2 * 1024,
        PartitionType.LINUX_FILE_SYSTEM.value,
        partition_guid=PART_UUID,
    )
    part_array.add(part)
    part_bytes = part.marshal()
    new_part = Partition.unmarshal(part_bytes, geo.sector_size)
    assert new_part.partition_name == PART_NAME
    assert new_part.size == 2 * 1024
    assert new_part.type_guid.upper() == PartitionType.LINUX_FILE_SYSTEM.value
    assert new_part.partition_guid == PART_UUID
    # @TODO: read attributes from existing partitions


def test_partition_entry_add(geo, partitions):
    part_array = PartitionEntryArray(geo)
    part_array.add(partitions[0])
    # check partition LBAs. The default alignment is 8 sectors so the
    # first LBA will always be a factor of 8
    assert partitions[0].first_lba_staged == 40
    assert partitions[0].last_lba_staged == 43
    part_array.add(partitions[1])
    assert partitions[1].first_lba_staged == 48
    assert partitions[1].last_lba_staged == 53

    assert len(part_array.entries) == 2
    partitions[2].alignment = 20
    part_array.add(partitions[2])
    assert partitions[2].first_lba_staged == 60
    assert partitions[2].last_lba_staged == 71


def test_partition_entry_add_too_large(geo):
    part_array = PartitionEntryArray(geo)
    part1 = Partition("part1", 2 * 1024 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    part2 = Partition("part2", 10 * 1024 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    part3 = Partition("part3", 5 * 1024 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)

    # this should fit
    part_array.add(part1)
    # this will raise an error
    with pytest.raises(PartitionEntryError):
        part_array.add(part2)
    # this will fit within the disk LBA boundaries
    part_array.add(part3)


def test_partition_entry_remove(part_array):
    assert len(part_array.entries) == 3
    first_partition_start = part_array.entries[0].first_lba_staged
    second_partition_start = part_array.entries[1].first_lba_staged
    assert part_array.find(PART_NAME_2).first_lba_staged == second_partition_start
    assert part_array.find(PART_NAME_3).first_lba_staged != second_partition_start

    # start by removing one from the middle
    part = part_array.remove(PART_NAME_2)

    # make sure the correct partition was removed and returned
    assert part.partition_name == PART_NAME_2
    assert part_array.find(PART_NAME_2) == None

    # make sure the remaining entries look correct
    assert len(part_array.entries) == 2
    assert part_array.entries[0] == part_array.find(PART_NAME)
    assert part_array.entries[-1] == part_array.find(PART_NAME_3)

    # make sure the first partition did not shift
    assert part_array.find(PART_NAME).first_lba_staged == first_partition_start
    # make sure partition_3 got shifted into the second partition slot
    assert part_array.find(PART_NAME_3).first_lba_staged == second_partition_start
    part = part_array.find(PART_NAME_3)

    # now try removing one from the start
    part_array.remove(PART_NAME)
    assert len(part_array.entries) == 1
    assert part_array.find(PART_NAME) == None

    # try removing one that does not exist in the first place
    with pytest.raises(NameError):
        part_array.remove("does_not_exist")

    # try removing the only remaining partition
    part_array.remove(PART_NAME_3)
    assert len(part_array.entries) == 0


def test_partition_entry_resize(part_array):
    assert len(part_array.entries) == 3

    second_partition_size = part_array.entries[1].size_staged
    second_partition_end = part_array.entries[1].last_lba_staged
    third_partition_start = part_array.entries[2].first_lba_staged
    third_partition_size = part_array.entries[2].size_staged

    # grow the middle partition
    part = part_array.resize(PART_NAME_2, 2 * second_partition_size)
    assert part.partition_name == PART_NAME_2
    assert len(part_array.entries) == 3

    # make sure the second partition has actually grown,
    # and that the third partition has shifted to make room
    assert part.size_staged == 2 * second_partition_size
    assert part.last_lba_staged > second_partition_end
    assert part_array.find(PART_NAME_3).first_lba_staged > third_partition_start
    assert part_array.find(PART_NAME_3).size_staged == third_partition_size

    second_partition_end = part_array.entries[1].last_lba_staged
    third_partition_start = part_array.entries[2].first_lba_staged
    third_partition_end = part_array.entries[2].last_lba_staged

    # shrink the third (last) partition
    part = part_array.resize(PART_NAME_3, third_partition_size / 2)

    # make sure it shrunk, but did not shift
    assert part.size_staged == third_partition_size / 2
    assert part.first_lba_staged == third_partition_start
    assert part.last_lba_staged < third_partition_end
    assert part_array.find(PART_NAME_2).last_lba_staged == second_partition_end


def test_partition_entry_marshall(geo):
    part_array = PartitionEntryArray(geo)
    part1 = Partition(PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    part2 = Partition(PART_NAME_2, 3 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
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


def test_partition_find(geo):
    part_array = PartitionEntryArray(geo)
    part1 = Partition(PART_NAME, 2 * 1024, PartitionType.LINUX_FILE_SYSTEM.value)
    part2 = Partition(PART_NAME_2, 3 * 1024, PartitionType.LINUX_FILE_SYSTEM.value, partition_guid=PART_UUID)
    part_array.add(part1)
    part_array.add(part2)
    test_part = part_array.find(PART_NAME)
    assert test_part.partition_name == PART_NAME
    assert test_part.size_staged == 2 * 1024
    assert test_part.type_guid == PartitionType.LINUX_FILE_SYSTEM.value
    test_part = part_array.find(PART_UUID.upper())
    assert test_part.partition_name == PART_NAME_2
    test_part = part_array.find(PART_UUID.lower())
    assert test_part.partition_name == PART_NAME_2
    test_part = part_array.find(PART_UUID_2)
    assert test_part == None
