from __future__ import annotations

import json
import shutil
import struct
import tempfile
import uuid
from enum import Enum, IntEnum
from math import ceil
from typing import List, Optional, Any, IO
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # a bit of a hack to allow typing to work
    from gpt_image.disk import Disk

from gpt_image.geometry import Geometry


class PartitionEntryError(Exception):
    """Exception class for errors in partition entries"""


class PartitionAttribute(IntEnum):
    """Supported partition attribute settings

    https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_entries_(LBA_2-33)


    The attribute field is 8 bytes with the last 2 bytes used for basic data. This
    field sets a bit in the last 2 bytes.
    """

    NONE = 0
    READ_ONLY = 60
    SHADOW_COPY = 61
    HIDDEN = 62
    NO_DRIVE_LETTER = 63


class PartitionType(Enum):
    # https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_entries

    UNUSED = "00000000-0000-0000-0000-000000000000"
    # Common Linux
    LINUX_FILE_SYSTEM = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"
    EFI_SYSTEM_PARTITION = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
    RAID_PARTITION = "A19D880F-05FC-4D3B-A006-743F0F84911E"
    ROOT_PARTITION_X86 = "44479540-F297-41B2-9AF7-D131D5F0458A"
    ROOT_PARTITION_X86_64 = "4F68BCE3-E8CD-4DB1-96E7-FBCAF984B709"
    ROOT_PARTITION_ARM = "69DAD710-2CE4-4E3C-B16C-21A1D49ABED3"
    ROOT_PARTITION_ARM_64 = "B921B045-1DF0-41C3-AF44-4C6F280D3FAE"
    BOOT_PARTITION = "BC13C2FF-59E6-4262-A352-B275FD6F7172"
    SWAP_PARTITION = "0657FD6D-A4AB-43C4-84E5-0933C84B4F4F"
    LOGICAL_VOLUME_MANAGER_PARTITION = "E6D6D379-F507-44C2-A23C-238F2A3DF928"
    HOME_PARTITION = "933AC7E1-2EB4-4F13-B844-0E14E2AEF915"
    SRV_SERVER_DATA_PARTITION = "3B8F8425-20E0-4F3B-907F-1A25A76F98E8"
    PLAIN_DMCRYPT_PARTITION = "7FFEC5C9-2D00-49B7-8941-3EA10A5586B7"
    LUKS_PARTITION = "CA7D7CCB-63ED-4C53-861C-1742536059CC"

    # Common Mac
    HIERARCHICAL_FILE_SYSTEM_PLUS_PARTITION = "48465300-0000-11AA-AA11-00306543ECAC"
    APPLE_APFS_CONTAINER = "7C3457EF-0000-11AA-AA11-00306543ECAC"
    APFS_FILEVAULT_VOLUME_CONTAINER = "7C3457EF-0000-11AA-AA11-00306543ECAC"
    APPLE_UFS_CONTAINER = "55465300-0000-11AA-AA11-00306543ECAC"
    ZFS = "6A898CC3-1DD2-11B2-99A6-080020736631"
    APPLE_RAID_PARTITION = "52414944-0000-11AA-AA11-00306543ECAC"
    APPLE_RAID_PARTITION_OFFLINE = "52414944-5F4F-11AA-AA11-00306543ECAC"
    APPLE_BOOT_PARTITION_RECOVERY_HD = "426F6F74-0000-11AA-AA11-00306543ECAC"
    APPLE_LABEL = "4C616265-6C00-11AA-AA11-00306543ECAC"
    APPLE_TV_RECOVERY_PARTITION = "5265636F-7665-11AA-AA11-00306543ECAC"
    APPLE_CORE_STORAGE_CONTAINER = "53746F72-6167-11AA-AA11-00306543ECAC"
    HFS_FILEVAULT_VOLUME_CONTAINER = "53746F72-6167-11AA-AA11-00306543ECAC"
    APPLE_APFS_PREBOOT_PARTITION = "69646961-6700-11AA-AA11-00306543ECAC"
    APPLE_APFS_RECOVERY_PARTITION = "52637672-7900-11AA-AA11-00306543ECAC"

    # Common Windows
    MICROSOFT_RESERVED_PARTITION = "E3C9E316-0B5C-4DB8-817D-F92DF00215AE"
    BASIC_DATA_PARTITION = "EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"
    LOGICAL_DISK_MANAGER_METADATA_PARTITION = "5808C8AA-7E8F-42E0-85D2-E1E90434CFB3"
    LOGICAL_DISK_MANAGER_DATA_PARTITION = "AF9B60A0-1431-4F62-BC68-3311714A69AD"
    WINDOWS_RECOVERY_ENVIRONMENT = "DE94BBA4-06D1-4D40-A16A-BFD50179D6AC"
    IBM_GENERAL_PARALLEL_FILE_SYSTEM_PARTITION = "37AFFC90-EF7D-4E96-91C3-2D7AE055B174"
    STORAGE_SPACES_PARTITION = "E75CAF8F-F680-4CEE-AFA3-B001E56EFC2D"
    STORAGE_REPLICA_PARTITION = "558D43C5-A1AC-43C0-AAC8-D1472B2923D1"


