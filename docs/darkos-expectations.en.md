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

1. **Intact backup of the original SD**, verified by hash.
   → see [storage.en.md](storage.en.md)
2. **Fully mapped boot chain**: offsets, U-Boot environment, exact `boot.img` format.
   → see [boot-chain.en.md](boot-chain.en.md)
3. **`script.bin` extracted and translated** to readable FEX, with GPIO, display, DRAM and clocks documented.
   → see [device-tree.en.md](device-tree.en.md)
4. **Working serial access** (TX/RX/GND pads identified and soldered). Without a serial console, a boot failure is a black screen with no diagnosis — it is the difference between debugging and guessing.
5. **A new Device Tree built from scratch** for the A33, from the values obtained in step 3, plus a mainline kernel with A33 and Mali-400 support.
6. **A tested recovery path** (FEL mode or SD re-flash) — proven to work **before** the first modified boot attempt.

Today steps 2 through 6 are pending. Step 1 is done.

## Why documenting came first

Because the alternative is the familiar pattern: someone tries to flash an image, the console does not boot, the original SD has already been overwritten, and the device becomes waste. The value of this repository is not a new system — it is that the **working environment continues to exist**, and that someone else with the same console learns the truth about the hardware before destroying it.

## Current position

Porting DarkOS **is not an immediate goal** and will only be reconsidered once the six prerequisites above are satisfied. See [scope.en.md](scope.en.md).
