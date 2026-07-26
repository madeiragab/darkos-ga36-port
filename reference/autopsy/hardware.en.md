> 🇧🇷 [Português](hardware.md) · 🇬🇧 **English**

# Hardware — GA36-MB (R36S clone with Allwinner A33)

This document describes the physical hardware of the R36S clone handheld console based on the **GA36-MB** board, as observed through direct visual inspection and comparison against the reference technical autopsy.

The focus is to **document what actually exists**, not what the manufacturer claims.

---

## Overview

- **Product:** R36S-style handheld console (clone)
- **Board:** GA36-MB
- **Known revisions:**
  - V1.0 (`GA36-MB V1.0-20250730`)
  - V1.1 (`GA36-MB V1.1-20251025`)
- **Current state:** working with the original system
- **Boot:** from microSD card

---

## SoC (System on Chip)

- **Actual SoC:** Allwinner A33
- **Architecture:** ARMv7 (quad-core Cortex-A7)
- **Typical frequency:** ~1.0–1.2 GHz (not confirmed against a real clock reading)
- **GPU:** ARM Mali-400 MP2
- **Process:** legacy (sunxi)

⚠️ **Critical observation**
The chip package carries false markings indicating **RK3326**. Boot logs and GPU identification confirm, unambiguously, an Allwinner A33.

---

## RAM

- **Type:** DDR3 (likely)
- **Estimated capacity:** 512 MB (not confirmed via dump)
- **Configuration:** defined via `script.bin` / `magic.bin`

⚠️ DRAM initialisation depends heavily on the legacy Allwinner configuration. Without that file, the system does not boot.

---

## Storage

### microSD card

- **Role:** boot + system + ROMs
- **Layout:** non-standard (Allwinner legacy)
- **Dependency:** high — the original SD is critical for recovery

### Partitions (summary)

- FAT16: boot/configuration (`script.bin`, resources)
- bootimg: kernel + ramdisk (Android-style)
- squashfs: system (custom EmuELEC)
- RW overlay: user data
- raw partitions: U-Boot / environment

---

## Display

- **Type:** LCD (exact resolution not confirmed)
- **Interface:** RGB / parallel (likely)
- **Initialisation:** via `script.bin`
- **State:** working with the original system

⚠️ The display does not initialise without the correct boot configuration.

---

## Controls and input

- **D-Pad:** physical
- **Action buttons:** physical
- **Triggers:** physical
- **Start / Select:** physical
- **Interface:** GPIO (sunxi)

Mapping is handled by the system and its overlays.

---

## Audio

- **Output:** internal speaker + headphones (likely)
- **Codec:** integrated or simple external part (not identified)
- **State:** working

---

## Connectivity

- **USB:** present (probably the A33's USB OTG)
- **Wi-Fi:** not identified / not present
- **Bluetooth:** not identified / not present

---

## Power

- **Battery:** Li-ion / Li-Po (internal)
- **Management:** dedicated circuit (not identified)
- **Charging:** over USB

---

## Bootloader

- **Type:** legacy U-Boot (sunxi)
- **Location:** raw partition on the SD
- **Compatibility:** specific to GA36 / A33
- **Replacement:** high risk without a working dump

---

## Serial interface (UART)

- **Pads identified on the board:**
  - GND
  - TX
  - RX
- **Logic level:** 3.3 V (assumed)
- **Use:** not explored in this project

⚠️ A serial console would give detailed boot logs, but it is not an immediate requirement.

---

## Differences between known revisions

- **V1.0 vs V1.1:**
  - Visual changes in the layout
  - No evidence of an SoC change
  - Kernel and system remain compatible

---

## Known hardware limitations

- Extremely old kernel (Linux 3.4.x)
- Dependence on legacy configuration (`script.bin`)
- Limited GPU (OpenGL ES 2.0)
- Porting to modern systems requires significant work

---

## Technical conclusion

This hardware is a **classic Allwinner A33**, reused in a modern product with misleading labelling.

It is not "mysterious" hardware, but rather:
- poorly documented
- deliberately obfuscated
- technically limited

Any port or modification attempt must respect:
- the existing working kernel
- the legacy bootloader
- the original hardware configuration

Ignoring these points results, almost certainly, in a brick.
