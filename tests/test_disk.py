from pathlib import Path

import pytest
from gpt_image.disk import Disk, Geometry


def test_default_geometry():
    """Simple tests to ensure math is sane

    We use statically calculated values (magic numbers) instead of
    trusting more math :)

    """
    disk_size = 2 * 1024 * 1024
    geo = Geometry(disk_size)
    assert geo.total_sectors == 4096
    assert geo.total_lba == 4096
    assert geo.partition_last_lba == 4062
    assert geo.primary_header_byte == 512
    assert geo.primary_array_byte == 1024
    assert geo.backup_header_lba == 4095
    assert geo.backup_header_byte == 2096640
    assert geo.backup_array_lba == 4063
    assert geo.backup_array_byte == 2080256


def test_disk_new(tmp_path):
    """Test creating a new disk image"""
    image_size = 2 * 1024 * 1024  # 2 MB
    image_name = tmp_path / "test.img"
    abs_path = image_name.resolve()
    disk = Disk(str(abs_path), image_size)
    assert Path(disk.name).exists()
    assert disk.size == image_size
    assert disk.image_path == image_name
    assert image_name.stat().st_size == image_size


def test_disk_existing(tmp_path):
    """Test existing disk image"""
    image_size = 2 * 1024 * 1024  # 2 MB
    image_name = tmp_path / "test.img"
    abs_path = image_name.resolve()
    image_name.touch()
    image_name.write_bytes(b"\x00" * image_size)

    disk = Disk(str(abs_path))
    assert disk.size == image_size
    assert disk.image_path == image_name
    assert image_name.stat().st_size == image_size
