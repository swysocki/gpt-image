from typing import Union


class Entry:
    def __init__(self, offset: int, length: int, data: Union[str, bytes, int]):
        self.offset = offset
        self.length = length
        assert type(data) in [str, int, bytes], "data must be of type str, int or bytes"

        self.data = self._convert_data(data)

    def _convert_data(self, data: Union[str, bytes, int]) -> bytes:
        """Convert incoming data to bytes

        Convenience class that converts data to bytes of the correct length

        """
        if isinstance(data, int):
            return (data).to_bytes(self.length, "little")
        if isinstance(data, str):
            b_string = bytes(data, encoding="utf_16_le")
            padded = b_string + bytes(self.length - len(b_string))
            return padded
        return data