class StagedAttribute:

    def __init__(self, value: Any):
        self._staged = value
        self._value = value

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._staged = value

    @property
    def staged_value(self) -> Any:
        return self._staged

    def needs_commit(self) -> bool:
        if self._value == self._staged:
            return False
        return True

    def commit(self) -> None:
        self._value = self._staged


class Partition:
    """Partition class represents a GPT partition

    Start and end LBA are set to None because they must be calculated from a table's
    partition list.

    Attibutes:
        name: string partition name
        size: integer size of partition in bytes
        type_guid: string UUID partition type
        partition_guid: string UUID partition GUID
        attribute_flags: PartitionAttribute or int of attribute flag bit to set
            automatically generated
        first_lba: integer LBA of partition start, automatically calculated
        last_lba: integer LBA of partition end, automatically calculated
        alignment: integer partition block alignment
    """

    _PARTITION_FORMAT = struct.Struct("<16s16sQQQ72s")

    def __init__(
        self,
        name: str,
        size: int,
        type_guid: str,
        partition_guid: str = "",
        alignment: int = 8,
        partition_attributes: int = PartitionAttribute.NONE,
    ):
        """Initialize Partition Object"""
        self.type_guid = type_guid
        self.partition_name = name
        self.partition_guid = partition_guid
        # if the partition GUID is empty, generate one
        if not partition_guid:
            self.partition_guid = str(uuid.uuid4())
        self._first_lba = StagedAttribute(0)
        self._last_lba = StagedAttribute(0)
        self._attribute_flags = partition_attributes
        self.alignment = alignment
        self._size = StagedAttribute(0)
        self._size.value = size

    def __repr__(self) -> str:
        partitionvalue = {k: v for k, v in vars(self).items() if not k.startswith("_")}
        partitionvalue["attribute_flags"] = self.attribute_flags
        return json.dumps(partitionvalue, indent=2, ensure_ascii=False)

    @property
    def first_lba(self) -> int:
        return int(self._first_lba.value)

    @first_lba.setter
    def first_lba(self, value: int) -> None:
        self._first_lba.value = value

    @property
    def first_lba_staged(self) -> int:
        return int(self._first_lba.staged_value)

    @property
    def last_lba(self) -> int:
        return int(self._last_lba.value)

    @last_lba.setter
    def last_lba(self, value: int) -> None:
        self._last_lba.value = value

    @property
    def last_lba_staged(self) -> int:
        return int(self._last_lba.staged_value)

    @property
    def size(self) -> int:
        return int(self._size.value)

    @size.setter
    def size(self, value: int) -> None:
        self._size.value = value

    @property
    def size_staged(self) -> int:
        return int(self._size.staged_value)

    @property
    def attribute_flags(self) -> List[int]:
        """Return a list of partition attribute flags

        Returns:
            List of attribute flags as integers, returns an empty list if no attributes
                are set
        """

        flags = []
        flag_int = self._attribute_flags
        while flag_int:
            flags.append((flag_int).bit_length() - 1)
            # remove the MSB by masking the integer by length -1
            flag_int = flag_int & ((1 << (flag_int.bit_length() - 1)) - 1)
        return flags

    @attribute_flags.setter
    def attribute_flags(self, flag: PartitionAttribute) -> None:
        """Set the partition attribute flag

        Sets the bit corresponding to the PartitionAttribute Class. If the
            PartitionAttribute.NONE value is set, this clears all flags

        Args:
            flag: integer value of partition attribute flags
        """

        if flag.value == 0:
            self._attribute_flags = 0
        else:
            self._attribute_flags = self._attribute_flags | (1 << flag.value)

    def marshal(self) -> bytes:
        """Marshal to byte structure

        Returns:
            Partition object represented as bytes
        """

        attributes_value = 0
        for attrib in self.attribute_flags:
            attributes_value += 2**attrib
        partition_bytes = self._PARTITION_FORMAT.pack(
            uuid.UUID(self.type_guid).bytes_le,
            uuid.UUID(self.partition_guid).bytes_le,
            self.first_lba_staged,
            self.last_lba_staged,
            attributes_value,
            bytes(self.partition_name, encoding="utf_16_le"),
        )
        return partition_bytes

    def _staged_attrs(self) -> List[StagedAttribute]:
        return [attr
                for attr in [self._first_lba, self._last_lba, self._size]
                if attr.needs_commit()]

    def _commit_attrs(self) -> None:
        for attr in self._staged_attrs():
            attr.commit()

    def needs_commit(self) -> bool:
        if len(self._staged_attrs()) == 0:
            return False
        return True

    def commit(self, disk: Disk, tmpfile: Optional[IO[bytes]] = None) -> None:
        if tmpfile is None:
            f: IO[bytes] = open(disk.image_path, 'r+b')
        else:
            f = tmpfile
        try:
            max_size = min(self.size, self.size_staged)
            data = self.read(disk, max_size=max_size)
            start = disk.sector_size * self.first_lba_staged
            self._write_data(f, start, bytes(data))
            self._commit_attrs()
        finally:
            if tmpfile is None:
                f.close()

    def _write_data(self, image: IO[bytes], start_offset: int, data: bytes) -> int:
        image.seek(start_offset)
        image.write(data)
        return len(data)

    def write_data(self, disk: Disk, data: bytes, offset: int = 0) -> int:
        """Write bytes to partition

        Args:
            disk: GPT Disk instance
            data: data in bytes
            offset: an offset (number of bytes) within the partition at which to write
        Returns:
            integer of byte count written
        Raises:
            ValueError if byte count is too large for partition
        """

        if len(data) + offset > self.size:
            raise ValueError(f"data too large for partition: {len(data)} + {offset} > {self.size}")
        start = disk.sector_size * self.first_lba + offset
        with open(disk.image_path, 'r+b') as image:
            return self._write_data(image, start, data)

    def read(self, disk: Disk, max_size: Optional[int] = None) -> bytearray:
        """Read bytes from a given partition

        Args:
            disk: GPT Disk instance
            max_size: a maximum number of bytes to read (or None to read the entire partition)
        Returns:
            bytearray of partition data
        """

        with open(str(disk.image_path), "rb") as b:
            start = disk.sector_size * self.first_lba
            size = self.size
            if max_size is not None:
                size = min(size, max_size)
            b.seek(start)
            buffer = b.read(size)
        return bytearray(buffer)

    def matches_name_or_guid(self, name_or_guid: str) -> bool:
        """Checks whether this partition matches the provided string. This can match
        on partition name (case-sensitive) or partition GUID (case-insensitive).

        Returns:
            True if the string matches this partition, False otherwise.
        """

        if self.partition_name == name_or_guid:
            return True
        if self.partition_guid.lower() == name_or_guid.lower():
            return True
        return False

    @staticmethod
    def unmarshal(partition_bytes: bytes, sector_size: int) -> "Partition":
        """Create a Partition object from existing bytes

        Args:
            partition_bytes: is a bytes string representing a GPT partition entry
            sector_size: disk sector size in bytes
        Returns:
            an instance of the Partition class
        """

        if len(partition_bytes) != PartitionEntryArray.EntryLength:
            raise ValueError(f"Invalid Partition Entry length: {len(partition_bytes)}")
        (
            type_guid,
            partition_guid,
            first_lba,
            last_lba,
            attribute_flags,
            partition_name,
        ) = Partition._PARTITION_FORMAT.unpack(partition_bytes)
        size = (last_lba - first_lba + 1) * sector_size

        part = Partition(
            partition_name.decode("utf_16_le").rstrip("\x00"),
            size,
            str(uuid.UUID(bytes_le=type_guid)),
            str(uuid.UUID(bytes_le=partition_guid)),
            partition_attributes=attribute_flags,
        )
        part.first_lba = first_lba
        part.last_lba = last_lba
        part._commit_attrs()
        return part


