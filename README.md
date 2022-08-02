# GPT Image

Create GUID Partition Table disk images on local disks.  Written in pure Python
`gpt-image` allows GPT disk images to be _built_ on a local filesystem and
exported to a destination device.

This is useful for creating a disk image on SD Cards or embedded devices.

## Quick Start

```python

import gpt_image

# create a new, 16 MB disk, size is in bytes
disk = gpt_image.disk.Disk("disk-image.raw")
disk.create(16 * 1024 * 1024)

# create a 2MB Linux partition named "boot"
boot_part = gpt_image.partition.Partition(
		"boot", 
		2 * 1024 * 1024, 
		gpt_image.partition.Partition.EFI_SYSTEM_PARTITION
	)
disk.table.partitions.add(boot_part)

# create an 8MB Linux partition named "data"
data_part = gpt_image.partition.Partition(
		"data", 
		8 * 1024 * 1024, 
		gpt_image.partition.Partition.LINUX_FILE_SYSTEM
	)
disk.table.partitions.add(data_part)

# commit the change to disk
disk.write()

# dump the current GPT information:

print(disk)
```

The final `print(disk)` command will output a JSON document of the current GPT
configuration:

```json
{
  "path": "disk-image.raw",
  "image_size": 16777216,
  "sector_size": 512,
  "primary_header": {
    "backup": false,
    "signature": "EFI PART",
    "revision": "\u0000\u0000\u0001\u0000",
    "header_size": 92,
    "header_crc32": 3533962731,
    "reserved": 0,
    "my_lba": 1,
    "alternate_lba": 32767,
    "first_usable_lba": 34,
    "last_usable_lba": 32734,
    "disk_guid": "3f09c9fe-66ea-4c67-b0fb-fd35906b393a",
    "partition_entry_lba": 2,
    "number_of_partition_entries": 128,
    "size_of_partition_entries": 128,
    "partition_entry_array_crc32": 673632436
  },
  "backup_header": {
    "backup": true,
    "signature": "EFI PART",
    "revision": "\u0000\u0000\u0001\u0000",
    "header_size": 92,
    "header_crc32": 727034965,
    "reserved": 0,
    "my_lba": 32767,
    "alternate_lba": 1,
    "first_usable_lba": 34,
    "last_usable_lba": 32734,
    "disk_guid": "3f09c9fe-66ea-4c67-b0fb-fd35906b393a",
    "partition_entry_lba": 32735,
    "number_of_partition_entries": 128,
    "size_of_partition_entries": 128,
    "partition_entry_array_crc32": 673632436
  },
  "partitions": [
    {
      "type_guid": "C12A7328-F81F-11D2-BA4B-00A0C93EC93B",
      "partition_name": "boot",
      "partition_guid": "67ed0675-9d44-46a6-bc29-99a2778e7563",
      "first_lba": 40,
      "last_lba": 4135,
      "alignment": 8,
      "size": 2097152,
      "attribute_flags": []
    },
    {
      "type_guid": "0FC63DAF-8483-4772-8E79-3D69D8477DE4",
      "partition_name": "data",
      "partition_guid": "1a44bc84-bb53-4f9f-b699-1d1268bfdbfa",
      "first_lba": 4136,
      "last_lba": 20519,
      "alignment": 8,
      "size": 8388608,
      "attribute_flags": []
    }
  ]
}
```
