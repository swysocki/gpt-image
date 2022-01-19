import uuid
from dataclasses import dataclass
from math import ceil

from gpt_image.disk import Geometry
from gpt_image.entry import Entry


class Partition:
    """Partition class represents a GPT partition

    Start and end LBA are set to None because they must be calculated
    from a table's partition list.
    """

    @dataclass
    class Type:
        """GPT Partition Types

        https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_entries
        """

        LinuxFileSystem = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"
        EFISystemPartition = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"

    def __init__(
        self,
        name: str = None,
        size: int = 0,
        partition_guid: uuid.UUID = None,
        alignment: int = 8,
    ):
        """Initialize Partition Object

        All parameters have a default value to allow Partition() to create
        an empty partition object.  If "name" is set, we assume this is not
        an empty object and set the other values.

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
        if name:
            self.type_guid.data = uuid.UUID(Partition.Type.LinuxFileSystem).bytes_le
            if not partition_guid:
                self.partition_guid.data = uuid.uuid4().bytes_le
            else:
                self.partition_guid.data = partition_guid.bytes_le
            b_name = bytes(name, encoding="utf_16_le")
            # ensure the partition name is padded
            self.partition_name.data = b_name + bytes(72 - len(b_name))

        self.alignment = alignment
        self.size = size

        self.partition_fields = [
            self.type_guid,
            self.partition_guid,
            self.first_lba,
            self.last_lba,
            self.attribute_flags,
            self.partition_name,
        ]

    def as_bytes(self) -> bytes:
        """Return the partition as bytes"""
        byte_list = [x.data for x in self.partition_fields]
        return b"".join(byte_list)


class PartitionEntry:
    """Stores the Partition objects for a Table"""

    def __init__(self, geometry: Geometry, entry_size: int = 128):
        self.entries = [Partition()] * entry_size
        self._geometry = geometry

    def add(self, partition: Partition):
        """Add a partition to the entries

        Appends the Partition to the next available entry. Calculates the
        LBA's
        """
        partition.first_lba.data = (self._get_first_lba(partition)).to_bytes(
            8, "little"
        )
        partition.last_lba.data = (self._get_last_lba(partition)).to_bytes(8, "little")
        entry_indx = self._get_next_partition()
        self.entries[entry_indx] = partition

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
            lba = int.from_bytes(part.last_lba.data, byteorder="little")
            if lba > largest_lba:
                largest_lba = lba
        last_lba = 33 if largest_lba == 0 else largest_lba
        return next_lba(last_lba, partition.alignment)

    def _get_last_lba(self, partition: Partition) -> int:
        """Calculate the last LBA of a new partition

        @NOTE: this likely needs improvement

        """
        assert (
            partition.size > self._geometry.sector_size
        ), "Partition smaller than sector size"

        # round the LBA up to ensure our LBA will hold the partition
        lba = ceil(partition.size / self._geometry.sector_size)
        f_lba = int.from_bytes(partition.first_lba.data, byteorder="little")
        return (f_lba + lba) - 1

    def _get_next_partition(self) -> int:
        """Return the index of the next unused partition"""

        # @TODO: handle error if partition not found
        for idx, part in enumerate(self.entries):
            # return the first partition index that has no name
            if int.from_bytes(part.partition_name.data, byteorder="little") == 0:
                return idx

    def as_bytes(self) -> bytes:
        """Represent as bytes

        Return the entire partition entrie list as bytes
        """
        parts = [x.as_bytes() for x in self.entries]
        return b"".join(parts)
