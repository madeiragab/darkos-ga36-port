> 🇧🇷 [Português](boot-chain.md) · 🇬🇧 **English**

# Boot chain

Understanding this chain is a prerequisite for any modification. Each link depends rigidly on the previous one — the Allwinner A33 with legacy U-Boot is sensitive to the **physical layout** of the SD card, not just to the contents of the partitions.

## Overview

Offsets confirmed by reading the image directly — method in
[image-autopsy.en.md](image-autopsy.en.md).

```text
BROM (SoC internal ROM, immutable)
   │  looks for the bootloader at sector 16 of the microSD
   ▼
boot0 "eGON.BT0"                          @0x00002000  (sector 16, 32 KB)
   │  brings up DRAM using parameters from its own header
   ▼
U-Boot 2017.09                            @0x01320000  (~20 MB)
   │  vendor build: -g05bceb2-dirty #lxl (Jul 14 2025)
   ▼
script.bin (Allwinner legacy)             @0x01366000  (19.40 MB)
   │  GPIO, clocks, display, UART, PMIC — 78 sections
   ▼
U-Boot environment                        @0x04400000  (68 MB)
   │  assembles the bootargs; defines root= and disk=
   ▼
boot.img (Android format)                 @0x05400000  (84 MB)
   │  kernel 12.60 MB @0x40008000 + initramfs 2.90 MB gzip
   ▼
Linux sunxi 3.4.39 kernel
   │  mounts /flash (mmcblk0p7) and /storage (mmcblk0p8)
   ▼
EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
```

> Correction relative to earlier versions of this document: `script.bin` is
> **not** in the `Volumn` FAT16 partition. It lives in the raw area next to
> U-Boot. That FAT16 holds only fonts, `bootlogo.bmp` and `magic.bin`.

## Why each link matters

### BROM
Burned into silicon, cannot be altered. It looks for the bootloader at a fixed offset on the card — this is why **recreating the SD with an ordinary partitioner breaks boot** even when every file is present.

### U-Boot
Lives in a **raw** partition (no filesystem), with board-specific environment and parameters. It loads `boot.img` in Android format.

> Generic or modern U-Boot is **not compatible** without deep adaptation.

### script.bin / magic.bin
The conceptual equivalent of a Device Tree, in an old proprietary format — details in [device-tree.en.md](device-tree.en.md). Without it: RAM may fail to initialise, the screen stays off, and boot fails **silently**, with no error message.

### bootimg
Android format (kernel + ramdisk packed together). It is neither a bare `zImage` nor a `uImage` — tools expecting those formats are of no use here.

### Kernel
Legacy Linux sunxi (3.4.x). See [kernel.en.md](kernel.en.md).

## Practical implications

| If you… | Likely result |
|---|---|
| Repartition the SD with a new layout | Brick — the BROM cannot find U-Boot |
| Flash a public EmuELEC image | Does not boot (kernel incompatible with the A33) |
| Swap only the kernel, keeping script.bin | Silent failure if the kernel does not understand the legacy format |
| Lose the original SD without a backup | Console unusable |

## U-Boot environment

Extracted from `0x04400000`. This is what builds the kernel command line —
the `boot.img` header has an **empty** `cmdline`.

```
bootdelay=0
bootcmd=run setargs_mmc boot_normal
console=ttyS2,115200
mmc_root=/dev/mmcblk0p7
disk=/dev/mmcblk0p8
init=/init
loglevel=0
boot_normal=sunxi_flash read 40007800 boot;boota 40007800
```

Two consequences that matter:

1. **`boot_normal` uses `sunxi_flash`**, i.e. Allwinner's proprietary
   partition table — not the MBR. The MBR exists in parallel, for the
   kernel. This is why repartitioning with an ordinary tool breaks boot even
   when every file is still present.
2. **`loglevel=0` and `bootdelay=0`**: boot is silent by design. Any failure
   shows up as a mute black screen, indistinguishable from a dead device.

## Documentation status

| Link | State |
|---|---|
| Existence and order of the chain | Confirmed |
| Exact offsets of each stage | ✅ **Confirmed** — see diagram above |
| Contents of the U-Boot environment | ✅ **Confirmed** |
| Serial console pins | ✅ **PB0/PB1 @115200** — see [serial-console.en.md](serial-console.en.md) |
| Full boot log over serial | **Pending** — requires wiring the adapter |
| Access to the U-Boot prompt | **Pending** — `bootdelay=0` suggests no window |

Primary source of the artefacts:
[../reference/autopsy/files.en.md](../reference/autopsy/files.en.md) and
[image-autopsy.en.md](image-autopsy.en.md).
