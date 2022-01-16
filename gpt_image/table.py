"""
Header information reference: https://en.wikipedia.org/wiki/GUID_Partition_Table

"""
import binascii
import uuid
from dataclasses import dataclass
from typing import List, Tuple

from gpt_image.disk import Disk, Geometry


@dataclass
class TableEntry:
    """Individual table entries

    Creates a consistent structure for writing GPT table data to its
    respective locations.  This is used for headers and partitions.

    The data field only accepts bytes to simplify writing back to a buffer.
    """

    offset: int
    length: int
    data: bytes
    # @TODO: make default data b"\x00" * length


class Header:
    """GPT Partition Table Header Object

    Each table has two GPT headers, primary and secondary (backup). The primary is
    written to LBA 1 and secondary is written to LBA -1. The GPT Headers contain
    various data including the locations of one another. Therefore two headers
    are created for each table.

    """

    def __init__(self, geometry: Geometry, is_backup: bool = False):
        self.backup = is_backup
        self.geometry = geometry
        self.header_sig = TableEntry(0, 8, b"EFI PART")
        self.revision = TableEntry(8, 4, b"\x00\x00\x01\x00")
        self.header_size = TableEntry(12, 4, (92).to_bytes(4, "little"))
        self.header_crc = TableEntry(16, 4, (0).to_bytes(4, "little"))
        self.reserved = TableEntry(20, 4, (0).to_bytes(4, "little"))
        self.primary_header_lba = TableEntry(
            24, 8, (self.geometry.primary_header_lba).to_bytes(8, "little")
        )
        self.secondary_header_lba = TableEntry(
            32, 8, (self.geometry.backup_header_lba).to_bytes(8, "little")
        )
        self.partition_start_lba = TableEntry(
            40, 8, (self.geometry.partition_start_lba).to_bytes(8, "little")
        )
        self.partition_last_lba = TableEntry(
            48, 8, (self.geometry.partition_last_lba).to_bytes(8, "little")
        )
        self.disk_guid = TableEntry(56, 16, uuid.uuid4().bytes_le)
        self.partition_array_start = TableEntry(
            72, 8, (self.geometry.primary_array_lba).to_bytes(8, "little")
        )
        self.partition_array_length = TableEntry(80, 4, (128).to_bytes(4, "little"))
        self.partition_entry_size = TableEntry(84, 4, (128).to_bytes(4, "little"))
        self.partition_array_crc = TableEntry(88, 4, (0).to_bytes(4, "little"))
        self.reserved_padding = TableEntry(92, 420, b"\x00" * 420)
        # the secondary header adjustments
        if self.backup:
            self.primary_header_lba.offset = 32
            self.secondary_header_lba.offset = 24
            self.partition_array_start.data = (
                self.geometry.backup_header_array_lba
            ).to_bytes(8, "little")

        # header start byte relative the table itself, not the disk
        # primary will be 0 secondary will be LBA 32
        self.header_start_byte = 0
        self.partition_entry_start_byte = int(1 * self.geometry.sector_size)
        if self.backup:
            self.header_start_byte = int(32 * self.geometry.sector_size)
            self.partition_entry_start_byte = 0

        # group the header fields to allow byte operations such as
        # checksum
        # this can be done with the `inspect` module
        self.header_fields = [
            self.header_sig,
            self.revision,
            self.header_size,
            self.header_crc,
            self.reserved,
            self.primary_header_lba,
            self.secondary_header_lba,
            self.partition_start_lba,
            self.partition_last_lba,
            self.disk_guid,
            self.partition_array_start,
            self.partition_array_length,
            self.partition_entry_size,
            self.partition_array_crc,
            self.reserved_padding,
        ]

    def as_bytes(self) -> bytes:
        """Return the header as bytes"""
        byte_list = [x.data for x in self.header_fields]
        return b"".join(byte_list)


