from pygpt_disk import table, disk
import pytest
import uuid

DISK_SIZE = 8 * 1024 * 1024
SECTOR_SIZE = 512
LAST_LBA = int(DISK_SIZE / SECTOR_SIZE)
SIGNATURE = b"EFI PART"
REVISION = b"\x00\x00\x01\x00"
HEADER_SIZE = b"\x5C\x00\x00\x00"
PRIMARY_LBA = 1
BACKUP_LBA = LAST_LBA - 1


@pytest.fixture
def fresh_disk(tmp_path):
    image_path = tmp_path / "table-test.img"
    return disk.Disk(DISK_SIZE, image_path)


def test_init(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)
    assert type(t.disk) == disk.Disk


def test__write_header(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)

    def read_header(primary=True):
        assert t.disk.buffer.read(8) == SIGNATURE
        assert t.disk.buffer.read(4) == REVISION
        assert t.disk.buffer.read(4) == HEADER_SIZE
        # header crc ensure it is no longer zeroed
        assert t.disk.buffer.read(4) != b"\x00" * 4
        # reserved
        assert t.disk.buffer.read(4) == b"\x00" * 4
        if primary:
            # primary header location LBA
            assert t.disk.buffer.read(8) == (PRIMARY_LBA).to_bytes(8, "little")
            # secondary header LBA
            assert t.disk.buffer.read(8) == (BACKUP_LBA).to_bytes(8, "little")
        else:
            # the locations will be swapped for backup header
            assert t.disk.buffer.read(8) == (BACKUP_LBA).to_bytes(8, "little")
            assert t.disk.buffer.read(8) == (PRIMARY_LBA).to_bytes(8, "little")
        # start LBA
        assert t.disk.buffer.read(8) == (34).to_bytes(8, "little")
        # last LBA
        assert t.disk.buffer.read(8) == (LAST_LBA - 34).to_bytes(8, "little")
        # GUID
        disk_guid = t.disk.buffer.read(16)
        assert type(uuid.UUID(bytes_le=disk_guid)) == uuid.UUID
        # partition array start LBA
        assert t.disk.buffer.read(8) == (2).to_bytes(8, "little")
        # partition array length
        assert t.disk.buffer.read(4) == (0).to_bytes(4, "little")
        # partition entry length
        assert t.disk.buffer.read(4) == (128).to_bytes(4, "little")
        # partition array crc
        # initially zeroed
        assert t.disk.buffer.read(4) == (0).to_bytes(4, "little")

    # test primary header
    t._write_header("primary")
    t.disk.buffer.seek(fresh_disk.sector_size)
    read_header()

    # test backup header
    t._write_header("backup")
    t.disk.buffer.seek(int(BACKUP_LBA * SECTOR_SIZE))
    read_header(False)


def test__checksum_header(fresh_disk: disk.Disk):
    CRC_OFFSET = 16  # offset relative to start of header
    t = table.Table(fresh_disk)
    t._write_header("primary")
    t._checksum_header(t.primary_header_start_byte)

    # read new checksum
    t.disk.buffer.seek(t.primary_header_start_byte + CRC_OFFSET)
    raw_crc = t.disk.buffer.read(4)
    assert raw_crc == (t._header_crc.content).to_bytes(4, "little")

    t._write_header("backup")
    t._checksum_header(t.backup_header_start_byte)
    t.disk.buffer.seek(t.backup_header_start_byte + CRC_OFFSET)
    raw_crc = t.disk.buffer.read(4)
    assert raw_crc == (t._header_crc.content).to_bytes(4, "little")
