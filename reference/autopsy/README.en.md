> 🇧🇷 [Português](README.md) · 🇬🇧 **English**

# Reference technical autopsy — GA36 / R36S clone

This directory contains the **reference technical autopsy** used as the baseline for studying, documenting and possibly porting a system to the R36S clone handheld console based on the **GA36-MB** board.

⚠️ This is NOT original work by this project.
All the detailed technical analysis, dumps and images were produced by the author of the original autopsy, duly credited in [`sources.en.md`](sources.en.md).

This project uses that autopsy **exclusively as a technical reference**.

---

## Purpose of this directory

The goal of this material is to:

- Consolidate reliable information about the real GA36 hardware
- Avoid redundant reverse engineering
- Establish a **proven working baseline**
- Reduce brick risk during future testing

This directory **contains no binaries**, only documentation and references.

---

## Hardware documented by the autopsy

- **Board:** GA36-MB (V1.0 / V1.1)
- **Actual SoC:** Allwinner A33
- **Architecture:** ARMv7 (sunxi)
- **GPU:** Mali-400
- **Bootloader:** U-Boot (sunxi legacy)
- **Kernel:** Linux 3.4.39 (sunxi)
- **Boot format:** Android-style `boot.img`
- **Hardware configuration:** `script.bin` / `magic.bin` (Allwinner legacy format)

The autopsy confirms that the device **does not use an RK3326**, despite the markings present on the chip package.

---

## Why this autopsy is critical

- Modern public EmuELEC builds **do not boot** on this hardware
- The partition layout is non-standard and depends on old U-Boot
- The kernel and hardware configuration are highly specific
- Without the original SD or equivalent dumps, the device is hard to recover

Therefore, any modification attempt **must start from exactly this known working state**.

---

## Structure of this directory

- `README.md` / `README.en.md` — context and scope of the reference autopsy
- `files.md` / `files.en.md` — technical catalogue of the files provided in the original autopsy
- `notes.md` / `notes.en.md` — observations and comparisons against this project's actual hardware
- `sources.md` / `sources.en.md` — links, credits and external sources

---

## Project directive

> No system component will be replaced before it is understood.

This rule applies to:
- kernel
- bootloader
- partition layout
- hardware configuration

Any violation of this directive drastically increases brick risk.

---

## Current state

- Autopsy validated as compatible with this project's hardware
- Working system confirmed via customized EmuELEC 4.7
- Next step: detailed documentation of the physical hardware ([`../../docs/hardware.en.md`](../../docs/hardware.en.md))
