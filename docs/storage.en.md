> 🇧🇷 [Português](storage.md) · 🇬🇧 **English**

# Storage and partition layout

The console **boots exclusively from the microSD**. There is no eMMC or NAND holding a recovery system: if the card is lost or corrupted and there is no backup, the console cannot be brought back.

## Rule number one

> **Take a bit-for-bit backup of the original SD before any experiment.**

A file-level backup (copy/paste) **is not enough**. Boot depends on the card's physical layout, including raw areas outside any filesystem.

```bash
# On a PC, with the SD inserted — replace /dev/sdX with the correct device.
# Check the target TWICE: pointing at the wrong disk destroys data.
sudo dd if=/dev/sdX of=backup-sd-original.img bs=4M status=progress conv=sync,noerror
sha256sum backup-sd-original.img > backup-sd-original.img.sha256
```

Keep the image **and** the hash in at least two different places.

## Partition layout

Reference from the autopsy (revision V1.0) — compare against your own media before assuming it is identical:

| Partition | Type | Approx. size | Contents |
|---|---|---|---|
| `img1` | FAT32 | large | ROMs, saves |
| `img2` | FAT16 | ~32 MB | `magic.bin`, boot resources |
| `img5` | raw | ~16 MB | U-Boot configuration |
| `img6` | bootimg | ~32 MB | Android bootimg (kernel + ramdisk) |
| `img7` | squashfs | ~768 MB | EmuELEC SYSTEM (read-only) |
| `img8` | rw overlay | ~1.5 GB | userdata, configs, cores |

Points that usually catch out first-timers:

- **`img5` is raw**: it has no filesystem. Graphical partitioning tools treat it as "unallocated space" and destroy it without warning.
- **`img7` is squashfs**: read-only by design. System changes live in the `img8` overlay.
- **Order and offsets matter** — see [boot-chain.en.md](boot-chain.en.md).

## How to document your own media

On the console:

```bash
mkdir -p dumps/bootlogs
cat /proc/cpuinfo   > dumps/bootlogs/cpuinfo.txt
uname -a            > dumps/bootlogs/uname.txt
dmesg               > dumps/bootlogs/dmesg.txt
ls -la /lib/modules > dumps/bootlogs/modules.txt
```

On a PC, with the SD inserted:

```bash
mkdir -p dumps/partitions
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINT > dumps/partitions/lsblk.txt
blkid                                               > dumps/partitions/blkid.txt
sudo fdisk -l /dev/sdX                              > dumps/partitions/fdisk.txt
```

> The `dumps/` folder does **not** yet exist in this repository — the commands above create it. Text output can be committed; full binary SD images cannot.

## What never to do

- Format the original SD, even "just one partition"
- Repartition with a new layout
- Flash a generic EmuELEC image over it
- Expand/move partitions with a graphical tool

Any of these almost always results in a permanent brick.
