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

LBA 2 - 33 partitions
"""
from pygpt_disk.disk import Disk
import struct


class Table:
    _header_sig = b"\x45\x46\x49\x20\x50\x41\x52\x54"  # "EFI PART"
    _revision = b"\x00\x00\x01\x00"  # "1.0"
    _header_size = b"\x5C\x00\x00\x00"  # 92 bytes
    _header_crc = (
        b"\x00\x00\x00\x00"  # CRC/zlib of header with this field zero'd during calc
    )
    _reserved = b"\x00\x00\x00\x00"  # reserved (all zeros)

    def __init__(self, disk: Disk) -> None:
        self.disk = disk
        self._primary_header_lba = int(self.disk.sector_size / self.disk.sector_size)
        self._backup_header_lba = int(
            (self.disk.size - self.disk.sector_size) / self.disk.sector_size
        )

    def create(self) -> None:
        """Create blank GPT Table Header"""
        # move to LBA 1
        self.disk.buffer.seek(self.disk.sector_size)
        self.disk.buffer.write(Table._header_sig)
        self.disk.buffer.write(Table._revision)
        self.disk.buffer.write(Table._header_size)
        self.disk.buffer.write(Table._header_crc)
        self.disk.buffer.write(Table._reserved)
        # use struct.pack with implicit native byte order and long type to
        # align data on 8 byte boundaries
        self.disk.buffer.write(struct.pack("l", self._primary_header_lba))
        self.disk.buffer.write(struct.pack("l", self._backup_header_lba))
        self.disk.buffer.seek(self.disk.size - 1)
        # move to the end of the buffer and write to avoid truncating the stream
        self.disk.buffer.write(b"\0")

    def checksum_header(self) -> None:
        pass
