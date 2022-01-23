import pytest
from gpt_image.disk import Disk


def test_disk_new(tmp_path):
    """Test creating a new disk image"""
    image_size = 2 * 1024 * 1024  # 2 MB
    image_name = tmp_path / "test.img"
    abs_path = image_name.resolve()
    disk = Disk(str(abs_path), image_size, fresh_disk=True)
    disk.update_table()
    assert disk.size == image_size
    assert disk.image_path == image_name
    assert image_name.stat().st_size == image_size
