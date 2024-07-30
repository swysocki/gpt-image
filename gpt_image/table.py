"""
Header information reference: https://en.wikipedia.org/wiki/GUID_Partition_Table

"""
import binascii
import json
import struct
import uuid

from gpt_image.geometry import Geometry
from gpt_image.partition import PartitionEntryArray


class HeaderReadError(Exception):
    """Exception from reading existing headers"""


class ProtectiveMBR:
    """Protective MBR Table Entry

    Provides the bare minimum entries needed to represent a protective MBR.
    https://thestarman.pcministry.com/asm/mbr/PartTables.htm#pte

    """

    _MBR_FORMAT = struct.Struct("<446sB3sc3sII48s2s")

    def __init__(
        self,
        geometry: Geometry,
        partition_type: bytes = b"\xEE",
        signature: bytes = b"\x55\xAA",
    ):
        self._geometry = geometry
        self._start_padding = b"\x00"  # padding before boot indicator
        self.boot_indicator = 0  # not bootable
        self.start_chs = b"\x00"  # ignore the start CHS
        self.partition_type = partition_type  # GPT partition type
        self.end_chs = b"\x00"  # ignore the end CHS
        self.start_sector = self._geometry.my_lba
        # size, minus the protective MBR sector. This only works if the
        # disk is under 2 TB
        self.partition_size = int(self._geometry.total_sectors - 1)
        self._end_padding = b"\x00"  # padding before signature
        self.signature = signature

    def marshal(self) -> bytes:
        """Convert Protective MBR to its byte structure"""
        pmbr_bytes = self._MBR_FORMAT.pack(
            self._start_padding,
            self.boot_indicator,
            self.start_chs,
            self.partition_type,
            self.end_chs,
            self.start_sector,
            self.partition_size,
            self._end_padding,
            self.signature,
        )
        return pmbr_bytes

    @staticmethod
    def unmarshal(pmbr_bytes: bytes, geometry: Geometry) -> "ProtectiveMBR":
        (
            _,
            boot_indicator,
            start_chs,
            partition_type,
            end_chs,
            start_sector,
            partition_size,
            _,
            signature,
        ) = ProtectiveMBR._MBR_FORMAT.unpack(pmbr_bytes)

        return ProtectiveMBR(geometry, partition_type, signature)


