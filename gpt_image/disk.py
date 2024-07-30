import json
import os
import pathlib

from gpt_image.geometry import Geometry
from gpt_image.partition import Partition, PartitionEntryArray, PartitionType
from gpt_image.table import Header, Table


class TableReadError(Exception):
    """Error reading partition table"""


class DiskReadError(Exception):
    """Error reading disk image"""


class Disk:
    """GPT disk

    A disk objects represents a new or existing GPT disk image.  If the file exists,
    it is assumed to be an existing GPT image. If it does not, a new file is created.

    Attributes:
        image_path: file image path (absolute or relative)
    """

    def __init__(self, image_path: str, sector_size: int = 512) -> None:
        """Init Disk with a file path

        Args:
            image_path: path a new or existing disk image
            sector_size: disk sector size in bytes (default 512 Bytes)
        """

        self.image_path = pathlib.Path(image_path)
        self.name = self.image_path.name
        self.sector_size = sector_size

    @staticmethod
    def open(image_path: str) -> "Disk":
        """Read existing GPT disk table

        Raises:
            DiskReadError: if disk image cannot be found
            TableReadError if primary and backup tables do not match
        """

        if not os.path.isfile(image_path):
            raise DiskReadError(f"unable to open disk: {image_path}")
        disk = Disk(image_path)
        disk_bytes = disk.image_path.read_bytes()
        disk.size = disk.image_path.stat().st_size
        disk.geometry = Geometry(disk.size, disk.sector_size)
        disk.table = Table(disk.geometry)
        # read the headers
        primary_header_b = disk_bytes[
            disk.geometry.primary_header_byte : disk.geometry.primary_header_byte
            + disk.geometry.header_length
        ]
        backup_header_b = disk_bytes[
            disk.geometry.alternate_header_byte : disk.geometry.alternate_header_byte
            + disk.geometry.header_length
        ]
        disk.table.primary_header = Header.unmarshal(primary_header_b, disk.geometry)
        disk.table.secondary_header = Header.unmarshal(backup_header_b, disk.geometry, is_backup=True)
        # read the partition tables
        primary_part_table_b = disk_bytes[
            disk.geometry.primary_array_byte : disk.geometry.primary_array_byte
            + disk.geometry.array_max_length
        ]
        backup_part_table_b = disk_bytes[
            disk.geometry.alternate_array_byte : disk.geometry.alternate_array_byte
            + disk.geometry.array_max_length
        ]
        if primary_part_table_b != backup_part_table_b:
            raise TableReadError("primary and backup table do not match")
        # unmarshal the partition bytes to objects and add the partition to the entry
        # list if the type_guid is valid
        for i in range(PartitionEntryArray.EntryCount):
            offset = i * PartitionEntryArray.EntryLength
            partition_bytes = primary_part_table_b[
                offset : offset + PartitionEntryArray.EntryLength
            ]
            new_part = Partition.unmarshal(partition_bytes, disk.geometry.sector_size)
            if new_part.type_guid != PartitionType.UNUSED.value:
                disk.table.partitions.entries.append(new_part)
        return disk

    def __repr__(self) -> str:
        # objects will be in the form of JSON strings, convert them to dicts so that we
        # can create a single JSON document
        partition_list = [json.loads(str(p)) for p in self.table.partitions.entries]
        disk_dict = {
            "path": str(self.image_path),
            "image_size": self.size,
            "sector_size": self.sector_size,
            "primary_header": json.loads(str(self.table.primary_header)),
            "backup_header": json.loads(str(self.table.secondary_header)),
            "partitions": partition_list,
        }
        return json.dumps(disk_dict, indent=2, ensure_ascii=False)

    def create(self, size: int) -> None:
        """Create the disk image on Disk

        Creates the basic image structure at the specified path. This zeros the disk
        and writes the protective MBR.

        Args:
            size in bytes
        """

        self.image_path.touch(exist_ok=False)
        self.size = size
        self.geometry = Geometry(self.size, self.sector_size)
        self.table = Table(self.geometry)
        # @TODO: move this into the write method
        with open(self.image_path, "r+b") as f:
            # zero entire disk
            f.write(b"\x00" * self.size)
        self.commit()

    def commit(self) -> None:
        """Commit the GPT information to disk

        Writes the GPT header and partition tables to disk. Actions that happen before
        this are not written to disk.
        """

        # if partitions have been moved or resized,
        # then their data needs to be shifted within the disk
        self.table.partitions.commit(self)
        self.table.update()
        with open(self.image_path, "r+b") as f:
            # write MBR
            f.seek(0)
            f.write(self.table.protective_mbr.marshal())

            # write primary header
            f.seek(self.geometry.primary_header_byte)
            f.write(self.table.primary_header.marshal())

            # write primary partition table
            f.seek(self.geometry.primary_array_byte)
            f.write(self.table.partitions.marshal())

            # move to secondary header location and write
            f.seek(self.geometry.alternate_header_byte)
            f.write(self.table.secondary_header.marshal())

            # write secondary partition table
            f.seek(self.geometry.alternate_array_byte)
            f.write(self.table.partitions.marshal())
