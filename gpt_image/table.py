"""
Header information reference: https://en.wikipedia.org/wiki/GUID_Partition_Table

"""
import binascii
import uuid

from gpt_image.entry import Entry
from gpt_image.geometry import Geometry
from gpt_image.partition import PartitionEntryArray


class ProtectiveMBR:
    """Protective MBR Table Entry

    Provides the bare minimum entries needed to represent a protective MBR.
    https://thestarman.pcministry.com/asm/mbr/PartTables.htm#pte

    """

    def __init__(self, geometry: Geometry):
        self._start_padding = Entry(0, 446, 0)  # padding before boot indicator
        self.boot_indicator = Entry(446, 1, 0)  # not bootable
        self.start_chs = Entry(447, 3, 0)  # ignore the start CHS
        self.partition_type = Entry(450, 1, b"\xEE")  # GPT partition type
        self.end_chs = Entry(451, 3, 0)  # ignore the end CHS
        self.start_sector = Entry(454, 4, geometry.my_lba)
        # size, minus the protective MBR sector. This only works if the
        # disk is under 2 TB
        self.partition_size = Entry(458, 4, geometry.total_sectors - 1)
        self._end_padding = Entry(462, 48, 0)  # padding before signature
        self.signature = Entry(510, 2, b"\x55\xAA")

    @property
    def byte_structure(self) -> bytes:
        """Convert Protective MBR to its byte structure"""
        pmbr_fields = [
            self._start_padding,
            self.boot_indicator,
            self.start_chs,
            self.partition_type,
            self.end_chs,
            self.start_sector,
            self.partition_size,
            self._end_padding,
            self.signature,
        ]
        byte_list = [x.data_bytes for x in pmbr_fields]
        return b"".join(byte_list)

    def read(self, pmbr_data: bytes):
        self.boot_indicator.data = pmbr_data[
            self.boot_indicator.offset : self.boot_indicator.end
        ]
        self.start_chs.data = pmbr_data[self.start_chs.offset : self.start_chs.end]
        self.partition_type.data = pmbr_data[
            self.partition_type.offset : self.partition_type.end
        ]
        self.end_chs.data = pmbr_data[self.end_chs.offset : self.end_chs.end]
        self.start_sector.data = pmbr_data[
            self.start_sector.offset : self.start_sector.end
        ]
        self.partition_size.data = pmbr_data[
            self.partition_size.offset : self.partition_size.end
        ]
        self.signature.data = pmbr_data[self.signature.offset : self.signature.end]


