> 🇬🇧 **English** · 🇧🇷 [Português](image-autopsy.md)

# Image autopsy (software)

Companion to the physical autopsy in [`reference/autopsy/`](../reference/autopsy/).
Where that one documents the PCB, this one documents the **card contents**:
offsets, structures, configuration and defects, all extracted by directly
reading a 2425 MB recovery image.

**Method:** offline parsing, nothing mounted, no Linux required. Tools in
[`tools/`](../tools/). Every value below has a verifiable offset — nothing
here is inferred from third-party documentation.

**Sample:** `r36s-a33-recovery.img`, 2 543 237 120 bytes.
**Unit:** GA36-MB V1.1 (2025-10-25).

---

## 1. Definitive SoC identification

The silkscreen says RK3326. It is not. Four independent pieces of evidence,
all inside the image:

| Evidence | Offset | Value |
|---|---|---|
| Machine string | 0x01a307e7f | `sun8iw5p1` |
| Machine string | 0x005bb2518 | `sun8iw5` |
| boot.img header name | 0x05400000 | `sun8i` |
| Bootloader signature | 0x00002004 | `eGON.BT0` |
| Kernel load address | header | `0x40008000` (ARM 32-bit) |

`sun8iw5p1` is Allwinner's internal codename for the **A33**. There is no
ambiguity: not A133 (`sun50iw10`), not H3 (`sun8iw7`), not Rockchip.

**Consequence:** Cortex-A7, **ARMv7 32-bit**. Any software requiring ARM64
(box64, aarch64 builds) is ruled out by architecture, not by performance.

---

## 2. Memory — DRAM parameters from boot0

The eGON header at `0x2000` carries the `dram_para` structure boot0 uses to
bring up memory. These are the values the board actually runs:

| Field | Offset | Value |
|---|---|---|
| `dram_clk` | 0x2038 | 552 MHz |
| `dram_type` | 0x203C | 3 (DDR3) |
| `dram_zq` | 0x2040 | `0x00003bbb` |
| `dram_odt_en` | 0x2044 | 1 |
| `dram_para1` | 0x2048 | `0x10f20200` |
| `dram_para2` | 0x204C | 0 |
| `dram_mr0` | 0x2050 | `0x1840` |
| `dram_mr1` | 0x2054 | `0x40` |
| `dram_mr2` | 0x2058 | `0x8` |
| `dram_mr3` | 0x205C | 0 |

`dram_para1 = 0x10f20200` together with the board's 2 DDR3 chips decodes to
15 rows × 10 columns × 8 banks × 32-bit bus = **1 GB**.

> Decoding the `para1` encoding is an inference and should be confirmed with
> `free -h` or `dmesg | grep -i memory` on the unit.

**Actually usable RAM is lower.** The bootargs reserve:

```
ion_cma_1g=176m  ion_carveout_1g=150m  coherent_pool=4m
```

Roughly **850 MB** is left for the system.

---

## 3. Boot chain — exact offsets

Closes the "exact offsets for each stage" item in
[boot-chain.en.md](boot-chain.en.md).

| Stage | Offset | Size | Detail |
|---|---|---|---|
| boot0 (`eGON.BT0`) | `0x00002000` (sector 16) | 32 768 B | `pub_head_size = 48` |
| U-Boot | `~0x01320000` (20.06 MB) | — | `U-Boot 2017.09-g05bceb2-dirty #lxl (Jul 14 2025 - 11:58:12 +0800)` |
| `script.bin` | `0x01366000` (19.40 MB) | — | 78 sections |
| U-Boot environment | `0x04400000` (68 MB) | — | see section 4 |
| `boot.img` | `0x05400000` (84 MB) | — | Android header |

### `boot.img` header

| Field | Value |
|---|---|
| `page_size` | 2048 |
| kernel | 13 213 848 B (12.60 MB) @ `0x40008000` |
| ramdisk | 3 040 904 B (2.90 MB) @ `0x41000000` |
| second | 0 |
| `tags_addr` | `0x40000100` |
| `name` | `sun8i` |
| `cmdline` | **empty** |
| ramdisk | `0x0609b000`, gzip (`1f8b0800`) |

The empty header `cmdline` is why the bootargs come entirely from the
U-Boot environment.

---

## 4. U-Boot environment

Closes the "U-Boot environment contents" item. Extracted from
`0x04400000`:

```
bootdelay=0
bootcmd=run setargs_mmc boot_normal
console=ttyS2,115200
nand_root=/dev/nandd
mmc_root=/dev/mmcblk0p7
init=/init
disk=/dev/mmcblk0p8
loglevel=0
setargs_mmc=setenv bootargs console=${console} root=${mmc_root} init=${init} disk=${disk} ion_cma_512m=8m ion_cma_1g=176m ion_carveout_512m=0m ion_carveout_1g=150m coherent_pool=4m loglevel=${loglevel} partitions=${partitions}
boot_normal=sunxi_flash read 40007800 boot;boota 40007800
```

What matters here:

- `boot_normal` uses **`sunxi_flash`**, i.e. Allwinner's proprietary
  partition table — not the MBR. The MBR exists in parallel, for the kernel.
- `loglevel=0` and `bootdelay=0`: total silence during boot. See
  [serial-console.en.md](serial-console.en.md) for why this is the project's
  single biggest practical obstacle.
- `disk=/dev/mmcblk0p8` and `root=/dev/mmcblk0p7` are **correct** and match
  the real layout.

---

## 5. Partition layout

Replaces the approximate table previously in
[storage.en.md](storage.en.md).

### Primary MBR

