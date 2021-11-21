from pygpt_disk import table, disk
import pytest

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


def test_write_header(fresh_disk: disk.Disk):
    t = table.Table(fresh_disk)

    def read_header(primary=True):
        assert t.disk.buffer.read(8) == SIGNATURE
        assert t.disk.buffer.read(4) == REVISION
        assert t.disk.buffer.read(4) == HEADER_SIZE
        # header crc (zeroed until calculated)
        assert t.disk.buffer.read(4) == b"\x00" * 4
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

    # test primary header
    t._write_header("primary")
    t.disk.buffer.seek(fresh_disk.sector_size)
    read_header()

    # test backup header
    t._write_header("backup")
    t.disk.buffer.seek(int(BACKUP_LBA * SECTOR_SIZE))
    read_header(False)
