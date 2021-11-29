import io
import pathlib


class Disk:
    sector_size = 512

    def __init__(self, image_path: str, size: int = 0) -> None:
        """Create a disk object

        A disk objects represents a new or existing GPT disk
        image.  If the file exists, it is assumed to be an existing
        GPT image. If it does not, a new file is created.

        Args:
            image_path: file image path (absolute or relative)
            size: disk image size in bytes
        """
        self._image_path = pathlib.Path(image_path)
        self.name = self._image_path.name
        self.size = size
        if self._image_path.exists():
            self.size = self._image_path.stat().st_size
        self.sectors = size / Disk.sector_size
        self.buffer = io.BytesIO()

    # @NOTE: bad idea here. This could create a large buffer if the
    # disk is huge
    def create(self) -> None:
        """Create a buffer to write image contents"""
        self.buffer.seek(self.size - 1)
        self.buffer.write(b"\0")

    def write(self) -> None:
        """Write a disk buffer to file"""
        self._image_path.write_bytes(self.buffer.getvalue())
