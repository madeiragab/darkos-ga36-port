> 🇧🇷 [Português](darkos-expectations.md) · 🇬🇧 **English**

# DarkOS: expectations vs. reality

The repository name (`darkos-ga36-port`) reflects the project's **initial motivation**. This document explains why the port did not happen, what would be required for it to happen, and why documenting came first.

## The initial expectation

The console is sold as "R36S / RK3326". Since DarkOS and other system images exist for genuine R36S units, the natural expectation is: download the image, flash it to the SD, done.

## The reality

The console **does not use the advertised SoC**. It is a clone with a remarked chip:

| Advertised | Actual |
|---|---|
| Rockchip RK3326 | Allwinner A33 (`sun8i`, quad Cortex-A7) |
| Compatible public images | Custom EmuELEC 4.7, board-specific build |
| Device Tree (DTB) | Legacy `script.bin` |
| Reasonably recent kernel | Linux sunxi 3.4.x |

**Flashing an R36S image onto this console does not boot** — and if the original SD is overwritten in the process, the console becomes e-waste.

## What a real port would require

In dependency order — each item requires the previous one:

1. ✅ **Intact backup of the original SD**, verified by hash.
   → [storage.en.md](storage.en.md)
2. ✅ **Fully mapped boot chain**: offsets, U-Boot environment, exact
   `boot.img` format. **Done** by offline parsing of the image.
   → [boot-chain.en.md](boot-chain.en.md), [image-autopsy.en.md](image-autopsy.en.md)
3. 🟡 **`script.bin` extracted and translated.** Located at `0x1366000`,
   78 sections. Display, UART and PMIC documented. **Missing** the control
   GPIO and the full FEX conversion. → [device-tree.en.md](device-tree.en.md)
4. 🟡 **Serial access.** Pins identified: **UART2, TX=PB0, RX=PB1,
   115200 8N1**, already enabled in U-Boot. **Missing** the correlation with
   the PCB pads and the soldering. → [serial-console.en.md](serial-console.en.md)
5. ⬜ **A new Device Tree for the A33**, plus a mainline kernel with Lima.
   **This is the real remaining work.**
6. 🟡 **A tested recovery path.** SD re-flash has been validated in practice
   (the console was recovered twice). FEL mode has not been tested.

Step 5 is the only one fully open, and inside it the concrete item is
**writing a driver for the `jd9366` panel**, which does not exist in
mainline.

## What changed since the first version of this document

The phrase "it cannot be ported" was imprecise. The accurate one is: **the
A33 has mainline support; what is missing is integrating this board.**

| Component | Mainline status |
|---|---|
| SoC `sun8i-a33` | `sun8i-a33.dtsi` |
| Mali-400 GPU | **Lima** (Mesa), GLES 2.0 |
| Display Engine | `sun4i-drm` + `sun8i-mixer` |
| MIPI DSI | `sun6i-mipi-dsi` |
| AXP223 PMIC | `axp20x` |
| MMC / USB / I2C / UART | supported |
| `jd9366` panel | **missing** |

The order that works: **serial first, device tree next, kernel last.**
Swapping the kernel before having serial is blind debugging — every failure
produces the same black screen.

## About PortMaster and Stardew Valley

A common motivation for people arriving at this console, worth recording so
no false expectations are set.

PortMaster **supports armhf**, so the infrastructure is not blocked by
architecture. Light 2D ports have a real chance. But the Stardew Valley port
published for the R36S **does not transfer**:

| | R36S (the port's target) | GA36-MB |
|---|---|---|
| Architecture | ARMv8 **64-bit** | ARMv7 **32-bit** |
| GPU | Mali-G31, GLES 3.2 | Mali-400, GLES 2.0, **no S3TC** |
| Usable RAM | 1 GB | ~850 MB |

The game's textures are DXT-compressed; without hardware S3TC the
decompression falls to software, consuming exactly the RAM and CPU that are
already short. **A new kernel changes none of those lines** — the limit is
GPU and memory. See [kernel.en.md](kernel.en.md), section "Limits no kernel
can fix".

## Why documenting came first

Because the alternative is the familiar pattern: someone tries to flash an image, the console does not boot, the original SD has already been overwritten, and the device becomes waste. The value of this repository is not a new system — it is that the **working environment continues to exist**, and that someone else with the same console learns the truth about the hardware before destroying it.

## Current position

Porting DarkOS **is not an immediate goal** and will only be reconsidered once the six prerequisites above are satisfied. See [scope.en.md](scope.en.md).
