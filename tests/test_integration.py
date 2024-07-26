import json
import shutil
import subprocess
import sys

import pytest

from gpt_image import disk
from gpt_image.partition import Partition, PartitionAttribute, PartitionType

STATIC_UUID = "4133e7fe-0be9-4097-b617-e3373fa0535e"
DISK_SIZE = 2 * 1024 * 1024  # (2MB)
PART1_NAME = "partition1"
PART1_SIZE = 2 * 1024  # 2KB
PART2_NAME = "partition-number2"
PART2_SIZE = 4 * 1024  # 4KB


@pytest.fixture
def create_image(tmp_path):
    image = tmp_path / "test-disk.raw"

    # this should produce a disk that can be opened and validated with GPT tools
    new_disk = disk.Disk(image)
    new_disk.create(DISK_SIZE)
    part1 = Partition(PART1_NAME, PART1_SIZE, PartitionType.LINUX_FILE_SYSTEM.value)
    part1.attribute_flags = PartitionAttribute.HIDDEN
    new_disk.table.partitions.add(part1)

    part2 = Partition(
        PART2_NAME, PART2_SIZE, PartitionType.LINUX_FILE_SYSTEM.value, STATIC_UUID
    )
    new_disk.table.partitions.add(part2)

    new_disk.commit()
    return image


@pytest.mark.skipif(sys.platform != "linux", reason="requires linux to run")
@pytest.mark.skipif(shutil.which("sfdisk") is None, reason="requires sfdisk utility")
@pytest.mark.skipif(shutil.which("sgdisk") is None, reason="requires sgdisk utility")
def test_sfdisk(create_image):
    sfdisk = shutil.which("sfdisk")
    sgdisk = shutil.which("sgdisk")
    result = subprocess.run(
        [sgdisk, "-v", create_image], capture_output=True, text=True
    )
    assert "no problems found" in (result.stdout).lower()
    result = subprocess.run(
        [sfdisk, "--json", create_image], capture_output=True, text=True
    )
    assert result.returncode == 0
    part_info = json.loads(result.stdout)
    assert part_info.get("partitiontable").get("label") == "gpt"
    # a bit of math is required to get the total disk size from the sfdisk output
    # the 34 sectors of GPT header must be added to the lastlba to get the total size
    size = (part_info.get("partitiontable").get("lastlba") + 34) * 512
    assert size == DISK_SIZE

    # test partitions
    partitions = part_info.get("partitiontable").get("partitions")
    assert partitions[0].get("name") == PART1_NAME
    assert partitions[0].get("size") == (PART1_SIZE / 512)
    assert (
        partitions[0].get("start") == 40
    )  # 34 is the first usable but alignment is 8, so 40 is the start
    assert partitions[0].get("attrs") == "GUID:62"
    assert partitions[1].get("name") == PART2_NAME
    assert partitions[1].get("size") == (PART2_SIZE / 512)
    assert partitions[1].get("start") == 48
    assert partitions[1].get("uuid") == STATIC_UUID.upper()

    disk_image = disk.Disk.open(create_image)
    disk_image.table.partitions.remove(PART1_NAME)
    disk_image.table.partitions.resize(PART2_NAME, PART1_SIZE)
    disk_image.commit()

    result = subprocess.run(
        [sgdisk, "-v", create_image], capture_output=True, text=True
    )
    assert "no problems found" in (result.stdout).lower()
    result = subprocess.run(
        [sfdisk, "--json", create_image], capture_output=True, text=True
    )
    assert result.returncode == 0
    part_info = json.loads(result.stdout)
    partitions = part_info.get("partitiontable").get("partitions")

    assert len(partitions) == 1
    assert partitions[0].get("name") == PART2_NAME
    assert partitions[0].get("size") == (PART1_SIZE / 512)
