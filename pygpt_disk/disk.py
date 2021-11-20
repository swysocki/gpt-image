import io


class Disk:
    sector_size = 512

    def __init__(self, size: int, name: str) -> None:
        # @NOTE: this needs to accept a disk path or create a new disk
        self.size = size
        self.name = name
        self.sectors = size / Disk.sector_size
        self.buffer = io.BytesIO()

    def create(self) -> None:
        """Create a buffer to write image contents"""
        self.buffer.seek(self.size - 1)
        self.buffer.write(b"\0")

    def write(self) -> None:
        """Write a disk buffer to file"""
        with open(self.name, "wb") as f:
            f.write(self.buffer.getvalue())
