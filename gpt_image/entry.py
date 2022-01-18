class Entry:
    def __init__(self, offset: int, length: int, data: bytes):
        self.offset = offset
        self.length = length
        self.data = data

    def int_to_bytes(self, number: int) -> None:
        """Convert in to the proper byte length"""
        self.data = (number).to_bytes(self.length, "little")

    def str_to_bytes(self, string: str) -> None:
        b_string = bytes(string, encoding="utf_16_le")
        padded = b_string + bytes(self.length - len(b_string))
        self.data = padded
