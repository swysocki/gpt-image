import uuid

from gpt_image import disk, table
from gpt_image.partition import Partition


def test_e2e():
    new_disk = disk.Disk("test-disk.raw", 2 * 1024 * 1024, True)
    part1 = new_disk.create_partition("test-part", 2 * 1024, uuid.uuid4())
    # we should now be able to part1.write_bytes(b"\x00")
    assert type(part1) is Partition
    new_disk.update_table()
