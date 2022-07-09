import uuid

import pytest
from gpt_image.geometry import Geometry
from gpt_image.table import Header, ProtectiveMBR, Table

DISK_SIZE = 2 * 1024 * 1024  # 2 MB disk


@pytest.fixture
def new_geometry():
    return Geometry(DISK_SIZE)


def test_protective_mbr_init(new_geometry):
    geo = new_geometry
    pmbr = ProtectiveMBR(geo)
    assert type(pmbr.byte_structure) == bytes
    pmbr_bytes = pmbr.byte_structure
    assert pmbr_bytes[pmbr.partition_type.offset : pmbr.partition_type.end] == b"\xEE"
    assert pmbr_bytes[
        pmbr.start_sector.offset : pmbr.start_sector.end
    ] == geo.my_lba.to_bytes(4, "little")
    assert pmbr_bytes[pmbr.partition_size.offset : pmbr.partition_size.end] == (
        geo.total_sectors - 1
    ).to_bytes(4, "little")


def test_proctective_mbr_read(new_geometry):
    pmbr = ProtectiveMBR(new_geometry)
    # change partition type to test it's read back properly
    pmbr.partition_type.data = b"\xFF"
    pmbr_b = pmbr.byte_structure
    new_pmbr = ProtectiveMBR(new_geometry)
    new_pmbr.read(pmbr_b)
    assert new_pmbr.partition_type.data == b"\xFF"


def test_header_init_primary(new_geometry):
    geo = new_geometry
    head = Header(geo, uuid.uuid4())
    assert head.backup is False
    assert head.my_lba.data == geo.my_lba
    assert head.alternate_lba.data == geo.alternate_lba
    assert head.partition_entry_lba.data == geo.partition_entry_lba


def test_header_init_backup(new_geometry):
    geo = new_geometry
    head = Header(geo, uuid.uuid4(), is_backup=True)
    assert head.backup is True
    # ensure the header LBA has been swapped
    assert head.my_lba.data == geo.alternate_lba
    assert head.alternate_lba.data == geo.my_lba
    assert head.partition_entry_start_byte == 0
    assert head.header_start_byte == int(32 * geo.sector_size)


def test_header_read(new_geometry):
    head = Header(new_geometry, uuid.uuid4())
    head_b = head.byte_structure

    head_ex = Header(new_geometry)
    head_ex.read(head_b)
    assert head_ex.signature.data == head.signature.data
    assert head_ex.revision.data == head.revision.data
    assert head_ex.revision.data == head.revision.data
    assert head_ex.disk_guid.data == head.disk_guid.data


def test_table_init(new_geometry):
    geo = new_geometry
    table = Table(geo)
    assert table.primary_header.backup is False
    assert table.secondary_header.backup is True


def test_checksum_partitions(new_geometry):
    table = Table(new_geometry)
    # partition checksum will be blank before when initialized
    assert table.primary_header.partition_entry_array_crc32.data == 0
    table.checksum_partitions(table.primary_header)
    # test that the checksum is no longer zeroed
    assert (
        table.primary_header.partition_entry_array_crc32.data == 2874462854
    )  # predictable binascii.crc32


def test_checksum_header(new_geometry):
    table = Table(new_geometry)
    assert table.primary_header.header_crc32.data == 0
    table.checksum_header(table.primary_header)
    # @TODO: (sjw) create header with static UUID
    # the crc is not predictable because the Header UUID is dynamic
    assert table.primary_header.header_crc32.data > 0


def test_update(new_geometry):
    table = Table(new_geometry)
    table.update()
    assert table.primary_header.header_crc32 != b"\x00" * 4
    assert table.secondary_header.header_crc32 != b"\x00" * 4
    assert table.primary_header.partition_entry_array_crc32 != b"\x00" * 4
    assert table.secondary_header.partition_entry_array_crc32 != b"\x00" * 4
