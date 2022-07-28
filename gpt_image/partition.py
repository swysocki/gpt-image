import json
import struct
import uuid
from enum import IntEnum
from math import ceil
from typing import List

from gpt_image.geometry import Geometry


class PartitionEntryError(Exception):
    """Exception class for erros in partition entries"""


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


class Partition:
    """Partition class represents a GPT partition

    Start and end LBA are set to None because they must be calculated
    from a table's partition list.

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
    _EMPTY_GUID = "00000000-0000-0000-0000-000000000000"
    # https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_entries
    LINUX_FILE_SYSTEM = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"
    EFI_SYSTEM_PARTITION = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"

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
        self._attribute_flags = 0
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
        partitionvalue['attribute_flags'] = self.attribute_flags
        return json.dumps(partitionvalue, indent=2, ensure_ascii=False)

    @property
    def attribute_flags(self) -> List[int]:
        """Return a list of partition attribute flags

        Returns an empty list if no attributes are set

        """
        flags = []
        flag_int = self._attribute_flags
        while flag_int:
            flags.append((flag_int).bit_length() - 1)
            # remove the MSB by masking the integer by length -1
            flag_int = flag_int & ((1 << (flag_int.bit_length() - 1)) - 1)
        return flags

    @attribute_flags.setter
    def attribute_flags(self, flag: PartitionAttribute):
        """Set the partition attribute flag

        Sets the bit corresponding to the PartitionAttribute Class.
        If the PartitionAttribute.NONE value is set, this clears all flags
        """
        if flag.value == 0:
            self._attribute_flags = 0
        else:
            self._attribute_flags = self._attribute_flags | (1 << flag.value)

    def marshal(self) -> bytes:
        """Marshal to byte structure"""
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

    @staticmethod
    def read(partition_bytes: bytes, sector_size: int) -> "Partition":
        """Create a Partition object from existing bytes"""
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

        Appends the Partition to the next available entry. Calculates the
        LBA's
        """
        partition.first_lba = self._get_first_lba(partition)
        partition.last_lba = self._get_last_lba(partition)
        self.entries.append(partition)

    def _get_first_lba(self, partition: Partition) -> int:
        """Calculate the first LBA of a new partition

        Search for the largest LBA, this will be used to calculate the first
        LBA of the partition being created.  If it is 0, all partitions are empty
        and the last lba is considered 33.

        The start sector (LBA) will take the alignment into account.

        """

        def next_lba(end_lba: int, alignment: int):
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

        """
        if partition.size < self._geometry.sector_size:
            raise PartitionEntryError("Partition smaller than sector size")

        # round the LBA up to ensure our LBA will hold the partition
        lba = int(ceil(partition.size / self._geometry.sector_size))
        f_lba = int(partition.first_lba)
        return (f_lba + lba) - 1

    def marshal(self) -> bytes:
        """Convert the Partition Entry Array to its byte structure"""
        parts = [x.marshal() for x in self.entries]
        part_bytes = b"".join(parts)
        # pad the rest with zeros
        padded = part_bytes + b"\x00" * (
            (PartitionEntryArray.EntryCount * PartitionEntryArray.EntryLength)
            - len(part_bytes)
        )
        return padded
