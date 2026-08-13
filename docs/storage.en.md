> 🇬🇧 **English** · 🇧🇷 [Português](storage.md)

# Storage and partition layout

The console **boots exclusively from the microSD**. There is no eMMC or NAND
recovery system: if the card is lost or corrupted and there is no backup,
the console cannot be brought back.

## Rule number one

> **Take a bit-for-bit backup of the original SD before any experiment.**

A file-level backup (copy/paste) **is not enough**. Boot depends on the
card's physical layout, including raw areas outside any filesystem.

```bash
# On the PC, with the SD inserted — replace /dev/sdX with the right device.
# Check the target TWICE: pointing at the wrong disk destroys data.
sudo dd if=/dev/sdX of=backup-sd-original.img bs=4M status=progress conv=sync,noerror
sha256sum backup-sd-original.img > backup-sd-original.img.sha256
```

Keep the image **and** the hash in at least two different places.

---

## ⚠️ Windows-specific hazard

**This is the most likely way to destroy the console by accident, and it
does not require you to knowingly do anything wrong.**

The `Volumn` partition declares contradictory sizes:

| Source | Size |
|---|---|
| MBR entry | **32 MB** |
| BPB inside the partition | **128 MB** |

Windows mounts the volume using the **BPB**. It believes it may write from
36 MB to 164 MB of the card. Inside that range are:

- **`boot.img` at 84 MB**
- **`SYSTEM` at 116 MB**

And Windows writes on its own: mounting the volume creates
`System Volume Information`.

**Practical rules:**

- Never copy anything to the `Volumn` partition (shows up as `D:` or
  similar).
- If Windows asks "you need to format the disk", click **Cancel**.
- Never accept "repairing" that volume.
- When flashing an image, leave the disk unmounted and remove the card
  without letting Windows remount it. Disabling automount helps:

```
diskpart
automount disable
```

(reversible with `automount enable`)

To find out whether the damage already happened, use
[`tools/verify_card.py`](../tools/verify_card.py) — it is read-only.

---

## Partition layout (confirmed)

Measured on the V1.1 unit's recovery image. Method and offsets in
[image-autopsy.en.md](image-autopsy.en.md).

### Primary MBR

| Slot | Type | Start (LBA) | Size | Contents |
|---|---|---|---|---|
| p1 | `0x0b` FAT32 | 4 956 161 | 5.42 MB¹ | ROMs, saves |
| p2 | `0x06` FAT16 | 73 728 | 32 MB | `Volumn` — fonts, bootlogo, `magic.bin` |
| p3 | `0x85` extended | 1 | 2420 MB | vendor-area container |

¹ size in the distributed recovery image — see "Defects" below.

### Logical partitions (inside p3)

| Device | Start | Size | Filesystem | Role |
|---|---|---|---|---|
| `mmcblk0p5` | 68 MB | 16 MB | raw | U-Boot environment |
| `mmcblk0p6` | 84 MB | 32 MB | raw | `boot.img` (kernel + initramfs) |
| `mmcblk0p7` | 116 MB | 768 MB | FAT16 `EMUELEC` | `/flash` — holds `SYSTEM` |
| `mmcblk0p8` | 884 MB | 1536 MB | ext4 | `/storage` |

U-Boot references these partitions explicitly:
`root=/dev/mmcblk0p7`, `disk=/dev/mmcblk0p8`.

Things that catch first-timers:

- **p5 and p6 are raw**: no filesystem. Graphical partitioning tools treat
  them as "unallocated space" and destroy them without warning.
- **`SYSTEM` is read-only squashfs** (405 MB, lzo-compressed). System
  changes live on the ext4 at `mmcblk0p8`.
- **p2 and p3 overlap** in the table — p2 sits inside p3's range. It ships
  that way and it works; do not "fix" it.
- **Order and offsets matter** — see [boot-chain.en.md](boot-chain.en.md).

---

## Defects in the distributed recovery image

Beyond the `Volumn` problem above:

**Truncated ROM partition.** The MBR entry declares 11 099 sectors
(5.42 MB) while the internal BPB declares 48 779 MB. Anyone flashing the
image gets an unusable partition and EmulationStation fails with
`we can't find any systems`.

**MBR off by one sector.** The entry points at LBA 4956161; the actual
FAT32 boot sector is at 4956160 — which is also the 2048-aligned value.

Fix: rewrite the MBR entry (start 4956160, size to the end of the card) and
generate a fresh FAT32 labelled `EEROMS`. Windows will not format FAT32
above 32 GB with native tools, so this needs `mkfs.vfat -F 32` on Linux or
a purpose-built generator.

After fixing, EmulationStation still hides any system whose folder is
empty — at least one ROM is required. The list of 106 expected folders is
in `/storage/.config/emulationstation/es_systems.cfg`, readable without
mounting anything:

```bash
python tools/ext4_reader.py IMAGE 0x37400000 \
  cat:/.config/emulationstation/es_systems.cfg
```

---

## Documenting your own media

Offline, from an image or from the card itself:

```bash
python tools/partition_map.py backup-sd-original.img
python tools/boot_header.py  backup-sd-original.img
python tools/uboot_env.py    backup-sd-original.img
```

On the console:

```bash
mkdir -p dumps/bootlogs
cat /proc/cpuinfo   > dumps/bootlogs/cpuinfo.txt
uname -a            > dumps/bootlogs/uname.txt
dmesg               > dumps/bootlogs/dmesg.txt
free -h             > dumps/bootlogs/meminfo.txt
ls -la /lib/modules > dumps/bootlogs/modules.txt
```

> The `dumps/` folder does **not** exist in this repository yet — the
> commands above create it. Text output can be versioned; full binary SD
> images cannot.

## What never to do

- Format the original SD, even "just one partition"
- Copy files to the `Volumn` partition
- Let Windows "repair" any volume on the card
- Repartition with a new layout
- Flash a generic EmuELEC image over it
- Expand/move partitions with a graphical tool

Any of these almost always ends in a permanent brick.
