> 🇧🇷 [Português](notes.md) · 🇬🇧 **English**

# Validation notes — autopsy vs. actual hardware (GA36)

This document records the observations made from comparing the **reference autopsy** against the **actual physical hardware** analysed in this project.

The aim is to identify:
- what has already been confirmed as compatible
- what is still uncertain
- what differs between board revisions

---

## State of the analysed hardware

- Working console
- Original system still operational
- Original SD preserved
- Board opened for visual inspection
- No serial console access at this time

---

## Board identification

**Reference autopsy:** GA36-MB V1.0 (`GA36-MB V1.0-20250730`)
**This project's hardware:** GA36-MB V1.1 (`GA36-MB V1.1-20251025`)

**Conclusion:** the revisions differ only in layout/routing. There is no visual indication of a change in SoC or architecture.

---

## SoC (System on Chip)

**Autopsy:** Allwinner A33 (confirmed by boot logs and Mali-400 GPU)

**This project's hardware:**
- Chip physically labelled "RK3326"
- System logs indicate:
  - Mali-400 GPU
  - OpenGL ES 2.0
  - ARM architecture

**Conclusion:** the actual SoC is an Allwinner A33. The RK3326 labelling is false.

Status: **confirmed**

---

## GPU

**Autopsy:** Mali-400

**This project's hardware:**
- EmuELEC reports OpenGL ES 2.0
- Shader ES 3.20 (compatibility layer)

**Conclusion:** compatible with Mali-400.

Status: **confirmed**

---

## Kernel and boot

**Autopsy:**
- Linux 3.4.39 (sunxi)
- Boot via Android-style `boot.img`
- Use of `script.bin` / `magic.bin`

**This project's hardware:**
- Original system reports custom EmuELEC 4.7
- Public EmuELEC build does not start

**Conclusion:** the same kernel/boot model is in use. Heavy dependence on legacy Allwinner configuration.

Status: **compatible (indirect)**

---

## Partition layout

**Autopsy:**
- Non-standard layout
- Raw and squashfs partitions
- FAT16 for `script.bin`

**This project's hardware:**
- Not yet dumped locally
- System works only with the original SD

**Conclusion:** the layout is highly likely to be identical or very close.

Status: **assumed (not verified)**

---

## U-Boot

**Autopsy:**
- Specific legacy U-Boot
- Configuration stored in a raw partition

**This project's hardware:**
- Working boot only with the original SD
- No evidence of a modern U-Boot

**Conclusion:** U-Boot compatible with the autopsy. Replacing it without a dump is risky.

Status: **assumed (high confidence)**

---

## Peripherals

**Display**
- Autopsy: display initialised via `script.bin`
- Actual hardware: display working
- Status: **compatible**

**Controls / buttons**
- Autopsy: input handled by overlays
- Actual hardware: controls working
- Status: **compatible**

**Audio**
- Autopsy: basic support
- Actual hardware: audio working
- Status: **compatible**

---

## Serial console

Pads silkscreened as:
- GND
- TX
- RX

Not used in this project so far; no serial log captured.

Status: **unexplored**

---

## Identified risks

- Losing the original SD may render the console unrecoverable
- Kernel and boot depend heavily on legacy configuration
- Port attempts without a working baseline are prone to bricking

---

## General conclusion

The hardware analysed in this project is **compatible with the reference autopsy**.

Observed differences:
- Board revision (V1.1 vs V1.0)
- No critical difference identified so far

The autopsy remains valid as a technical baseline for:
- documentation
- study
- future port or modification attempts

Any progress must preserve:
- the working kernel
- `script.bin` / `magic.bin`
- the partition layout
