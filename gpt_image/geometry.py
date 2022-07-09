class Geometry:
    """Geometry of disk image

    This is a convenience class that provides geometry calculations for
    an underlying disk

    Attributes:
        sector_size: typically set to 512 bytes
        total_bytes: disk size in bytes
        total_sectors: number of sectors on the disk
        total_lba: number of logical blocks on the disk
        header_length: 92 bytes
        array_max_length: maximum partition array length in bytes (128*128)
        first_usable_lba: logical block where the partitions start
        last_usable_lba: logical block where the partitions end
        my_lba: logical block location of primary header
        primary_header_byte: byte where primary header starts
        partition_entry_lba: logical block where the primary partition array starts
        primary_array_byte: byte where the primary partition array starts
        alternate_lba: logical block where the backup header starts
        alternate_header_byte: byte where the backup header starts
        alternate_array_lba: logical block where backup partition array starts
        alternate_array_byte: byte where the backup partition array starts
    """

    def __init__(self, size: int, sector_size: int = 512) -> None:
        """Init Geometry with size in bytes"""
        self.sector_size = sector_size
        self.total_bytes = size
        self.total_sectors = int(size / self.sector_size)
        self.total_lba = int(size / self.sector_size)
        self.header_length = 92
        self.array_max_length = 128 * 128
        self.first_usable_lba = 34
        self.last_usable_lba = int(self.total_lba - 34)
        self.my_lba = 1
        self.primary_header_byte = int(self.my_lba * self.sector_size)
        self.partition_entry_lba = 2
        self.primary_array_byte = int(self.partition_entry_lba * self.sector_size)
        self.alternate_lba = int(self.total_lba - 1)
        self.alternate_header_byte = int(self.alternate_lba * self.sector_size)
        self.alternate_array_lba = int(self.total_lba - 33)
        self.alternate_array_byte = int(self.alternate_array_lba * self.sector_size)
