from gpt_image.geometry import Geometry


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
