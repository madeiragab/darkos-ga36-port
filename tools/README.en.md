> 🇬🇧 **English** · 🇧🇷 [Português](README.md)

# Analysis tools

Scripts used to produce [`docs/image-autopsy.en.md`](../docs/image-autopsy.en.md).

**Pure Python 3, no external dependencies.** They run on Windows without
WSL, and on Linux without installing anything. They exist because the usual
tools (`losetup`, `mount`, `unsquashfs`, sunxi-tools) are unavailable on
Windows, and mounting the image on Linux was unnecessary just to read it.

**All of them are read-only.** None writes to the image or the card.

## Usage

Each takes the image (or device) path as an argument.

```bash
# full partition map: MBR + extended chain + bootloader
python partition_map.py r36s-a33-recovery.img

# boot.img header + superblock scan
python boot_header.py r36s-a33-recovery.img

# U-Boot environment
python uboot_env.py r36s-a33-recovery.img

# script.bin: list sections
python scriptbin_parse.py r36s-a33-recovery.img
# ... then dump the interesting ones
python scriptbin_parse.py r36s-a33-recovery.img uart_para lcd0_para power_sply

# ext4 /storage: list and read files without mounting
python ext4_reader.py r36s-a33-recovery.img 0x37400000 ls:/
python ext4_reader.py r36s-a33-recovery.img 0x37400000 cat:/.config/EE_VERSION
```

## Comparing card against image

`verify_card.py` is the only one that touches hardware, and it **only
reads**. Use it to answer "was the boot chain corrupted?" without risking
making things worse.

```bash
# Linux
sudo python3 verify_card.py r36s-a33-recovery.img /dev/sdX
```

```powershell
# Windows, PowerShell as Administrator
python verify_card.py r36s-a33-recovery.img \\.\PhysicalDrive1
```

It checks the four critical structures (boot0, boot.img, SYSTEM, ext4),
compares everything byte by byte and classifies each difference by region.

> Differences inside `ext4 /storage` are **normal** after any boot —
> EmuELEC writes logs and configuration. Differences in `boot.img` or the
> raw area are **not**, and point to the problem described in
> [image-autopsy.en.md](../docs/image-autopsy.en.md) §6.3.

## Offsets for this board

These apply to the GA36-MB V1.1 recovery image. Confirm with
`partition_map.py` before assuming your media is identical.

| Offset | Contents |
|---|---|
| `0x00002000` | boot0 (`eGON.BT0`), sector 16 |
| `0x01320000` | U-Boot 2017.09 |
| `0x01366000` | `script.bin` |
| `0x04400000` | U-Boot environment |
| `0x05400000` | `boot.img` |
| `0x07400000` | FAT16 `EMUELEC` (`/flash`, holds `SYSTEM`) |
| `0x37400000` | ext4 (`/storage`) |
| `0x97400000` | FAT32 (ROMs) |

## Known limitations

- `ext4_reader.py` cannot walk hash-tree directories when `rec_len` is
  corrupted; on a healthy image it works.
- `scriptbin_parse.py` decodes word, string and GPIO types. Multi-word
  values show up as "not decoded".
- `SYSTEM` is a squashfs compressed with **lzo**, which Python's stdlib
  cannot decompress. Reading its contents requires `unsquashfs` built with
  lzo support.
