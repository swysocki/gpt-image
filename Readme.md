# GPT Image

Create GUID Partition Table disk images on local disks.  Written in pure Python
`gpt-image` allows GPT disk images to be _built_ on a local filesystem and
exported to a destination device.

This is useful for creating a disk image on SD Cards or embedded devices.

## Quick Start

```python

import gpt_image

# create a new, 8 MB disk, size is in bytes
disk = gpt_image.disk.Disk("disk-image.raw", 8 * 1024 * 1024, fresh_disk=True)

# create a 2MB partition, default is a Linux partition
partition = gpt_image.partition.Partition("partition1", 2 * 1024 * 1024, uuid.uuid4())

# add the partition to disk
disk.table.partitions.add(partition)
disk.update_table()

# write data to disk, data must be in bytes
with open("binary_data.bin", "r+b") as f:
    data = f.read()
    disk.write_data(data, partition)

```