class PartitionEntryArray:
    """Stores the Partition objects for a Table"""

    EntryCount = 128
    EntryLength = 128

    def __init__(self, geometry: Geometry):
        self.entries: List[Partition] = []
        self._geometry: Geometry = geometry

    def add(self, partition: Partition) -> None:
        """Add a partition to the entries

        Appends the Partition to the next available entry. Calculates the LBA's and
        writes them to the partition object's attributes.

        Tests that there is enough space to create the partition with in GPT table
        boundaries.  If the partition would extend beyond last usable LBA an exception
        is raised.

        Args:
            partition: instance of the Partition class to add to the entry table
        Raises:
            PartitionEntryError if the partition will not fit within the table
                boundaries
        """

        partition.first_lba = self._get_first_lba(partition, self.entries)
        partition.last_lba = self._get_last_lba(partition)

        if partition.last_lba_staged > self._geometry.last_usable_lba:
            raise PartitionEntryError(
                "partition overflows the last allowed Logical Block Address: "
                f"{self._geometry.last_usable_lba} requested: {partition.last_lba_staged}"
            )
        self.entries.append(partition)

    def resize(self, partition_name_or_guid: str, size: int) -> Partition:
        """Resize a partition in place. This may truncate data.

        Args:
            partition_name_or_guid: string name of partition to resize
            size: new integer size of partition in bytes
        Returns:
            the partition instance
        Raises:
            NameError if the partition was not found
        """

        entries: List[Partition] = []
        matched_partition: Optional[Partition] = None
        for partition in self.entries:
            if partition.matches_name_or_guid(partition_name_or_guid):
                partition.size = size
                matched_partition = partition
            if matched_partition is not None:
                partition.first_lba = self._get_first_lba(partition, entries)
                partition.last_lba = self._get_last_lba(partition)
            entries.append(partition)
        if matched_partition is None:
            raise NameError(partition_name_or_guid)
        self.entries = entries
        return matched_partition

    def remove(self, partition_name_or_guid: str) -> Partition:
        """Remove a partition from the list of entries

        Args:
            partition_name_or_guid: string name of partition to remove
        Returns:
            the partition instance
        Raises:
            NameError if the partition was not found
        """

        entries: List[Partition] = []
        matched_partition: Optional[Partition] = None
        for partition in self.entries:
            if partition.matches_name_or_guid(partition_name_or_guid):
                matched_partition = partition
                continue
            if matched_partition is not None:
                partition.first_lba = self._get_first_lba(partition, entries)
                partition.last_lba = self._get_last_lba(partition)
            entries.append(partition)
        if matched_partition is None:
            raise NameError(partition_name_or_guid)
        self.entries = entries
        return matched_partition

    def commit(self, disk: Disk) -> None:
        """Shift partition data within the disk based on any staged LBA/size modifications,
        then commit all staged LBA/size modifications.

        Args:
            disk: GPT Disk instance
        """

        if not any([partition.needs_commit() for partition in self.entries]):
            return
        with tempfile.NamedTemporaryFile() as tmpfile:
            for partition in self.entries:
                partition.commit(disk, tmpfile)
            shutil.copy(tmpfile.name, disk.image_path)

    def _get_first_lba(self, partition: Partition, entries: List[Partition]) -> int:
        """Calculate the first LBA of a new partition

        Search for the largest LBA, this will be used to calculate the first
        LBA of the partition being created.  If it is 0, all partitions are empty
        and the last lba is considered 33.

        The start sector (LBA) will take the alignment into account.

        Args:
            partition: instance of the Partition class to calculate LBA for
            entries: list of Partition instances in which LBA is already calculated
        Returns:
            integer of the first LBA
        """

        def next_lba(end_lba: int, alignment: int) -> int:
            m = int(end_lba / alignment)
            return (m + 1) * alignment

        largest_lba = 0
        for part in entries:
            lba = part.last_lba_staged
            if int(lba) > int(largest_lba):
                largest_lba = lba
        last_lba = 33 if largest_lba == 0 else largest_lba
        return next_lba(int(last_lba), partition.alignment)

    def _get_last_lba(self, partition: Partition) -> int:
        """Calculate the last LBA of a new partition

        The last LBA will always be the -1 from the total partition LBA

        Args:
            partition: instance of the Partition class to calculate LBA for
        Returns:
            integer of the last LBA
        Raises:
            PartitionEntryError if the target partition smaller than a sector
        """

        if partition.size_staged < self._geometry.sector_size:
            raise PartitionEntryError("Partition smaller than sector size")

        # round the LBA up to ensure our LBA will hold the partition
        lba = int(ceil(partition.size_staged / self._geometry.sector_size))
        f_lba = int(partition.first_lba_staged)
        return (f_lba + lba) - 1

    def marshal(self) -> bytes:
        """Convert the Partition Entry Array to its byte structure

        Returns:
            bytes representation of the Partition Entry Array
        """

        parts = [x.marshal() for x in self.entries]
        part_bytes = b"".join(parts)
        # pad the rest with zeros
        padded = part_bytes + b"\x00" * (
            (PartitionEntryArray.EntryCount * PartitionEntryArray.EntryLength)
            - len(part_bytes)
        )
        return padded

    def find(self, partition_name_or_guid: str) -> Optional[Partition]:
        """Find a Partition by name or GUID

        Args:
            partition_name_or_guid: string name (or string GUID) of partition to search for
        Returns:
            the partition instance or None if not found
        """

        for partition in self.entries:
            if partition.matches_name_or_guid(partition_name_or_guid):
                return partition
        return None
