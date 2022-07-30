import json
import uuid

import pytest

from gpt_image.geometry import Geometry
from gpt_image.table import Header, ProtectiveMBR, Table

DISK_SIZE = 2 * 1024 * 1024  # 2 MB disk
DISK_GUID = "51581dee-faaa-404d-b0fe-85dc65157702"


@pytest.fixture
def new_geometry():
    return Geometry(DISK_SIZE)


def test_protective_mbr_marshall(new_geometry: Geometry):
    pmbr = ProtectiveMBR(new_geometry)
    pmbr_bytes = pmbr.marshal()
    assert pmbr_bytes[:446] == b"\x00" * 446
    assert pmbr_bytes[446:447] == b"\x00"
    assert pmbr_bytes[447:450] == b"\x00" * 3
    assert pmbr_bytes[450:451] == b"\xEE"
    assert pmbr_bytes[451:454] == b"\x00" * 3
    assert pmbr_bytes[454:458] == b"\x01\x00\x00\x00"
    assert pmbr_bytes[458:462] == b"\xff\x0f\x00\x00"
    assert pmbr_bytes[462:510] == b"\x00" * 48
    assert pmbr_bytes[510:512] == b"\x55\xAA"


def test_protective_mbr_read(new_geometry: Geometry):
    pmbr = ProtectiveMBR(new_geometry)
    pmbr_bytes = pmbr.marshal()

    pmbr_o = ProtectiveMBR.unmarshal(pmbr_bytes, new_geometry)
    assert pmbr_o.boot_indicator == 0
    assert pmbr_o.start_chs == b"\x00"
    assert pmbr_o.partition_type == b"\xEE"
    assert pmbr_o.end_chs == b"\x00"
    assert pmbr_o.start_sector == 1
    assert pmbr_o.partition_size == 4095
    assert pmbr_o.signature == b"\x55\xAA"


def test_header_marshall(new_geometry: Geometry):
    header = Header(
        new_geometry,
        guid=DISK_GUID,
    )
    header_b = header.marshal()
    assert len(header_b) == new_geometry.sector_size
    assert header_b[:8] == b"EFI PART"
    assert header_b[8:12] == b"\x00\x00\x01\x00"
    assert header_b[12:16] == b"\\\x00\x00\x00"
    assert header_b[16:20] == b"\x00" * 4
    assert header_b[20:24] == b"\x00" * 4
    assert header_b[24:32] == b"\x01" + b"\x00" * 7
    assert header_b[32:40] == b"\xff\x0f" + b"\x00" * 6
    assert header_b[40:48] == b'"\x00' + b"\x00" * 6
    assert header_b[48:56] == b"\xde\x0f" + b"\x00" * 6
    assert header_b[56:72] == uuid.UUID(DISK_GUID).bytes_le
    assert header_b[72:80] == b"\x02" + b"\x00" * 7
    assert header_b[80:84] == b"\x80" + b"\x00" * 3
    assert header_b[84:88] == b"\x80" + b"\x00" * 3
    assert header_b[88:92] == b"\x00" * 4


def test_header_read(new_geometry: Geometry):
    header = Header(
        new_geometry,
        guid=DISK_GUID,
    )
    header_b = header.marshal()
    assert len(header_b) == new_geometry.sector_size

    header_o = Header.unmarshal(header_b[: Header._HEADER_SIZE], new_geometry)
    assert header_o.signature == Header._SIGNATURE
    assert header_o.revision == Header._REVISION
    assert header_o.header_size == Header._HEADER_SIZE


def test_header_repr(new_geometry: Geometry):
    header = Header(new_geometry, guid=DISK_GUID)
    header_s = header.__repr__()
    assert "EFI PART" in header_s
    header_d = json.loads(header_s)
    assert header_d.get("header_size") == Header._HEADER_SIZE
    assert len(header_d) == 15


def test_table_init(new_geometry):
    geo = new_geometry
    table = Table(geo)
    assert table.primary_header.backup is False
    assert table.secondary_header.backup is True


def test_checksum_partitions(new_geometry):
    table = Table(new_geometry)
    # partition checksum will be blank before when initialized
    assert table.primary_header.partition_entry_array_crc32 == 0
    table.checksum_partitions(table.primary_header)
    # test that the checksum is no longer zeroed
    assert (
        table.primary_header.partition_entry_array_crc32 == 2874462854
    )  # predictable binascii.crc32


def test_checksum_header(new_geometry):
    table = Table(new_geometry)
    assert table.primary_header.header_crc32 == 0
    # create a predictable GUID so that the test is predictable
    table.primary_header.disk_guid = DISK_GUID
    table.checksum_header(table.primary_header)
    assert table.primary_header.header_crc32 == 82915359


def test_update(new_geometry):
    table = Table(new_geometry)
    table.update()
    assert table.primary_header.header_crc32 != b"\x00" * 4
    assert table.secondary_header.header_crc32 != b"\x00" * 4
    assert table.primary_header.partition_entry_array_crc32 != b"\x00" * 4
    assert table.secondary_header.partition_entry_array_crc32 != b"\x00" * 4