class Header:
    """GPT Partition Table Header Object

    Each table has two GPT headers, primary and secondary (backup). The primary is
    written to LBA 1 and secondary is written to LBA -1. The GPT Headers contain
    various data including the locations of one another. Therefore two headers
    are created for each table.  The only common component is the disk GUID.

    """

    def __init__(
        self,
        geometry: Geometry,
        guid: uuid.UUID = uuid.uuid4(),
        is_backup: bool = False,
    ):
        self.geometry = geometry
        self.guid = guid
        self.backup = is_backup

        # all header values start with just offset and length, data is 0
        self.signature = Entry(0, 8, b"EFI PART")

        self.revision = Entry(8, 4, b"\x00\x00\x01\x00")

        self.header_size = Entry(12, 4, 92)
        self.header_crc32 = Entry(16, 4, 0)
        self.reserved = Entry(20, 4, 0)
        self.my_lba = Entry(24, 8, self.geometry.my_lba)

        self.alternate_lba = Entry(32, 8, self.geometry.alternate_lba)
        self.first_usable_lba = Entry(40, 8, self.geometry.first_usable_lba)

        self.last_usable_lba = Entry(48, 8, self.geometry.last_usable_lba)
        self.disk_guid = Entry(56, 16, self.guid.bytes_le)
        self.partition_entry_lba = Entry(72, 8, self.geometry.partition_entry_lba)
        self.number_of_partition_entries = Entry(80, 4, 128)
        self.size_of_partition_entries = Entry(84, 4, 128)
        self.partition_entry_array_crc32 = Entry(88, 4, 0)
        self.reserved_padding = Entry(92, 420, 0)

        if self.backup:
            self.my_lba.data, self.alternate_lba.data = (
                self.alternate_lba.data,
                self.my_lba.data,
            )
            self.partition_entry_lba.data = (
                self.geometry.alternate_array_lba
            ).to_bytes(8, "little")

        # header start byte relative to the table itself, not the disk
        # primary will be 0 secondary will be LBA 32
        self.header_start_byte = 0
        self.partition_entry_start_byte = int(1 * self.geometry.sector_size)
        if self.backup:
            self.header_start_byte = int(32 * self.geometry.sector_size)
            self.partition_entry_start_byte = 0

    @property
    def byte_structure(self) -> bytes:
        """Convert the Header object to its byte structure"""
        header_fields = [
            self.signature,
            self.revision,
            self.header_size,
            self.header_crc32,
            self.reserved,
            self.my_lba,
            self.alternate_lba,
            self.first_usable_lba,
            self.last_usable_lba,
            self.disk_guid,
            self.partition_entry_lba,
            self.number_of_partition_entries,
            self.size_of_partition_entries,
            self.partition_entry_array_crc32,
        ]
        byte_list = [x.data_bytes for x in header_fields]
        return b"".join(byte_list)

    def read(self, header_bytes: bytes) -> None:
        """Unmarshal bytes to Header object"""

        def _to_int(field: Entry):
            return int.from_bytes(header_bytes[field.offset : field.end], "little")

        self.signature.data = header_bytes[
            self.signature.offset : self.signature.offset + self.signature.length
        ]
        self.revision.data = header_bytes[
            self.revision.offset : self.revision.offset + self.revision.length
        ]
        self.header_size.data = _to_int(self.header_size)
        self.header_crc32.data = _to_int(self.header_crc32)
        self.reserved.data = _to_int(self.reserved)
        self.my_lba.data = _to_int(self.my_lba)
        self.alternate_lba.data = _to_int(self.alternate_lba)
        self.first_usable_lba.data = _to_int(self.first_usable_lba)
        self.last_usable_lba.data = _to_int(self.last_usable_lba)
        # stored as little endian bytes. This will need to be converted to display in
        # human readable form
        # uuid.UUID(bytes=self.disk_guid.data)
        self.disk_guid.data = header_bytes[
            self.disk_guid.offset : self.disk_guid.offset + self.disk_guid.length
        ]
        self.partition_entry_lba.data = _to_int(self.partition_entry_lba)
        self.number_of_partition_entries.data = _to_int(
            self.number_of_partition_entries
        )
        self.size_of_partition_entries.data = _to_int(self.size_of_partition_entries)
        self.partition_entry_array_crc32.data = _to_int(
            self.partition_entry_array_crc32
        )


class Table:
    """GPT Partition Table Object

    The entire GPT table structure including the protective MBR,
    GPT headers and partition tables
    """

    def __init__(self, geometry: Geometry):
        self.geometry = geometry
        self.protective_mbr = ProtectiveMBR(self.geometry)
        self.primary_header = Header(self.geometry)
        self.secondary_header = Header(self.geometry, is_backup=True)
        self.partitions = PartitionEntryArray(self.geometry)

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
        part_entry_bytes = self.partitions.byte_structure
        header.partition_entry_array_crc32.data = binascii.crc32(part_entry_bytes)

    def checksum_header(self, header: Header) -> None:
        """Checksum the table header

        This CRC includes the partition checksum, and must be calculated
        after that has been written.

        Args:
            header: initialized GPT header object
        """
        # zero the old checksum before calculating
        header.header_crc32.data = 0
        header.header_crc32.data = binascii.crc32(header.byte_structure)
