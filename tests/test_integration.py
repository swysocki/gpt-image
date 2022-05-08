import uuid
import os

from gpt_image import disk
from gpt_image.partition import Partition


def test_e2e():
    FILE_NAME = "tests/testdata/test-disk.raw"
    # cleanup old test file
    if os.path.isfile(FILE_NAME):
        os.remove(FILE_NAME)
    # this should produce a disk that can be opened and validated with gdisk/sgdisk
    new_disk = disk.Disk(FILE_NAME)
    new_disk.create(2 * 1024 * 1024)
    part1 = Partition("test-part", 2 * 1024, uuid.uuid4())

    new_disk.table.partitions.add(part1)
    new_disk.write()
