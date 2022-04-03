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
    assert type(pmbr.as_bytes()) == bytes
    pmbr_bytes = pmbr.as_bytes()
    assert pmbr_bytes[4:5] == b"\xEE"
    assert pmbr_bytes[8:12] == geo.primary_header_lba.to_bytes(4, "little")
    assert pmbr_bytes[12:16] == (geo.total_sectors - 1).to_bytes(4, "little")


def test_header_init_primary(new_geometry):
    geo = new_geometry
    head = Header(geo, uuid.uuid4())
    assert head.backup is False
    assert head.primary_header_lba.data == geo.primary_header_lba.to_bytes(8, "little")
    assert head.secondary_header_lba.data == geo.backup_header_lba.to_bytes(8, "little")
    assert head.partition_array_start.data == geo.primary_array_lba.to_bytes(
        8, "little"
    )


def test_header_init_backup(new_geometry):
    geo = new_geometry
    head = Header(geo, uuid.uuid4(), is_backup=True)
    assert head.backup is True
    # ensure the header LBA has been swapped
    assert head.primary_header_lba.data == geo.backup_header_lba.to_bytes(8, "little")
    assert head.secondary_header_lba.data == geo.primary_header_lba.to_bytes(
        8, "little"
    )
    assert head.partition_entry_start_byte == 0
    assert head.header_start_byte == int(32 * geo.sector_size)


def test_table_init(new_geometry):
    geo = new_geometry
    table = Table(geo)
    assert table.primary_header.backup is False
    assert table.secondary_header.backup is True


def test_checksum_partitions(new_geometry):
    table = Table(new_geometry)
    # partition checksum will be blank before when initialized
    assert table.primary_header.partition_array_crc.data == b"\x00" * 4
    table.checksum_partitions(table.primary_header)
    # test that the checksum is no longer zeroed
    assert table.primary_header.partition_array_crc.data != b"\x00" * 4


def test_checksum_header(new_geometry):
    table = Table(new_geometry)
    assert table.primary_header.header_crc.data == b"\x00" * 4
    table.checksum_header(table.primary_header)
    assert table.primary_header.header_crc.data != b"\x00" * 4


def test_update(new_geometry):
    table = Table(new_geometry)
    table.update()
    assert table.primary_header.header_crc != b"\x00" * 4
    assert table.secondary_header.header_crc != b"\x00" * 4
    assert table.primary_header.partition_array_crc != b"\x00" * 4
    assert table.secondary_header.partition_array_crc != b"\x00" * 4
