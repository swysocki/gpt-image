import io


class Disk:
    def __init__(self, size: int, name: str):
        self.size = size
        self.name = name
        self.disk = io.BytesIO()

    def create(self) -> None:
        self.disk.seek(self.size - 1)
        self.disk.write(b"\0")

    def write(self) -> None:
        """Write a disk buffer to file"""
        with open(self.name, "wb") as f:
            f.write(self.disk.getvalue())
