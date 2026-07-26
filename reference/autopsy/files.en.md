> 🇧🇷 [Português](files.md) · 🇬🇧 **English**

# Reference autopsy files (GA36 / R36S clone)

This document catalogues and describes the files made available in the autopsy repository used as the **primary technical reference** for this project.

⚠️ Important:
- These files were **NOT produced by this project**
- They belong to the author of the original autopsy
- In this repository they are used **only as a technical reference**
- Binary files are **not committed here**, only documented

---

## List of analysed files

### 1. `first-1kb-of-sd-card-image.img.gz`

**Type:** binary dump (first 1 KB of the SD card)
**Origin:** GA36-MB autopsy (original repository)

**Technical description:**
Dump of the first 1024 bytes of the console's original SD card. Contains:
- MBR
- partition offsets
- initial boot information (sunxi legacy)

**Importance:** High.
An Allwinner A33 with old U-Boot is extremely sensitive to the SD's physical layout. This dump allows you to:
- understand the actual partition scheme
- avoid recreating the layout incorrectly

**Use in this project:**
- Reference for layout comparison
- Not used directly for flashing or booting

**Status:** External reference (not committed to this repository)

---

### 2. `kernel.img.zip`

**Type:** compressed kernel image
**Origin:** GA36-MB autopsy

**Technical description:**
The working kernel used by the GA36 clone console. Observed characteristics:
- Linux-sunxi (old kernel)
- Compatible with Allwinner A33
- Mali-400 GPU correctly detected
- Used via Android-style `boot.img`

**Importance:** Critical.
Modern public EmuELEC builds **do not work** on this hardware. This kernel represents a **proven working baseline**.

**Use in this project:**
- Reference for understanding compatibility
- Conceptual basis for any future port attempt

**Status:** External reference (not committed to this repository)

---

### 3. `magic.bin`

**Type:** hardware configuration binary (Allwinner legacy)
**Origin:** GA36-MB autopsy

**Technical description:**
A classic file from the old Allwinner ecosystem. It acts as:
- legacy DTB
- DRAM configuration
- GPIO mapping
- display, clock and peripheral initialisation

Conceptually equivalent to a modern DTB, but in a proprietary/legacy format.

**Importance:** Maximum.
Without this file:
- RAM may fail to initialise
- the screen stays off
- boot fails silently

**Use in this project:**
- Mandatory reference for understanding the hardware
- Any kernel change depends on it

**Status:** External reference (not committed to this repository)

---

### 4. `uboot-partition.img.gz`

**Type:** raw partition dump (U-Boot)
**Origin:** GA36-MB autopsy

**Technical description:**
Image of the partition containing:
- U-Boot
- environment
- board-specific parameters

This U-Boot:
- understands the old SD layout
- loads `boot.img` in Android format
- is specific to Allwinner A33 / GA36-MB

**Importance:** Critical.
Generic or modern U-Boot is **not compatible** without deep adaptation.

**Use in this project:**
- Recovery reference
- Understanding of the actual boot process

**Status:** External reference (not committed to this repository)

---

### 5. `overlays.zip`

**Type:** set of overlays/configurations
**Origin:** GA36-MB autopsy

**Technical description:**
Auxiliary files used by the system at runtime. Possible functions:
- framebuffer adjustments
- input (buttons/controls)
- audio
- minor peripherals

**Importance:** Medium.
The system can boot without them, but with broken functionality.

**Use in this project:**
- Reference for understanding specific adjustments
- Possible future reuse

**Status:** External reference (not committed to this repository)

---

## Project directive regarding these files

- None of these files will be modified without prior understanding
- None will be redistributed without a clear need
- Every port or modification attempt **starts from this data**
- This set defines the **working technical baseline** of the GA36 clone hardware

---

## Final note

This project does not attempt to "forcibly modernise" the hardware. The priority is:

1. understand what works
2. document why it works
3. only then consider changes

Any approach outside this tends to result in a brick.
