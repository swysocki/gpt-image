import uuid

from gpt_image.geometry import Geometry
from gpt_image.table import Table
from gpt_image.partition import Partition

DISK_SIZE = 2 * 1024 * 1024  # 2 MB disk


def test_lba_offsets():
    """Test sector size and ensure proper alignment"""
    # default sector size 512
    geo = Geometry(DISK_SIZE)
    table = Table(geo)
    # create a partition that falls between the 512 sector_size
    # this should round up and use 2 sectors (34-35) the next
    # partition should start at sector (lba) 36
    part1 = Partition("small-part", 768, uuid.uuid4(), 1)
    part2 = Partition("next-part", 1024, uuid.uuid4(), 1)
    table.partitions.add(part1)
    table.partitions.add(part2)
    assert table.partitions.entries[0].last_lba.data == (35).to_bytes(8, "little")
    assert table.partitions.entries[1].first_lba.data == (36).to_bytes(8, "little")
