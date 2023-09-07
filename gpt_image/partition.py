from __future__ import annotations

import json
import struct
import uuid
from enum import Enum, IntEnum
from math import ceil
from typing import List, Optional
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
        self.first_lba = 0
        self.last_lba = 0
        self._attribute_flags = partition_attributes
        self.alignment = alignment
        self.size = size

    def __repr__(self) -> str:
        partitionvalue = {k: v for k, v in vars(self).items() if not k.startswith("_")}
        partitionvalue["attribute_flags"] = self.attribute_flags
        return json.dumps(partitionvalue, indent=2, ensure_ascii=False)

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
            self.first_lba,
            self.last_lba,
            attributes_value,
            bytes(self.partition_name, encoding="utf_16_le"),
        )
        return partition_bytes

    def write_data(self, disk: Disk, data: bytes) -> int:
        """Write bytes to partition

        Args:
            disk: GPT Disk instance
            data: data in bytes
        Returns:
            integer of byte count written
        Raises:
            ValueError if byte count is too large for partition
        """
        if len(data) > self.size:
            raise ValueError(f"data too large for partition: {len(data)} {self.size}")
        with open(str(disk.image_path), "r+b") as b:
            start = self.first_lba * disk.sector_size
            b.seek(start)
            b.write(data)
        return len(data)

    def read(self, disk: Disk) -> bytearray:
        """Read bytes from a given partition

        Args:
            disk: GPT Disk instance
        Returns:
            bytearray of partition data
        """
        with open(str(disk.image_path), "rb") as b:
            start = self.first_lba * disk.sector_size
            b.seek(start)
            buffer = b.read(self.size)
        return bytearray(buffer)

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

        partition.first_lba = self._get_first_lba(partition)
        partition.last_lba = self._get_last_lba(partition)

        if partition.last_lba > self._geometry.last_usable_lba:
            raise PartitionEntryError(
                "partition overflows the last allowed Logical Block Address: "
                f"{self._geometry.last_usable_lba} requested: {partition.last_lba}"
            )
        self.entries.append(partition)

    def _get_first_lba(self, partition: Partition) -> int:
        """Calculate the first LBA of a new partition

        Search for the largest LBA, this will be used to calculate the first
        LBA of the partition being created.  If it is 0, all partitions are empty
        and the last lba is considered 33.

        The start sector (LBA) will take the alignment into account.

        Args:
            partition: instance of the Partition class to calculate LBA for
        Returns:
            integer of the first LBA
        """

        def next_lba(end_lba: int, alignment: int) -> int:
            m = int(end_lba / alignment)
            return (m + 1) * alignment

        largest_lba = 0
        for part in self.entries:
            lba = part.last_lba
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

        if partition.size < self._geometry.sector_size:
            raise PartitionEntryError("Partition smaller than sector size")

        # round the LBA up to ensure our LBA will hold the partition
        lba = int(ceil(partition.size / self._geometry.sector_size))
        f_lba = int(partition.first_lba)
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

    def find(self, partition_name: str) -> Optional[Partition]:
        """Find a Partition by name

        Args:
            partition_name: string name of partition to search for
        Returns:
            the partition instance or None if not found
        """
        for partition in self.entries:
            if partition.partition_name == partition_name:
                return partition
        return None
