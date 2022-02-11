import pathlib
import uuid

from gpt_image.geometry import Geometry
from gpt_image.partition import Partition
from gpt_image.table import ProtectiveMBR, Table


class Disk:
    """GPT disk

    A disk objects represents a new or existing GPT disk image.  If the file exists,
    it is assumed to be an existing GPT image. If it does not, a new file is created.

    Attributes:
        image_path: file image path (absolute or relative)
        size: disk image size in bytes
        sector_size: disk sector size. This should not be changed, changes to the
          layout should be done through the Partition alignment attribute
        fresh_disk: boolean create a new disk
    """

    def __init__(
        self,
        image_path: str,
        size: int = 0,
        sector_size: int = 512,
        *,
        fresh_disk: bool = False
    ) -> None:
        """Init Disk with a file path and size in bytes"""
        self.image_path = pathlib.Path(image_path)
        self.name = self.image_path.name
        self.size = size
        self.sector_size = sector_size
        self.geometry = Geometry(self.size, self.sector_size)
        self.table = Table(self.geometry)
        if fresh_disk:
            self._create_disk()
        else:
            # @TODO: handle existing disk
            pass

    def _create_disk(self):
        """Create the disk image on Disk

        Creates the basic image structure at the specified path. This zeros
        the disk and writes the protective MBR.

        """
        self.image_path.touch(exist_ok=False)
        with open(self.image_path, "r+b") as f:
            # zero entire disk
            f.write(b"\x00" * self.size)
            f.seek(ProtectiveMBR.PROTECTIVE_MBR_START)
            f.write(self.table.protective_mbr.as_bytes())
            f.seek(ProtectiveMBR.DISK_SIGNATURE_START)
            f.write(self.table.protective_mbr.signature.data)

    def create_partition(
        self, name: str, size: int, guid: uuid.UUID, alignment: int = 8
    ) -> Partition:
        """Create a GPT partition

        Wraps the creation of a Partition object to allow it to be created from
        the Disk class

        Args:
            name: partition name
            size: partition size in Bytes
            guid: partition GUID. generated if None
            alignment: sector alignment
        Returns:
            Partition object
        """
        part = Partition(name, size, guid, alignment)
        self.table.partitions.add(part)
        # @TODO: returning this is probably unecessary
        return part

    def update_table(self):
        """Update the GPT table

        Writes the GPT header and partition tables to disk. Actions that
        happen before this are not written to disk.

        """
        self.table.update()
        with open(self.image_path, "r+b") as f:
            # write primary header
            f.seek(self.geometry.primary_header_byte)
            f.write(self.table.primary_header.as_bytes())

            # write primary partition table
            f.seek(self.geometry.primary_array_byte)
            f.write(self.table.partitions.as_bytes())

            # move to secondary header location and write
            f.seek(self.geometry.backup_header_byte)
            f.write(self.table.secondary_header.as_bytes())

            # write secondary partition table
            f.seek(self.geometry.backup_array_byte)
            f.write(self.table.partitions.as_bytes())
