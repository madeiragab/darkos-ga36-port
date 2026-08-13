> 🇧🇷 [Português](hardware.md) · 🇬🇧 **English**

# Hardware — GA36-MB (V1.1) — local documentation

**Purpose:** gather, concisely and verifiably, everything we know about the board of the console you opened (GA36-MB V1.1).
This file is operational: update it whenever something new is confirmed (photos, dumps, readings).

---

## Metadata

```text
Board:     GA36-MB
Revision:  V1.1 (2025-10-25)
SoC:       Allwinner A33 (sun8iw5p1) — Cortex-A7 quad, ARMv7 32-bit
GPU:       Mali-400 (GLES 2.0)
RAM:       1 GB DDR3 @552 MHz (~850 MB usable)
Panel:     640x480, MIPI DSI 2 lanes, jd9366_8inch
PMIC:      AXP22x
Kernel:    Linux 3.4.39 (sunxi legacy)
OS_stock:  EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
Boot:      microSD (Android boot.img + script.bin)
Serial:    UART2 — TX=PB0, RX=PB1, 115200 8N1
State:     working boot, SD backup verified
```

---

## Identification and short summary

- **Board:** `GA36-MB`
- **Revision confirmed on this unit:** **V1.1** (`GA36-MB V1.1-20251025`) — confirmed by the PCB silkscreen.
- **Actual SoC:** **Allwinner A33** (`sun8iw5p1`) — ARM Cortex-A7 quad-core,
  **ARMv7 32-bit**.
- **Note on remarking:** the chip package carries silkscreen indicating
  Rockchip RK3326. That is remarking. See the "Evidence" section.
- **Stock firmware:** EmuELEC 4.7 (`EE_VERSION` = `4.7`), build
  `GA36-UDT-EE-TF-R-20250818` — an unofficial fork adapted to the A33.
- **Boot:** Android `boot.img` format (kernel + ramdisk) and **script.bin**
  (Allwinner legacy) — **not** a standard DTB.

---

## Photos

Already in the repository:

- [`images/pcb_front.jpg`](../images/pcb_front.jpg) — the whole board
- [`images/soc_allwinner_a33.png`](../images/soc_allwinner_a33.png) — close-up of the SoC
- [`images/ram_ddr_chips.png`](../images/ram_ddr_chips.png) — close-up of the RAM chips
- [`images/serial_pads.png`](../images/serial_pads.png) — candidate TX/RX/GND pads

Still missing:

- `images/display_fpc.*` — display FPC connector
- An annotated photo correlating the serial pads with **PB0/PB1** — see
  [serial-console.en.md](serial-console.en.md) for the identification
  method.

---

## Identified components (current state)

| Component | Value | Source of confirmation |
|---|---|---|
| SoC | Allwinner A33 (`sun8iw5p1`), Cortex-A7 quad | image strings, boot.img header |
| GPU | Mali-400 (GLES 2.0, no S3TC) | EmuELEC logs |
| Memory | **1 GB DDR3 @552 MHz**, 2 chips, 32-bit bus | `dram_para` in the eGON header |
| Usable RAM | **~850 MB** (176 MB CMA + 150 MB carveout) | U-Boot bootargs |
| PMIC | **AXP22x** (AXP223 family) | `power_sply` and `lcd_power` in script.bin |
| Display | **640 × 480**, MIPI DSI 2 lanes, `jd9366_8inch` panel | `lcd0_para` in script.bin |
| Backlight | PWM channel 0 @20 kHz | `lcd0_para` |
| Storage | microSD slot (SD-only boot) | — |
| Debug serial | **UART2, TX=PB0, RX=PB1, 115200** | `uart_para` in script.bin |
| Inputs | 2 analog sticks + buttons (GPIO) | **mapping still undocumented** |
| Audio | mono speaker | enable pin not located yet |

PMIC rails (`power_sply`, in mV): `dcdc1`=3000, `dcdc2`=1100, `dcdc3`=1200,
`dcdc4`=0, `dcdc5`=1500, `aldo2`=2500, `aldo3`=3000, `dldo3`=3000.

Details and offsets: [image-autopsy.en.md](image-autopsy.en.md) and
[device-tree.en.md](device-tree.en.md).

---

## Technical evidence confirming Allwinner A33

Confirmed by reading the image directly, without needing console access:

| Evidence | Offset | Value |
|---|---|---|
| Machine string | `0x01a307e7f` | `sun8iw5p1` |
| Machine string | `0x005bb2518` | `sun8iw5` |
| boot.img header name | `0x05400000` | `sun8i` |
| Bootloader signature | `0x00002004` | `eGON.BT0` |
| Kernel version | `0x005a4e899` | `Linux version 3.4.39 (lxl@lxl)` |
| Load address | header | `0x40008000` (ARM 32-bit) |

`sun8iw5p1` is Allwinner's internal codename for the A33 — not A133
(`sun50iw10`), not H3 (`sun8iw7`), not Rockchip.

Additional confirmation on the device:

```bash
cat /proc/cpuinfo    # sun8i / Allwinner identifier
uname -a             # sunxi kernel 3.4.39
free -h              # confirm the 1 GB decoding
dmesg | grep -i mali # Mali-400
```

> The chip silkscreen is **not** a definitive source.

---

## Partition layout

Full, confirmed layout in **[storage.en.md](storage.en.md)**. Summary:

| Device | Offset | Size | Contents |
|---|---|---|---|
| `mmcblk0p1` | 2420 MB | ROMs | FAT32 |
| `mmcblk0p2` | 36 MB | 32 MB | `Volumn` — fonts, bootlogo |
| `mmcblk0p5` | 68 MB | 16 MB | U-Boot environment (raw) |
| `mmcblk0p6` | 84 MB | 32 MB | `boot.img` (raw) |
| `mmcblk0p7` | 116 MB | 768 MB | `/flash` — holds `SYSTEM` |
| `mmcblk0p8` | 884 MB | 1536 MB | `/storage` (ext4) |

> **WARNING:** do not overwrite or format without a bit-for-bit backup. And
> read the Windows warning in [storage.en.md](storage.en.md) — it can write
> over `boot.img` without being asked.

---

## Essential commands

Run **exactly** these and commit the output:

```bash
mkdir -p dumps/bootlogs dumps/partitions
cat /proc/cpuinfo   > dumps/bootlogs/cpuinfo.txt
uname -a            > dumps/bootlogs/uname.txt
dmesg               > dumps/bootlogs/dmesg.txt
free -h             > dumps/bootlogs/meminfo.txt
ls -la /lib/modules > dumps/bootlogs/modules.txt
```

Offline, from an image or the card — no Linux required:

```bash
python tools/partition_map.py IMAGE
python tools/boot_header.py   IMAGE
python tools/uboot_env.py     IMAGE
python tools/scriptbin_parse.py IMAGE lcd0_para uart_para power_sply
```
