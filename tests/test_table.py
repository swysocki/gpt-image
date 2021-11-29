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
    return disk.Disk(image_path, DISK_SIZE)


def test_init(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)
    assert type(t.disk) == disk.Disk


def test__write_header(fresh_disk: disk.Disk):
    primary_header = table.Table(fresh_disk)
    primary_header._write_table()

    def read_header(header):
        assert header.buffer.read(8) == SIGNATURE
        assert header.buffer.read(4) == REVISION
        assert header.buffer.read(4) == HEADER_SIZE
        # header crc ensure it is no longer zeroed
        assert header.buffer.read(4) != b"\x00" * 4
        # reserved
        assert header.buffer.read(4) == b"\x00" * 4
        if not header.backup:
            # primary header location LBA
            assert header.buffer.read(8) == (PRIMARY_LBA).to_bytes(8, "little")
            # secondary header LBA
            assert header.buffer.read(8) == (BACKUP_LBA).to_bytes(8, "little")
        if header.backup:
            # the locations will be swapped for backup header
            assert header.buffer.read(8) == (BACKUP_LBA).to_bytes(8, "little")
            assert header.buffer.read(8) == (PRIMARY_LBA).to_bytes(8, "little")
        # start LBA
        assert header.buffer.read(8) == (34).to_bytes(8, "little")
        # last LBA
        assert header.buffer.read(8) == (LAST_LBA - 34).to_bytes(8, "little")
        # GUID
        disk_guid = header.buffer.read(16)
        assert type(uuid.UUID(bytes_le=disk_guid)) == uuid.UUID
        # partition array start LBA
        if not header.backup:
            assert header.buffer.read(8) == (2).to_bytes(8, "little")
        if header.backup:
            assert header.buffer.read(8) == (LAST_LBA - 33).to_bytes(8, "little")
        # partition array length
        assert header.buffer.read(4) == (128).to_bytes(4, "little")
        # partition entry length
        assert header.buffer.read(4) == (128).to_bytes(4, "little")
        # partition array crc
        # initially zeroed
        assert header.buffer.read(4) != (0).to_bytes(4, "little")

    # test primary header
    primary_header._write_header()
    primary_header.buffer.seek(0)

    read_header(primary_header)

    backup_header = table.Table(fresh_disk, is_backup=True)
    backup_header._write_table()
    backup_header._write_header()
    backup_header.buffer.seek(
        int(32 * fresh_disk.sector_size)
    )  # secondary header lba start
    read_header(backup_header)