class Header:
    """GPT Partition Table Header Object

    Each table has two GPT headers, primary and secondary (backup). The primary is
    written to LBA 1 and secondary is written to LBA -1. The GPT Headers contain
    various data including the locations of one another. Therefore two headers
    are created for each table.  The only common component is the disk GUID.

    """

    _HEADER_FORMAT = struct.Struct("<8s4sIIIQQQQ16sQIII")
    _SIGNATURE = b"EFI PART"
    _REVISION = b"\x00\x00\x01\x00"
    _HEADER_SIZE = 92

    def __init__(
        self,
        geometry: Geometry,
        header_crc32: int = 0,
        partition_entry_array_crc32: int = 0,
        guid: str = "",
        is_backup: bool = False,
    ):
        self._geometry = geometry
        self.backup = is_backup
        # header fields
        self.signature = self._SIGNATURE
        self.revision = self._REVISION
        self.header_size = self._HEADER_SIZE
        self.header_crc32 = header_crc32
        self.reserved = 0
        self.my_lba = self._geometry.my_lba
        self.alternate_lba = self._geometry.alternate_lba
        self.first_usable_lba = self._geometry.first_usable_lba
        self.last_usable_lba = self._geometry.last_usable_lba
        self.disk_guid = guid
        # create a GUID if it's a blank string
        if not guid:
            self.disk_guid = str(uuid.uuid4())
        self.partition_entry_lba = self._geometry.partition_entry_lba
        self.number_of_partition_entries = 128
        self.size_of_partition_entries = 128
        self.partition_entry_array_crc32 = partition_entry_array_crc32

        if self.backup:
            self.my_lba, self.alternate_lba = (
                self.alternate_lba,
                self.my_lba,
            )
            self.partition_entry_lba = self._geometry.alternate_array_lba

    def __repr__(self) -> str:
        filtered_values = {k: v for k, v in vars(self).items() if not k.startswith("_")}
        # convert dictionary values that are bytes to strings
        converted_values = {
            k: v.decode() for k, v in filtered_values.items() if isinstance(v, bytes)
        }
        filtered_values.update(converted_values)
        return json.dumps(filtered_values, indent=2, ensure_ascii=False)

    def marshal(self) -> bytes:
        header_bytes = self._HEADER_FORMAT.pack(
            self.signature,
            self.revision,
            self.header_size,
            self.header_crc32,
            self.reserved,
            self.my_lba,
            self.alternate_lba,
            self.first_usable_lba,
            self.last_usable_lba,
            uuid.UUID(self.disk_guid).bytes_le,
            self.partition_entry_lba,
            self.number_of_partition_entries,
            self.size_of_partition_entries,
            self.partition_entry_array_crc32,
        )
        assert len(header_bytes) == self._HEADER_SIZE
        padding = b"\x00" * (self._geometry.sector_size - len(header_bytes))
        return header_bytes + padding

    @staticmethod
    def unmarshal(header_bytes: bytes, geometry: Geometry, is_backup: bool = False) -> "Header":
        (
            signature,
            revision,
            header_size,
            header_crc32,
            reserved,
            my_lba,
            alternate_lba,
            first_usable_lba,
            last_usable_lba,
            disk_guid,
            partition_entry_lba,
            number_of_partitions,
            size_of_partitions,
            partition_entry_crc32,
        ) = Header._HEADER_FORMAT.unpack(header_bytes)

        if signature != Header._SIGNATURE:
            raise HeaderReadError("Invalid GPT header signature")

        if revision != Header._REVISION:
            raise HeaderReadError("Invalid GPT revision")

        if header_size != Header._HEADER_SIZE:
            raise HeaderReadError("Invalid header size")

        if is_backup:
            my_lba, alternate_lba = alternate_lba, my_lba
        geometry.my_lba = my_lba
        geometry.alternate_lba = alternate_lba
        geometry.first_usable_lba = first_usable_lba
        geometry.last_usable_lba = last_usable_lba
        geometry.partition_entry_lba = partition_entry_lba

        disk_guid = str(uuid.UUID(bytes=disk_guid))
        return Header(
            geometry,
            header_crc32,
            partition_entry_crc32,
            disk_guid,
            is_backup=is_backup
        )


class Table:
    """GPT Partition Table Object

    The entire GPT table structure including the protective MBR,
    GPT headers and partition tables
    """

    def __init__(self, geometry: Geometry):
        self._geometry = geometry
        self.protective_mbr: ProtectiveMBR = ProtectiveMBR(self._geometry)
        self.primary_header: Header = Header(self._geometry)
        self.secondary_header: Header = Header(
            self._geometry, guid=self.primary_header.disk_guid, is_backup=True
        )
        self.partitions: PartitionEntryArray = PartitionEntryArray(self._geometry)

    def update(self) -> None:
        # calculate partition checksum and write to header
        self.checksum_partitions(self.primary_header)
        self.checksum_partitions(self.secondary_header)

        # calculate header checksum and write to header
        self.checksum_header(self.primary_header)
        self.checksum_header(self.secondary_header)

    def checksum_partitions(self, header: Header) -> None:
        """Checksum the partition entries

        Args:
            header: initialized GPT header object
        """
        part_entry_bytes = self.partitions.marshal()
        header.partition_entry_array_crc32 = binascii.crc32(part_entry_bytes)

    def checksum_header(self, header: Header) -> None:
        """Checksum the table header

        This CRC includes the partition checksum, and must be calculated
        after that has been written.

        Args:
            header: initialized GPT header object
        """
        # zero the old checksum before calculating
        header.header_crc32 = 0
        # only CRC the header feilds 0x0 - 0x5b
        header.header_crc32 = binascii.crc32(header.marshal()[:92])
