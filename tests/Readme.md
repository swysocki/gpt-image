# Test Notes

## Reference Image

We use a 16MB disk image, partitioned using the `gdisk` or `sgdisk` utility as reference.
Create the image using the following commands.

```bash
fallocate -l 16M ref-disk.raw
```

Use `gdisk` to build a GPT disk:

* run `gdisk ref-disk.raw`
* set the alignment to 4096 bytes
  * enter `x` (extra functionality)
  * enter `l` (set sector alignment) to 8
  * enter `m` (return to main menu)
* create a new partition of 4 sectors (2048 bytes)
  * enter `n` (new partition)
    * enter `1` for partition number
    * enter `40` for first sector
    * enter `43` for last sector
    * enter `8300` for file system
* write the table and exit
  * enter `w`
