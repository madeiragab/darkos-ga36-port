> 🇧🇷 [Português](boot-chain.md) · 🇬🇧 **English**

# Boot chain

Understanding this chain is a prerequisite for any modification. Each link depends rigidly on the previous one — the Allwinner A33 with legacy U-Boot is sensitive to the **physical layout** of the SD card, not just to the contents of the partitions.

## Overview

```text
BROM (SoC internal ROM, immutable)
   │  looks for the bootloader at a fixed microSD offset
   ▼
U-Boot (raw partition, ~16 MB)
   │  board-specific; understands the old SD layout
   │  reads the hardware configuration
   ▼
script.bin / magic.bin (Allwinner legacy)
   │  initialises DRAM, GPIO, clocks, display
   ▼
bootimg (Android format, ~32 MB)
   │  contains kernel + ramdisk
   ▼
Linux sunxi 3.4.x kernel
   │  mounts the system partitions
   ▼
EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
```

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

## Documentation status

| Link | State |
|---|---|
| Existence and order of the chain | Confirmed by the reference autopsy |
| Exact offsets of each stage | **Pending** — requires dumping and analysing the first KB of the SD |
| Contents of the U-Boot environment | **Pending** |
| Full boot log over serial | **Pending** — requires identifying the TX/RX/GND pads |

Primary source of the artefacts: [../reference/autopsy/files.md](../reference/autopsy/files.en.md).
