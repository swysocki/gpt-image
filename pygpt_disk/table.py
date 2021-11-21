"""
Header information reference: https://en.wikipedia.org/wiki/GUID_Partition_Table

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
        self._partition_array_start = Table.HeaderEntry(72, 8, 2)
        self._partition_array_length = Table.HeaderEntry(80, 4, 0)
        self._partition_entry_size = Table.HeaderEntry(84, 4, 128)
        self._partition_array_crc = Table.HeaderEntry(88, 4, 0)

    def write(self) -> None:
        """Write the GPT Table

        Write the GPT table to both the primary and backup
        locations

        """
        self._write_header("primary")
        self._write_header("backup")
        # Remainder of the header sector is zeroed
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
            start_byte = (
                self._secondary_header_lba.content * self.disk.sector_size
            )  # LBA -1
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
        self._write_section(self._partition_array_start, start_byte)
        self._write_section(self._partition_array_length, start_byte)
        self._write_section(self._partition_entry_size, start_byte)
        self._write_section(self._partition_array_crc, start_byte)

    def _write_section(self, entry: HeaderEntry, buffer_position: int):
        # seek to section's offset
        self.disk.buffer.seek(buffer_position + entry.offset)
        if type(entry.content) != bytes:
            self.disk.buffer.write((entry.content).to_bytes(entry.length, "little"))
        else:
            self.disk.buffer.write(entry.content)

    def checksum_header():
        pass

    def update_header():
        pass
