"""
LBA 0 is the protective MBR

LBA 1 is where the header starts

Byte 0 - 7 (Signature) "EFI PART" or 45h 46h 49h 20h 50h 41h 52h
Byte 8 - 11 (Revision) "1.0" or 00h 00h 01h 00h
Byte 12 - 15 (Header size LE) 5Ch 00h 00h 00h (92 bytes)
Byte 16 - 19 CRC32 of header from 0 to 15
Byte 20 - 23 reserved (must be zero)
Byte 24 - 31 Current LBA location
Byte 32 - 39 Backup LBA location

LBA 2 - 33 partition entries
"""
from pygpt_disk.disk import Disk
from typing import Union
from dataclasses import dataclass
import uuid


class Table:
    """GPT Partition Table Object"""

    @dataclass
    class HeaderEntry:
        offset: int
        length: int
        content: Union[int, str]

    def __init__(self, disk: Disk) -> None:
        self.disk = disk

        # header fields
        self._header_sig = Table.HeaderEntry(0, 8, b"EFI PART")
        self._revision = Table.HeaderEntry(8, 4, b"\x00\x00\x01\x00")
        self._header_size = Table.HeaderEntry(12, 4, 92)
        self._header_crc = Table.HeaderEntry(16, 4, 0)
        self._reserved = Table.HeaderEntry(20, 4, 0)
        self._primary_header_lba = Table.HeaderEntry(24, 8, 1)
        self._secondary_header_lba = Table.HeaderEntry(
            32, 8, int(self.disk.sectors - 1)
        )
        self._partition_start_lba = Table.HeaderEntry(40, 8, 34)
        self._partition_last_lba = Table.HeaderEntry(48, 8, int(self.disk.sectors - 34))
        self._disk_guid = Table.HeaderEntry(56, 16, uuid.uuid4().bytes_le)

    def write(self) -> None:
        """Write the GPT Table

        Write the GPT table to both the primary and backup
        locations

        """
        self._write_header("primary")
        self._write_header("backup")
        # move to the end of the buffer and write to avoid truncating the stream
        self.disk.buffer.seek(self.disk.size - 1)
        self.disk.buffer.write(b"\0")

    def _write_header(self, header: str = "primary") -> None:
        """Write the table header to proper location"""
        header_locations = ["primary", "backup"]
        if header not in header_locations:
            raise ValueError(f"Invalid header location {header}")
        if header == "primary":
            start_byte = 1 * self.disk.sector_size  # LBA 1
        if header == "backup":
            start_byte = self._secondary_header_lba * self.disk.sector_size  # LBA -1
            # the primary/backup header locations are swapped when writing
            # to the backup header
            self._primary_header_lba.offset = 32
            self._secondary_header_lba.offset = 24

        self._write_section(self._header_sig, start_byte)
        self._write_section(self._revision, start_byte)
        self._write_section(self._header_size, start_byte)
        self._write_section(self._header_crc, start_byte)
        self._write_section(self._reserved, start_byte)
        self._write_section(self._primary_header_lba, start_byte)
        self._write_section(self._secondary_header_lba, start_byte)
        self._write_section(self._partition_start_lba, start_byte)
        self._write_section(self._partition_last_lba, start_byte)
        self._write_section(self._disk_guid, start_byte)

    def _write_section(self, entry: HeaderEntry, buffer_position: int):
        # seek to section's offset
        self.disk.buffer.seek(buffer_position + entry.offset)
        if type(entry.content) != bytes:
            self.disk.buffer.write((entry.content).to_bytes(entry.length, "little"))
        else:
            self.disk.buffer.write(entry.content)
