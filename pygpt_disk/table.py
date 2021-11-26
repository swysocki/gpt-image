"""
Header information reference: https://en.wikipedia.org/wiki/GUID_Partition_Table

"""
import binascii
import uuid
from dataclasses import dataclass
from typing import Union

from pygpt_disk.disk import Disk


class Table:
    """GPT Partition Table Object"""

    @dataclass
    class HeaderEntry:
        offset: int
        length: int
        content: Union[int, str, bytes]

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
        self._partition_array_length = Table.HeaderEntry(80, 4, 128)
        self._partition_entry_size = Table.HeaderEntry(84, 4, 128)
        self._partition_array_crc = Table.HeaderEntry(88, 4, 0)

        self.primary_header_start_byte = 1 * self.disk.sector_size  # LBA 1
        self.backup_header_start_byte = int(
            self._secondary_header_lba.content * self.disk.sector_size
        )  # LBA -1

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
        start_byte = self.primary_header_start_byte
        # override offset if header is backup
        if header == "backup":
            start_byte = self.backup_header_start_byte
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

        # once the header is written the CRC is calculated
        self._checksum_header(start_byte)

    def _write_section(self, entry: HeaderEntry, buffer_position: int):
        """Write a GPT header entry

        Args:
            entry: HeaderEntry object
            buffer_position: the byte offset of where the entry should be written
        """
        # seek to section's offset
        self.disk.buffer.seek(buffer_position + entry.offset)
        if type(entry.content) != bytes:
            self.disk.buffer.write((entry.content).to_bytes(entry.length, "little"))
        else:
            self.disk.buffer.write(entry.content)

    def _checksum_header(self, offset: int):
        """Calculate the header checksum

        Args:
            offset: start byte of the header we are writing (primary or backup)
        """
        # zero field before calculating
        self._header_crc.content = 0
        self._write_section(self._header_crc, offset)
        # read header
        self.disk.buffer.seek(offset)
        raw_header = self.disk.buffer.read(self._header_size.content)
        self._header_crc.content = binascii.crc32(raw_header)
        self._write_section(self._header_crc, offset)


if __name__ == "__main__":
    disk = Disk(8 * 1024 * 1024, "/tmp/testgpt.img")
    t = Table(disk)
    t.write()
    disk.write()
