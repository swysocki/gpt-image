import uuid

from gpt_image import disk, table


def test_e2e():
    new_disk = disk.Disk("test-disk.raw", 2 * 1024 * 1024, True)

    t = table.Table(new_disk)
    # t.create_partition("test-part", 2 * 1024, uuid.uuid4())
    t.write()
