import pathlib

from gpt_image.geometry import Geometry
from gpt_image.partition import Partition, PartitionEntryArray
from gpt_image.table import Header, Table


class TableReadError(Exception):
    pass


class Disk:
    """GPT disk

    A disk objects represents a new or existing GPT disk image.  If the file exists,
    it is assumed to be an existing GPT image. If it does not, a new file is created.

    Attributes:
        image_path: file image path (absolute or relative)
    """

    def __init__(self, image_path: str) -> None:
        """Init Disk with a file path"""
        self.image_path = pathlib.Path(image_path)
        self.name = self.image_path.name
        self.sector_size = 512  # 512 bytes

    def open(self):
        """Read existing GPT disk Table"""
        disk_bytes = self.image_path.read_bytes()
        self.size = self.image_path.stat().st_size
        self.geometry = Geometry(self.size, self.sector_size)
        self.table = Table(self.geometry)
        # read the headers
        primary_header_b = disk_bytes[
            self.geometry.primary_header_byte : self.geometry.primary_header_byte
            + self.geometry.header_length
        ]
        backup_header_b = disk_bytes[
            self.geometry.backup_header_byte : self.geometry.backup_header_byte
            + self.geometry.header_length
        ]
        self.table.primary_header = Header(self.geometry)
        self.table.primary_header.read(primary_header_b)
        self.table.secondary_header = Header(self.geometry, is_backup=True)
        self.table.secondary_header.read(backup_header_b)
        # read the partition tables
        primary_part_table_b = disk_bytes[
            self.geometry.primary_array_byte : self.geometry.primary_array_byte
            + self.geometry.array_length
        ]
        backup_part_table_b = disk_bytes[
            self.geometry.backup_array_byte : self.geometry.backup_array_byte
            + self.geometry.array_length
        ]
        if primary_part_table_b != backup_part_table_b:
            raise TableReadError("primary and backup table do not match")
        # unmarshal the partition bytes to objects
        # loop through the entire array and unmarshall the bytes if partition
        # data is found
        for i in range(PartitionEntryArray.EntryCount):
            offset = i * PartitionEntryArray.EntryLength
            partition_bytes = primary_part_table_b[
                offset : offset + PartitionEntryArray.EntryLength
            ]
            new_part = Partition()
            new_part.read(partition_bytes)
            if new_part.type_guid.data != b"\x00" * 16:
                self.table.partitions.entries.append(new_part)

    def create(self, size: int):
        """Create the disk image on Disk

        Creates the basic image structure at the specified path. This zeros
        the disk and writes the protective MBR.

        """
        self.image_path.touch(exist_ok=False)
        self.size = size
        self.geometry = Geometry(self.size, self.sector_size)
        self.table = Table(self.geometry)
        # @TODO: move this into the write method
        with open(self.image_path, "r+b") as f:
            # zero entire disk
            f.write(b"\x00" * self.size)
            f.seek(0)
            f.write(self.table.protective_mbr.as_bytes())
        self.write()

    def write(self):
        """Write the GPT information to disk

        Writes the GPT header and partition tables to disk. Actions that
        happen before this are not written to disk.

        """
        self.table.update()
        with open(self.image_path, "r+b") as f:
            # write primary header
            f.seek(self.geometry.primary_header_byte)
            f.write(self.table.primary_header.as_bytes())

            # write primary partition table
            f.seek(self.geometry.primary_array_byte)
            f.write(self.table.partitions.as_bytes())

            # move to secondary header location and write
            f.seek(self.geometry.backup_header_byte)
            f.write(self.table.secondary_header.as_bytes())

            # write secondary partition table
            f.seek(self.geometry.backup_array_byte)
            f.write(self.table.partitions.as_bytes())

    def write_data(self, data: bytes, partition: Partition, offset: int = 0) -> None:
        # @NOTE: this isn't a GPT function. Writing data should be outside the
        # scope of this module
        """Write data to disk

        Args:
            data: data to write to partition. only bytes supported
            partition: Partition object to write data to
            offset: byte offset for writing data. The default is 0 but can be set to
                support custom offsets
        """
        if not type(data) is bytes:
            raise ValueError(f"data must be of type bytes. found type: {type(data)}")

        with open(self.image_path, "r+b") as f:
            start_lba = int.from_bytes(partition.first_lba.data_bytes, "little")
            start_byte = int(start_lba * self.sector_size)
            with open(self.image_path, "r+b") as f:
                f.seek(start_byte + offset)
                f.write(data)
