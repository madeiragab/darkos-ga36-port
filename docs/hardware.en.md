> 🇧🇷 [Português](hardware.md) · 🇬🇧 **English**

# Hardware — GA36-MB (V1.1) — local documentation

**Purpose:** gather, concisely and verifiably, everything we know about the board of the console you opened (GA36-MB V1.1).
This file is operational: update it whenever something new is confirmed (photos, dumps, readings).

---

## Metadata

```text
Board:    GA36-MB
Revision: V1.1 (2025-10-25)
SoC:      Allwinner A33
OS_stock: EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
Boot:     microSD (bootimg + script.bin)
State:    working boot, SD backup taken
```

---

## Identification and short summary

- **Board:** `GA36-MB`
- **Revision confirmed on this unit:** **V1.1** (`GA36-MB V1.1-20251025`) — confirmed by the PCB silkscreen.
- **Actual SoC (behaviour-confirmed):** Allwinner A33 (ARM Cortex-A7, quad-core).
- **Important note on remarking:** the chip package may carry silkscreen indicating another vendor (e.g. Rockchip), but boot/kernel/GPU behaviour confirms an Allwinner A33 (see the "Evidence" section).
- **Stock firmware:** EmuELEC 4.7 — custom build for the A33.
- **Boot:** the image uses the Android `bootimg` format (kernel + ramdisk) and **script.bin** (Allwinner legacy) — **not** a standard DTB.

---

## Photos

Take exactly these photos, without disassembling more than necessary:

- `images/pcb_front.jpg` — the whole board (layout reference)
- `images/soc_allwinner_a33.jpg` — close-up of the SoC (silkscreen reading)
- `images/ram_ddr_chips.jpg` — close-up of the RAM chips (silkscreen reading)
- `images/serial_pads.jpg` — TX/RX/GND pads (or the suspected area)
- `images/display_fpc.jpg` — display FPC connector

Add short captions to the images in the repository (e.g. `soc_allwinner_a33.jpg — silkscreen read: ...`).

---

## Identified components (current state)

- **SoC:** Allwinner A33 — CONFIRMED by logs and system behaviour.
- **GPU:** Mali-400 — detected in the EmuELEC logs.
- **Memory:** 2 × DDR3 chips (model reading pending).
- **Storage:** microSD slot (boots from SD).
- **Display:** FPC interface (timings unconfirmed).
- **Inputs:** 2 analog sticks + buttons (GPIO) — mapping undocumented.
- **Audio:** mono speaker (enable pin may depend on the DTB/script.bin).
- **Debug/serial pads:** there is a pad area near the top — confirm TX/RX/GND with a macro photo.

---

## Technical evidence confirming Allwinner A33

- `/proc/cpuinfo` showing `sun8i` / an Allwinner identifier.
- `uname -a` indicating a sunxi kernel (e.g. `3.4.39` in the dump).
- `dmesg` reporting Mali-400 or `sunxi` strings.

> If the three outputs above are present, assume remarking: the chip silkscreen is NOT a definitive source.

---

## Partition layout

(save the output under `dumps/partitions/`)

Example (autopsy V1.0 — compare against your own media):

| Partition | Type | Approx. size | Contents |
|---|---|---|---|
| `img1` | FAT32 | large | ROMs / saves |
| `img2` | FAT16 | ~32 MB | `magic.bin` / boot resources |
| `img5` | raw | ~16 MB | U-Boot config (raw) |
| `img6` | bootimg | ~32 MB | Android bootimg (kernel + ramdisk) |
| `img7` | squashfs | ~768 MB | EmuELEC SYSTEM |
| `img8` | rw overlay | ~1.5 GB | userdata / configs / cores |

**WARNING:** do not overwrite or format these partitions without a bit-for-bit backup.

---

## Essential commands

Run **exactly** these commands and commit the output.

On the console:

```bash
mkdir -p dumps/bootlogs dumps/partitions
cat /proc/cpuinfo   > dumps/bootlogs/cpuinfo.txt
uname -a            > dumps/bootlogs/uname.txt
dmesg               > dumps/bootlogs/dmesg.txt
ls -la /lib/modules > dumps/bootlogs/modules.txt
```

On a PC with the SD inserted (replace `/dev/sdX` with your device):

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINT > dumps/partitions/lsblk.txt
blkid                                               > dumps/partitions/blkid.txt
sudo fdisk -l /dev/sdX                              > dumps/partitions/fdisk.txt
```
