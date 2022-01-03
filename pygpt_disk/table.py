"""
Header information reference: https://en.wikipedia.org/wiki/GUID_Partition_Table

"""
import binascii
import io
import uuid
from dataclasses import dataclass
from typing import Union

from pygpt_disk.disk import Geometry


class Table:
    """GPT Partition Table Object

    Each disk has two partition tables, primary and backup. The
    Table class represents one of the partition tables.

    """

    @dataclass
    class HeaderEntry:
        offset: int
        length: int
        content: Union[int, str, bytes]

    def __init__(
        self, geometry: Geometry, is_backup: bool = False, sector_size: int = 512
    ) -> None:
        self.backup = is_backup
        self.buffer = io.BytesIO()
        self.geometry = geometry
        self._header_sig = Table.HeaderEntry(0, 8, b"EFI PART")
        self._revision = Table.HeaderEntry(8, 4, b"\x00\x00\x01\x00")
        self._header_size = Table.HeaderEntry(12, 4, 92)
        self._header_crc = Table.HeaderEntry(16, 4, 0)
        self._reserved = Table.HeaderEntry(20, 4, 0)
        self._primary_header_lba = Table.HeaderEntry(24, 8, geometry.primary_header_lba)
        self._secondary_header_lba = Table.HeaderEntry(
            32, 8, geometry.backup_header_lba
        )
        if self.backup:
            self._primary_header_lba.offset = 32
            self._secondary_header_lba.offset = 24
        self._partition_start_lba = Table.HeaderEntry(
            40, 8, geometry.partition_start_lba
        )
        self._partition_last_lba = Table.HeaderEntry(48, 8, geometry.partition_last_lba)
        self._disk_guid = Table.HeaderEntry(56, 16, uuid.uuid4().bytes_le)
        self._partition_array_start = Table.HeaderEntry(
            72, 8, geometry.primary_array_lba
        )
        if self.backup:
            self._partition_array_start.content = geometry.backup_header_array_lba
        self._partition_array_length = Table.HeaderEntry(80, 4, 128)
        self._partition_entry_size = Table.HeaderEntry(84, 4, 128)
        self._partition_array_crc = Table.HeaderEntry(88, 4, 0)

        # header start byte relative the table itself, not the disk
        # primary will be 0 backup will be LBA 32
        self.header_start_byte = 0
        self.partition_entry_start_byte = int(1 * sector_size)
        if self.backup:
            self.header_start_byte = int(32 * sector_size)
            self.partition_entry_start_byte = 0

    def _write_table(self) -> None:
        # start with blank table
        self.buffer.write(b"\x00" * 33 * self.geometry.sector_size)

    def _write_header(self) -> None:
        """Write the table header to proper location

        The header is typically 92 bytes with the remainder of bytes in the sector
        zeroed. The primary header is at LBA 1 with the partition entries at 2 - 33.
        The backup header is at LBA -1 with the partition entries at -2 to -33.

        """
        self._write_section(self._header_sig)
        self._write_section(self._revision)
        self._write_section(self._header_size)
        self._write_section(self._header_crc)
        self._write_section(self._reserved)
        self._write_section(self._primary_header_lba)
        self._write_section(self._secondary_header_lba)
        self._write_section(self._partition_start_lba)
        self._write_section(self._partition_last_lba)
        self._write_section(self._disk_guid)
        self._write_section(self._partition_array_start)
        self._write_section(self._partition_array_length)
        self._write_section(self._partition_entry_size)
        self._write_section(self._partition_array_crc)

        # @TODO: write partition entries

        # once the partitions are written the CRC is calculated
        self._checksum_partitions()

        # once the header is written the CRC is calculated
        self._checksum_header()

    def _write_section(self, entry: HeaderEntry) -> None:
        """Write a GPT header entry

        Args:
            entry: HeaderEntry object
        """
        # seek to section's offset
        self.buffer.seek(self.header_start_byte + entry.offset)
        if type(entry.content) != bytes:
            self.buffer.write((entry.content).to_bytes(entry.length, "little"))
        else:
            self.buffer.write(entry.content)

    def _checksum_header(self) -> None:
        """Calculate the header checksum

        This CRC includes the partition checksum, and must be calculated
        after that has been written.
        """
        # zero field before calculating
        self._header_crc.content = 0
        self._write_section(self._header_crc)
        # read header
        self.buffer.seek(self.header_start_byte)
        raw_header = self.buffer.read(self._header_size.content)
        self._header_crc.content = binascii.crc32(raw_header)
        self._write_section(self._header_crc)

    def _checksum_partitions(self) -> None:
        """Write the partition checksum

        Move to the start of the partition entries.  Read the partition
        entry array length * the partition entry size.  CRC that value.
        """
        # read partitions entries relative to the table
        self.buffer.seek(self.partition_entry_start_byte)
        if self.backup:
            self.buffer.seek(self.partition_entry_start_byte)

        raw_partitions = self.buffer.read(
            self._partition_array_length.content * self._partition_entry_size.content
        )
        self._partition_array_crc.content = binascii.crc32(raw_partitions)
        self._write_section(self._partition_array_crc)
