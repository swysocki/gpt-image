import struct
from typing import Union


class Entry:
    """Entry Class contains a GPT table entry data"""

    valid_types = [str, bytes, int]

    def __init__(self, offset: int, length: int, input_data: Union[str, bytes, int]):
        """Create a GPT table entry

        Args:
            offset: the location of the bytes relative to structure
            length: of entry in bytes
            input_data: value the field is set to. can be str, bytes, int
        """
        self.offset = offset
        self.length = length
        self.end = self.offset + self.length
        self.data = input_data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if type(value) not in Entry.valid_types:
            raise ValueError(f"invalid entry type: {type(value)}")
        # @TODO: handle too large of integer
        if (isinstance(value, str) or isinstance(value, bytes)) and len(
            value
        ) > self.length:
            raise ValueError(f"insufficient space for entry data: {self.length}")
        self._data = value

    @property
    def data_bytes(self) -> bytes:
        if isinstance(self.data, int):
            return (self.data).to_bytes(self.length, "little")
        if isinstance(self.data, str):
            return struct.pack(
                f"<{str(self.length)}s", bytes(self.data, encoding="ascii")
            )
        if isinstance(self.data, bytes):
            return struct.pack(f"<{str(self.length)}s", self.data)
        raise ValueError("cannot convert value to bytes")
