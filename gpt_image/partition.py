import uuid
from math import ceil
from typing import List, Union

from gpt_image.entry import Entry
from gpt_image.geometry import Geometry


class Partition:
    """Partition class represents a GPT partition

    Start and end LBA are set to None because they must be calculated
    from a table's partition list.
    """

    # https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_entries
    LINUX_FILE_SYSTEM = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"
    EFI_SYSTEM_PARTITION = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"

    def __init__(
        self,
        name: str = "",
        size: int = 0,
        partition_guid: Union[None, uuid.UUID] = None,
        alignment: int = 8,
    ):
        """Initialize Partition Object

        All parameters have a default value to allow Partition() to create
        an empty partition object.  If "name" is set, we assume this is not
        an empty object and set the other values.

        Empty partition objects are used as placeholders in the partition
        entry array.

        Attributes:
            size: partition size in Bytes
        """
        # create an empty partition object
        self.type_guid = Entry(0, 16, 0)
        self.partition_guid = Entry(16, 16, 0)
        self.first_lba = Entry(32, 8, 0)
        self.last_lba = Entry(40, 8, 0)
        self.attribute_flags = Entry(48, 8, 0)
        self.partition_name = Entry(56, 72, 0)
        # if name is set, this isn't an empty partition. Set relevant fields
        # @TODO: don't base an empty partition off of the name attribute
        if name:
            self.type_guid.data = uuid.UUID(Partition.LINUX_FILE_SYSTEM).bytes_le
            if not partition_guid:
                self.partition_guid.data = uuid.uuid4().bytes_le
            else:
                self.partition_guid.data = partition_guid.bytes_le
            # the partition name is stored as utf_16_le
            self.partition_name.data = bytes(name, encoding="utf_16_le")

        self.alignment = alignment
        self.size = size

    @property
    def byte_structure(self) -> bytes:
        part_fields = [
            self.type_guid,
            self.partition_guid,
            self.first_lba,
            self.last_lba,
            self.attribute_flags,
            self.partition_name,
        ]
        byte_list = [x.data_bytes for x in part_fields]
        return b"".join(byte_list)

    def read(self, partition_bytes):
        """Unmarshal bytes to Partition Object"""
        self.type_guid.data = partition_bytes[
            self.type_guid.offset : self.type_guid.offset + self.type_guid.length
        ]
        self.partition_guid.data = partition_bytes[
            self.partition_guid.offset : self.partition_guid.offset
            + self.partition_guid.length
        ]
        self.first_lba.data = partition_bytes[
            self.first_lba.offset : self.first_lba.offset + self.first_lba.length
        ]
        self.last_lba.data = partition_bytes[
            self.last_lba.offset : self.last_lba.offset + self.last_lba.length
        ]
        self.attribute_flags.data = partition_bytes[
            self.attribute_flags.offset : self.attribute_flags.offset
            + self.attribute_flags.length
        ]
        part_name_b = partition_bytes[
            self.partition_name.offset : self.partition_name.offset
            + self.partition_name.length
        ]
        # partition name is stored as UTF-16-LE padded to 72 bytes
        self.partition_name.data = part_name_b.decode(encoding="utf_16_le").rstrip(
            "\x00"
        )


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
        partition.first_lba.data = self._get_first_lba(partition)
        partition.last_lba.data = self._get_last_lba(partition)
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
            lba = part.last_lba.data
            if int(lba) > int(largest_lba):
                largest_lba = lba
        last_lba = 33 if largest_lba == 0 else largest_lba
        return next_lba(int(last_lba), partition.alignment)

    def _get_last_lba(self, partition: Partition) -> int:
        """Calculate the last LBA of a new partition

        The last LBA will always be the -1 from the total partition LBA

        """
        assert (
            partition.size > self._geometry.sector_size
        ), "Partition smaller than sector size"

        # round the LBA up to ensure our LBA will hold the partition
        lba = int(ceil(partition.size / self._geometry.sector_size))
        f_lba = int(partition.first_lba.data)
        return (f_lba + lba) - 1

    @property
    def byte_structure(self) -> bytes:
        """Convert the Partition Array to its byte structure"""
        parts = [x.byte_structure for x in self.entries]
        part_bytes = b"".join(parts)
        # pad the rest with zeros
        padded = part_bytes + b"\x00" * (
            (PartitionEntryArray.EntryCount * PartitionEntryArray.EntryLength)
            - len(part_bytes)
        )
        return padded
