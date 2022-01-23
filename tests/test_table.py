import uuid

import pytest
from gpt_image.disk import Disk, Geometry
from gpt_image.table import Table

DISK_SIZE = 2 * 1024 * 1024  # 2 MB disk


def test_sector_size(tmp_path):
    """Test that sector size impacts partition
    start and end sectors
    """
    # default sector size 512
    img_path = tmp_path / "test.img"
    disk = Disk(img_path, DISK_SIZE)
    table = Table(disk)
    # create a partition that falls between the 512 sector_size
    # this should round up and use 2 sectors (34-35) the next
    # partition should start at sector (lba) 36
    table.create_partition("small-part", 768, uuid.uuid4(), 1)
    table.create_partition("next-part", 1024, uuid.uuid4(), 1)
    assert table.partitions.entries[0].last_lba.data == (35).to_bytes(8, "little")
    assert table.partitions.entries[1].first_lba.data == (36).to_bytes(8, "little")