class Partition:
    @dataclass
    class Type:
        """GPT Partition Types

        https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_entries
        """

        LinuxFileSystem = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"
        EFISystemPartition = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"

    def __init__(
        self,
        partition_list: List,
        name: str,
        size: int,
        partition_guid: uuid.UUID,
        alignment: int,
        disk_geometry: Geometry,
    ):
        """
        # @TODO: add 64 bits of partition attributes
        """
        self.type_guid = TableEntry(
            0, 16, uuid.UUID(Partition.Type.LinuxFileSystem).bytes_le
        )
        if not partition_guid:
            self.partition_guid = TableEntry(16, 16, uuid.uuid4().bytes_le)
        self.alignment = alignment
        self._partition_list = partition_list
        self._partition_size = size
        self._sector_size = disk_geometry.sector_size
        self._start_lba = disk_geometry.partition_start_lba

        start, end = self._get_partition_lba()
        self.first_lba = TableEntry(32, 8, start.to_bytes(8, "little"))
        self.last_lba = TableEntry(40, 8, end.to_bytes(8, "little"))

        self.attribute_flags = TableEntry(48, 8, b"\x00" * 8)
        self.partition_name = TableEntry(56, 72, bytes(name, encoding="utf_16_le"))

        self.partition_fields = [
            self.type_guid,
            self.partition_guid,
            self.first_lba,
            self.last_lba,
            self.attribute_flags,
            self.partition_name,
        ]

    def _get_partition_lba(self) -> tuple:
        """Calculate the partition's LBAs"""
        last_partition = self._start_lba.to_bytes(4, "little")
        if self._partition_list:
            last_partition = self.partition_list[-1].last_lba.data
        first_lba = int.from_bytes(last_partition, "little") + 1
        # calculate partition size in LBA with alignment considered
        total_lba = int(self._partition_size / (self._sector_size * self.alignment) + 1)
        return first_lba, first_lba + total_lba

    def as_bytes(self) -> bytes:
        """Return the partition as bytes"""
        byte_list = [x.data for x in self.partition_fields]
        return b"".join(byte_list)


class Table:
    """GPT Partition Table Object

    A table contains a primary and secondary header and a primary
    and secondary partition entry table.  All management of their entries
    is done with this object.
    """

    def __init__(self, disk: Disk, sector_size: int = 512) -> None:
        self.disk = disk
        self.geometry = disk.geometry
        self.primary_header = Header(self.geometry)
        self.secondary_header = Header(self.geometry, is_backup=True)
        # partition entry array
        self.partition_entries = []

    def write(self):
        """Write the table to disk"""
        # calculate partition checksum and write to header
        self.checksum_partitions(self.primary_header)
        self.checksum_partitions(self.secondary_header)

        # calculate header checksum and write to header
        self.checksum_header(self.primary_header)
        self.checksum_header(self.secondary_header)

        with open(self.disk.image_path, "r+b") as f:
            # move to primary header location and write
            f.seek(self.geometry.primary_header_byte)
            f.write(self.primary_header.as_bytes())
            f.seek(self.geometry.primary_array_byte)
            f.write(b"".join(self.partition_entries))
            # move to secondary header location and write
            f.seek(self.geometry.backup_header_byte)
            f.write(self.secondary_header.as_bytes())

    def create_partition(self, name: str, size: int, guid: str, alignment: int = 8):
        part = Partition(
            self.partition_entries,
            name,
            size,
            guid,
            alignment,
            self.geometry,
        )
        self.partition_entries.append(part.as_bytes())

    def checksum_partitions(self, header: Header):
        """Checksum the partition entries"""

        part_entry_bytes = b"".join(self.partition_entries)
        header.partition_array_crc.data = binascii.crc32(part_entry_bytes).to_bytes(
            4, "little"
        )

    def checksum_header(self, header: Header):
        """Checksum the table header

        This CRC includes the partition checksum, and must be calculated
        after that has been written.
        """
        # zero the old checksum before calculating
        header.header_crc.data = b"\x00" * 4

        header.header_crc.data = binascii.crc32(header.as_bytes()).to_bytes(4, "little")
