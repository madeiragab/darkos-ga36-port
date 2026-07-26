> 🇧🇷 [Português](reference_autopsy.md) · 🇬🇧 **English**

# Reference: R36S console clone — technical autopsy (baseline)

**Primary source:**
https://github.com/phaseloop/R36S-console-clone---GA36-MB-V1.0-20250730

A public repository containing a technical autopsy and a recovery image for the R36S clone console based on the GA36-MB board.

## 1. Identification of the analysed board

- **Board model:** GA36-MB
- **Revision:** V1.0
- **Silkscreen:** `GA36-MB V1.0-20250730`

This board is the same physical model found in this project, and therefore serves as a direct reference.

## 2. Actual SoC and architecture

- **Actual SoC identified:** Allwinner A33
- **GPU detected at boot:** Mali-400 (definitive evidence)
- **Architecture:** ARMv7 (sunxi)

Although the physical chip marking indicates RK3326, this is false labelling. The boot logs confirm an Allwinner A33 unambiguously.

## 3. Kernel and boot

- **Reported kernel:** Linux version 3.4.39
- **Family:** Linux-sunxi (old kernel, pre-mainline)
- **Boot format:** Android-style `boot.img` (kernel + ramdisk)

Important characteristics:

- Does not use a modern DTB
- Uses `script.bin` / `magic.bin` (Allwinner legacy format)
- Bootloader and kernel follow the old Android/sunxi ecosystem pattern

## 4. Partition layout (from the original dump)

| Partition | Type | Size | Function |
|---|---|---|---|
| `img1` | FAT32 | ~47.6 GB | ROMs |
| `img2` | FAT16 | 32 MB | `script.bin`, `magic.bin`, boot resources |
| `img5` | raw | 16 MB | U-Boot configuration |
| `img6` | bootimg | 32 MB | Kernel + ramdisk (Android `boot.img`) |
| `img7` | squashfs | 768 MB | SYSTEM (customized EmuELEC) |
| `img8` | RW overlay | ~1.5 GB | Userdata / overlay |

**Critical note:** this layout does not follow modern standards and depends on old U-Boot.

## 5. Operating system

- **Base:** heavily customized EmuELEC 4.7
- **Origin:** LibreELEC / Android hybrid
- **Root filesystem:** squashfs (SYSTEM)

Characteristics:

- Old Android/sunxi kernel
- Custom ramdisk
- Incompatible with official public EmuELEC builds
- Generic images do not boot

## 6. Critical technical observations

- The system uses a "franken-kernel" (sunxi + Android + LibreELEC)
- `script.bin` acts as a legacy DTB
- Conversion to a modern DTB is possible, but non-trivial
- Without a working original SD, there is no reliable public recovery method

## 7. Practical conclusions (project baseline)

- This hardware does not support modern images without a specific port
- Reusing the kernel + `script.bin` from the autopsy is the safest path
- Porting to a modern kernel requires:
  - `script.bin` → DTB conversion
  - deep bootloader adjustments
  - probable loss of compatibility

## 8. Use of this document in the project

This file is the project's primary technical reference. Any modification attempt must:

1. Compare partitions
2. Compare `boot.img`
3. Compare `script.bin`

**Never replace kernel/boot without cross-validating against this autopsy.**
