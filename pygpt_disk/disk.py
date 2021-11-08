import io


class Disk:
    sector_size = 512

    def __init__(self, size: int, name: str):
        self.size = size
        self.name = name
        self.buffer = io.BytesIO()  # this is bad, it makes Disk.disk :(

    def create(self) -> None:
        self.buffer.seek(self.size - 1)
        self.buffer.write(b"\0")

    def write(self) -> None:
        """Write a disk buffer to file"""
        with open(self.name, "wb") as f:
            f.write(self.buffer.getvalue())
