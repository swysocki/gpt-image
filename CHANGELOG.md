# CHANGELOG



## v0.8.0 (2023-09-07)

### Feature

* feat: read partition data ([`1bd9159`](https://github.com/swysocki/gpt-image/commit/1bd91590fadd7d927090539efd149fcd500392ba))

* feat: write data function ([`7b8c176`](https://github.com/swysocki/gpt-image/commit/7b8c176c6a6e87689e67684a2fce8876bef03e3a))

* feat: add partition find function ([`7d810cf`](https://github.com/swysocki/gpt-image/commit/7d810cf3a4057cb58c559aae27bf15a7c7602a20))


## v0.7.0 (2022-09-11)

### Documentation

* docs: update partition type to use enum ([`bf5ddbc`](https://github.com/swysocki/gpt-image/commit/bf5ddbc823311a9697ffd0af7a2aa3584b441786))

### Feature

* feat: change disk open API

Allows the disk.open() function to be called without first creating
a disk.Disk instance. ([`5259629`](https://github.com/swysocki/gpt-image/commit/525962940e1fc25cd217d0d46a84f3c6963d963f))


## v0.6.8 (2022-09-10)

### Fix

* fix: add partition GUID for Linux, Windows, Mac

Add additional partition UUID values for common OS&#39;s ([`e45c102`](https://github.com/swysocki/gpt-image/commit/e45c10221e952a84967b254962b9a6d0b75490a3))


## v0.6.7 (2022-08-09)

### Chore

* chore: reformat readme ([`c4533a9`](https://github.com/swysocki/gpt-image/commit/c4533a904e1abede474a4c3c6e673c96fc030726))

### Fix

* fix: raise an error if partition is too large ([`f4b1fca`](https://github.com/swysocki/gpt-image/commit/f4b1fcae926d1ce32f2c5fa415fcb4404d268cba))

### Unknown

* simplify imports in readme ([`801ff40`](https://github.com/swysocki/gpt-image/commit/801ff408c2d0c24a3052a552b241ee873f8a1588))


## v0.6.6 (2022-08-02)

### Ci

* ci: add gdisk verification tests ([`091b1e0`](https://github.com/swysocki/gpt-image/commit/091b1e0d8b9e532c7280855b11eb4c71c6b41b55))

### Documentation

* docs: update quick start example ([`d28dd28`](https://github.com/swysocki/gpt-image/commit/d28dd281f94cced2ce32350eb0f560fe079fc408))

### Fix

* fix: ensure disk GUID&#39;s match in header

primary and backup header must match. This ensure the backup uses the
primary&#39;s GUID and adds a test to check.

fixes #39 ([`5b7503f`](https://github.com/swysocki/gpt-image/commit/5b7503fd9bab243958d6dc2470d4a9b255d5084f))

### Refactor

* refactor: change disk.write() function name ([`94dd23e`](https://github.com/swysocki/gpt-image/commit/94dd23e9a2b76cd27ffe0bc40a90f460569a00e6))

* refactor: remove partition write function ([`be423c7`](https://github.com/swysocki/gpt-image/commit/be423c7f1f3274e6bb03f444f41ba2acbc172f74))


## v0.6.5 (2022-07-31)

### Chore

* chore: add mypy strict type hints for partition module ([`90d17f9`](https://github.com/swysocki/gpt-image/commit/90d17f947427f18a0e64223581f2ddff77dbcff1))

* chore: add mypy strict type hints for disk module ([`93ddf50`](https://github.com/swysocki/gpt-image/commit/93ddf50d711044d5d797fc4ceeae6c5a56944cb7))

* chore: update doc comments for partition module ([`566ef26`](https://github.com/swysocki/gpt-image/commit/566ef26708d8f76510d11c4662bf9d064fce06a2))

* chore: cleanup disk module formatting and docs ([`6e7eebe`](https://github.com/swysocki/gpt-image/commit/6e7eebea46004b346c7389985a31ee91061c8698))

* chore: change read method to unmarshal

change to more descriptive name. read() may be used in the class
for something else in the future ([`27e13a3`](https://github.com/swysocki/gpt-image/commit/27e13a37bb5e45aa1085f7f5838d3cfa8a6f48f0))

### Fix

* fix: add types tests to CI

Closes #15 ([`fee4da6`](https://github.com/swysocki/gpt-image/commit/fee4da6d99392c69a5efffdbb8c09324e93eab07))


## v0.6.4 (2022-07-28)

### Documentation

* docs: denote partition UUID in creation step ([`8f768d7`](https://github.com/swysocki/gpt-image/commit/8f768d758eeb1f735f94432adf555b6c927b6ce6))

### Fix

* fix: make attributes integer-like

Replace the PartitionAttribute Enum base class with IntEnum
to allow integer comparison ([`1f875cb`](https://github.com/swysocki/gpt-image/commit/1f875cbbf1d0ec973957747b8653fd4445d2d10a))


## v0.6.3 (2022-07-27)

### Fix

* fix: add py.typed to package ([`3b13b41`](https://github.com/swysocki/gpt-image/commit/3b13b41bdcfd3a6d1733264a1d8fd4d90329f388))


## v0.6.2 (2022-07-25)

### Fix

* fix: add disk image data to string repr ([`2d5b3ef`](https://github.com/swysocki/gpt-image/commit/2d5b3ef7e64705c97f74622b98636b21fdc0de3c))


## v0.6.1 (2022-07-24)

### Chore

* chore: restore main repo for release workflow ([`df5491f`](https://github.com/swysocki/gpt-image/commit/df5491fae24601a00d9bece1426834af2af206ed))

### Fix

* fix: Return friendly partition attribute flags

Return the bit position(s) of the partition attribute flag if set. ([`6fb826f`](https://github.com/swysocki/gpt-image/commit/6fb826f715d74792fae265afe2634349989a0025))


## v0.6.0 (2022-07-23)

### Feature

* feat: add JSON output of objects

Closes #22 ([`467f104`](https://github.com/swysocki/gpt-image/commit/467f1046c7898e878a03cb8f4ee8b8cf337b0c87))


## v0.5.0 (2022-07-14)

### Feature

* feat: migrate to struct module

Removes the Entry class in favor of the builtin struct module. This
will simplify marshalling the disk image byte data. ([`aaa777f`](https://github.com/swysocki/gpt-image/commit/aaa777f2ab67c8d57c94dcbb3697ed3384a7a251))


## v0.4.2 (2022-07-12)

### Chore

* chore: update Readme with uuid import ([`614b123`](https://github.com/swysocki/gpt-image/commit/614b123a8eb27edb529144ff099c6c701c9936e9))

### Fix

* fix: allow setting the partition attribute on init ([`523e220`](https://github.com/swysocki/gpt-image/commit/523e220c3bc3023e3f59c76517f2338773d31645))

* fix: import modules in package namespace ([`c35476f`](https://github.com/swysocki/gpt-image/commit/c35476faa64b9af870648f0f1dd86e032a36040e))

### Unknown

* fix formatting ([`f5b8210`](https://github.com/swysocki/gpt-image/commit/f5b821050d2aa7cae191a34f221aec088821ecc0))


## v0.4.1 (2022-07-09)

### Fix

* fix: use EFI spec mnemonics for attribute names ([`0e62e24`](https://github.com/swysocki/gpt-image/commit/0e62e24c1d80939068c7d4fd8c5dc703fbd99eb9))


## v0.4.0 (2022-05-28)

### Feature

* feat: allow setting partition attributes ([`fa73bde`](https://github.com/swysocki/gpt-image/commit/fa73bde27921561382613e6ed7ed1df88eb85458))


## v0.3.2 (2022-05-21)

### Ci

* ci: add integration test using sfdisk

Add an integration test using sfdisk to test the resulting GPT image ([`af0b26a`](https://github.com/swysocki/gpt-image/commit/af0b26a1ecb86d174e1644b18587aaeff593c68f))

### Fix

* fix: custom partition error class ([`bf2cdaa`](https://github.com/swysocki/gpt-image/commit/bf2cdaa514c8a1ff44d7df7c2e22d09ab4e9c1a1))

* fix: add missing types ([`f348697`](https://github.com/swysocki/gpt-image/commit/f348697dd7300a12e60d761874819f32b720eb0c))


## v0.3.1 (2022-05-08)

### Fix

* fix: allow guid to be None or UUID type ([`c2f15c7`](https://github.com/swysocki/gpt-image/commit/c2f15c7c12ca5a66023af8b9fcf5db241f2d70aa))

* fix: add marshal function

Use object property to marshal bytes ([`a7e06fd`](https://github.com/swysocki/gpt-image/commit/a7e06fd4fd80b0c8717da9803250d5eeb46969db))

### Unknown

* ignore *.raw files in test directory ([`fba4b56`](https://github.com/swysocki/gpt-image/commit/fba4b56e52db96aef409c8d76cbe2dd0ea5117a2))


## v0.3.0 (2022-05-07)

### Feature

* feat: read existing disk (#14)

* feat: read existing disk

Opens an existing disk image and ummarshals it
to a gpt_image object ([`ed83cb0`](https://github.com/swysocki/gpt-image/commit/ed83cb06efcdcdad2eee6be6930c8027565823b0))


## v0.2.2 (2022-04-03)

### Fix

* fix: adjust pmbr partition size (#13)

Fix the protective MBR partition size value ([`379d615`](https://github.com/swysocki/gpt-image/commit/379d615093451783643a7ec665c98f12ff907927))

### Unknown

* add long description to release

[release skip] ([`2b73f31`](https://github.com/swysocki/gpt-image/commit/2b73f319317f1375c3913ad86a6b346442e934e8))


## v0.2.1 (2022-02-27)

### Fix

* fix: add partition tests (#9) ([`da41ad2`](https://github.com/swysocki/gpt-image/commit/da41ad271ea56a2c0bfb53937ddac4f40599509f))


## v0.2.0 (2022-02-26)

### Ci

* ci: build with build instead of poetry (#6) ([`d4972cb`](https://github.com/swysocki/gpt-image/commit/d4972cb7c30627ec9848177114ca145ec765520d))

### Documentation

* docs: update comments ([`73e7052`](https://github.com/swysocki/gpt-image/commit/73e705213b4fb1144bb8ce92c6d895e7e7be6d4a))

### Feature

* feat: add semantic release (#10) ([`95177b2`](https://github.com/swysocki/gpt-image/commit/95177b21d1d45cb8bde0b736e332fb6452d3ddae))

### Fix

* fix: set version ([`a4262c1`](https://github.com/swysocki/gpt-image/commit/a4262c100acd4cbdf9f04177700a650710c8a757))

* fix: use setup.py for package version ([`3d69f94`](https://github.com/swysocki/gpt-image/commit/3d69f945fb22286ba6623e87f607ddb6c5dd7990))

* fix: remove partition wrapper

Use the partition object directly when creating partitions ([`1f491ad`](https://github.com/swysocki/gpt-image/commit/1f491ad72c05c56094c7ea84b0888d34ffd3a546))

* fix: move logic to Disk object

Moves functionality to the disk object to simplify the creation
of partitions ([`4ab2211`](https://github.com/swysocki/gpt-image/commit/4ab2211a55beb23ce0f148a1a52387efe11fbd9d))

### Test

* test: add table module tests ([`a133a92`](https://github.com/swysocki/gpt-image/commit/a133a925e0aa7c4c9ce5f34b8d2ca5a1cfdeb61f))

### Unknown

* 4 write data (#7)

Allow writing byte data individual partitions ([`c0680cd`](https://github.com/swysocki/gpt-image/commit/c0680cd431fe87448c3c97de1895929ba9d2fa40))

* test with 3.8 ([`3fd92d7`](https://github.com/swysocki/gpt-image/commit/3fd92d7286482a2fecd223d915a004b9bd7b90fa))

* Create python-app.yml ([`de8fa64`](https://github.com/swysocki/gpt-image/commit/de8fa64d5a25738eead9e24375f5df038949140a))

* Rename Partition Entry ([`2ec80ec`](https://github.com/swysocki/gpt-image/commit/2ec80ecfa2aa5aa8cf3dc5ca8569fa92dfa745d3))

* Convert data (#2)

* Convert Entry data to bytes

* Remove MBR magic numbers ([`3ecdbe7`](https://github.com/swysocki/gpt-image/commit/3ecdbe71a5abc59c41e08b871ff9f68954bed930))

* Merge pull request #1 from swysocki/feature/partition-module

Move partitions to Python Class ([`b4d97dc`](https://github.com/swysocki/gpt-image/commit/b4d97dcf9f76d1614e9b94fc8f7b50212efd255e))

* Use Entry class ([`a05226e`](https://github.com/swysocki/gpt-image/commit/a05226e8e48462fd6d109d1272c71bb254d4b26b))

* Separate partition module ([`d0be1fb`](https://github.com/swysocki/gpt-image/commit/d0be1fb74767547943b7a7fd5dbf890d0b6fab3c))

* wip: separate partition module ([`6f6a00b`](https://github.com/swysocki/gpt-image/commit/6f6a00b88e53917c4ce7ef99f40f41e0dd8f6d24))

* wip: remove comments ([`f2ac4a3`](https://github.com/swysocki/gpt-image/commit/f2ac4a307b632aed804f55fc50225c757fab918d))

* Add disk module tests ([`3952f81`](https://github.com/swysocki/gpt-image/commit/3952f81525ea327f4e8f69cb9844ebcc7937c3e4))

* wip: correct partition CRC

The partition name wasn&#39;t being padded to 72 bytes.
Now the alignments need fixing. ([`6809e4e`](https://github.com/swysocki/gpt-image/commit/6809e4e125db0c0477e65744818c3b2e698303bb))

* wip: adding partition

adding a partition works but the CRC for the tables are invalid. ([`73a6973`](https://github.com/swysocki/gpt-image/commit/73a697378719f0ccef2c8383499257be1a0ca3b5))

* wip: create default partition array entry ([`df52857`](https://github.com/swysocki/gpt-image/commit/df52857e6766fde78459836214f52a1de4d5edd1))

* Bare GPT working

Protective MBR and GPT functioning.  Partition CRC&#39;s are not calculated
correctly when a partition is created. ([`4a8dc0f`](https://github.com/swysocki/gpt-image/commit/4a8dc0f633435f10e5e0a3e5e0f3ce447942378e))

* wip: add protective MBR ([`8f797c0`](https://github.com/swysocki/gpt-image/commit/8f797c059d63e883d069aa5b2d8ad4bb137024eb))

* wip: test writing a single partition ([`d06e785`](https://github.com/swysocki/gpt-image/commit/d06e785026fbf32524b3347c039b803fa2596642))

* wip: create new partition ([`f6b1ccf`](https://github.com/swysocki/gpt-image/commit/f6b1ccfe2d652f0258151387233bdcb14c992562))

* wip: initial raw disk ([`e31a479`](https://github.com/swysocki/gpt-image/commit/e31a47989b48248c69da21c72335b5ea96660af2))

* wip: write headers ([`05aab61`](https://github.com/swysocki/gpt-image/commit/05aab61e9ac0e47d6e3c99292ab9525ccf0d3acb))

* wip: more surgery ([`c2ea588`](https://github.com/swysocki/gpt-image/commit/c2ea5881db0b238404a61393c22439db858876d9))

* change package name ([`6cf051e`](https://github.com/swysocki/gpt-image/commit/6cf051ed5c4410fe698227297fd644736785553a))

* wip: write geometry tests ([`28602f4`](https://github.com/swysocki/gpt-image/commit/28602f4168931a78416327ab8f2a7daffaaf9acf))

* wip: clumsy version of seperating headers ([`0105626`](https://github.com/swysocki/gpt-image/commit/01056264d785ff6bbc71bd56588b4626b03237ae))

* reorder checksum functions ([`9175c7d`](https://github.com/swysocki/gpt-image/commit/9175c7d11bcb91a014c042df05a86519b8d877df))

* Zero enter disk in tests

use the disk.create() function to seek to the end of the buffer
effectively zeroing the buffer so checksums will work before writing to
disk ([`48e827d`](https://github.com/swysocki/gpt-image/commit/48e827d3123c499ffd8cb5ba6695b7b662bb47f5))

* Set partition array size to 128 ([`ed111ad`](https://github.com/swysocki/gpt-image/commit/ed111ad3f4f925c0a30ca6f4d05a4f8b42ae5acb))

* fix test ([`e308574`](https://github.com/swysocki/gpt-image/commit/e308574d0deded34774480bb7f63f317bb86ee82))

* wip: header crc ([`e297700`](https://github.com/swysocki/gpt-image/commit/e2977008f52c62ded4edae716608526b00482e33))

* all header section tests ([`5d05fe2`](https://github.com/swysocki/gpt-image/commit/5d05fe2aa7b00597e77828bcb2118d798d54af1d))

* test both headers ([`58cef2a`](https://github.com/swysocki/gpt-image/commit/58cef2af39e498c12b2cdce1cc21d49af4017446))

* Initial commit ([`1a2d21a`](https://github.com/swysocki/gpt-image/commit/1a2d21ab2ad9323de89f7c92736fccbd8122676f))

* wip: remaining header fields ([`480ba3f`](https://github.com/swysocki/gpt-image/commit/480ba3f12e5d61e41b381be974f5e3a6c2ac9496))

* wip: disk GUID ([`2644991`](https://github.com/swysocki/gpt-image/commit/264499183270ead25d64aaca28ff57fa0f94b58a))

* wip: refactor header creation ([`96a3036`](https://github.com/swysocki/gpt-image/commit/96a30366920138747cb456ef9a31e7a4a27fd5be))

* wip: header lba ([`d204cd9`](https://github.com/swysocki/gpt-image/commit/d204cd977fd20a88c2b632d4578e8622a5bdbc15))

* fix offset for first header

avoid truncating image file by writing last byte ([`40e636c`](https://github.com/swysocki/gpt-image/commit/40e636c81b4fc37fcc734210a5a127022b40ddcc))

* wip: first table header section ([`0f8d9ef`](https://github.com/swysocki/gpt-image/commit/0f8d9ef1803a454776560bad1b13c30b05ff44a5))

* Initial commit ([`fc1523c`](https://github.com/swysocki/gpt-image/commit/fc1523c0a13898a72e12ed6fd20c4f52f4e9a6ee))
