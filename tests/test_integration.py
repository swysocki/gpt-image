import uuid

from gpt_image import disk
from gpt_image.partition import Partition


def test_e2e():
    # this should produce a disk that can be opened and validated with gdisk/sgdisk
    new_disk = disk.Disk("test-disk.raw", 2 * 1024 * 1024, fresh_disk=True)
    part1 = Partition("test-part", 2 * 1024, uuid.uuid4())

    new_disk.table.partitions.add(part1)
    new_disk.update_table()