| Slot | Type | Start (LBA) | Sectors | Contents |
|---|---|---|---|---|
| p1 | `0x0b` FAT32 | 4 956 161 | 11 099 (5.42 MB) | ROMs — **see defect below** |
| p2 | `0x06` FAT16 | 73 728 | 65 536 (32 MB) | `Volumn` — boot flag `0x80` |
| p3 | `0x85` extended | 1 | 4 956 160 (2420 MB) | vendor-area container |

### Logical partitions (inside p3)

| Device | Start (LBA) | Size | Filesystem | Role |
|---|---|---|---|---|
| `mmcblk0p5` | 139 264 (68 MB) | 16 MB | raw | U-Boot environment |
| `mmcblk0p6` | 172 032 (84 MB) | 32 MB | raw | `boot.img` |
| `mmcblk0p7` | 237 568 (116 MB) | 768 MB | FAT16 `EMUELEC` | `/flash` — holds `SYSTEM` |
| `mmcblk0p8` | 1 810 432 (884 MB) | 1536 MB | ext4 | `/storage` |

### Relevant contents

- **p7** (`/flash`): `SYSTEM` (425 447 424 B) and `LOW_PWR.BMP`.
  `SYSTEM` is **lzo** squashfs, 405.74 MB, block 524 288, 12 276 inodes,
  built **2025-08-22 12:45**.
- **p2** (`Volumn`): `font32.sft`, `font24.sft`, `bootlogo.bmp`,
  `magic.bin` (512 B), `bat/`.
- **p8** (`/storage`): ext4, block 4096, 98 304 inodes, 256 B inodes.
  `state = clean`, mount count **53**, last check 2025-05-13.

### ext4 compatibility with kernel 3.4

Verified by reading the superblock — this matters because it rules out a
common failure hypothesis:

```
compat    0x0000003c : has_journal, ext_attr, resize_inode, dir_index
incompat  0x000002c2 : filetype, extents, 64bit, flex_bg
ro_compat 0x0000006b : sparse_super, large_file, huge_file, dir_nlink, extra_isize
```

No feature outside what Linux 3.4 supports. `/storage` **mounts read-write**
without restriction.

---

## 6. Defects found in the image

### 6.1 MBR is off by one sector on p1

MBR entry 1 points at **LBA 4956161**. The actual FAT32 boot sector sits at
**LBA 4956160**. Beyond being wrong, 4956161 is not 2048-aligned, while
4956160 is exactly `2048 × 2420`.

Effect: Windows formats a fresh filesystem at the wrong offset and
misaligns the partition, a permanent performance penalty on SD.

### 6.2 Truncated ROM partition

The distributed recovery image declares p1 as **11 099 sectors (5.42 MB)**,
even though the internal FAT32 BPB declares 48 779 MB. Anyone flashing that
image gets an unusable ROM partition and EmulationStation fails with:

```
we can't find any systems
```

Fix: rewrite the MBR entry and generate a fresh FAT32 spanning the card.
See [`tools/`](../tools/).

### 6.3 `Volumn` lies about its own size — brick risk

**This is the most dangerous defect of the set.**

| Source | Declared size |
|---|---|
| MBR entry (p2) | **32 MB** |
| BPB inside the partition | **128 MB** |

Windows mounts the volume using the **BPB**, so it sees 128 MB and treats
the 36 MB–164 MB range of the card as writable. Inside that range are:

- `boot.img` at **84 MB**
- `SYSTEM` at **116 MB**

Any Windows write past the real 32 MB lands **on top of the boot chain**.
And Windows writes on its own: it creates `System Volume Information` on
mount.

> **Never copy anything to the `Volumn` partition. Never let Windows
> "repair" that volume.** If it offers to format, cancel.

### 6.4 `fsck.auto` does not exist in the initramfs

`init` calls, without specifying a type:

```sh
fsck -T -M -p -a $RUN_FSCK_DISKS
```

Type detection fails and it looks for `/sbin/fsck.auto`. The initramfs ships
`e2fsck`, `fsck.ext2`, `fsck.fat`, `fsck.exfat` — but **no `fsck.ext4` and
no `fsck.auto`**. The result is recorded in the image's own `init.log`:

```
fsck: fsck.auto: No such file or directory
fsck: fsck.auto: No such file or directory
mount: mounting /run on /sysroot/run failed: Invalid argument
```

`/storage` is never checked after an unclean shutdown.

---

## 7. Tools

All in [`tools/`](../tools/), pure Python, read-only except where noted.
They run on Windows without WSL.

| Tool | Purpose |
|---|---|
| `ext4_reader.py` | Reads ext4 (extents, inodes, directories) straight from a raw image |
| `scriptbin_parse.py` | Locates and parses legacy Allwinner `script.bin` |
| `partition_map.py` | MBR plus the extended partition chain |
| `boot_header.py` | Android `boot.img` header plus superblock scan |
| `uboot_env.py` | Extracts the U-Boot environment |
| `verify_card.py` | Byte-by-byte card vs image comparison (read-only) |

---

## 8. What this changes about project scope

[kernel.en.md](kernel.en.md) argued that recompiling was out of reach for
lack of information about the board. Much of that information now exists:

| Prerequisite | Before | Now |
|---|---|---|
| Verified backup | ✅ | ✅ |
| Boot chain mapped | ❌ | ✅ exact offsets |
| U-Boot environment | ❌ | ✅ complete |
| Serial access | ❌ | ✅ PB0/PB1 identified |
| Device tree source data | ❌ | ✅ LCD, PMIC, UART, DRAM |
| New device tree and kernel | ❌ | ❌ **remaining work** |
| Recovery procedure | partial | partial |

What is left became concrete and enumerable instead of unknown. See
[device-tree.en.md](device-tree.en.md) for the extracted values and
[serial-console.en.md](serial-console.en.md) for the next practical step.
