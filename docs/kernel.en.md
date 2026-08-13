> 🇧🇷 [Português](kernel.md) · 🇬🇧 **English**

# Kernel

## Working baseline

| Item | Value | State |
|---|---|---|
| Family | Linux-sunxi (legacy) | Confirmed |
| Version | **3.4.39** | Confirmed |
| Build toolchain | gcc 4.6.3 (crosstool-NG linaro-1.13.1-2012.02) | Confirmed |
| Build signature | `lxl@lxl` — same builder as U-Boot | Confirmed |
| Architecture | ARM Cortex-A7 quad-core, **ARMv7 32-bit** (`sun8iw5p1`) | Confirmed |
| GPU | Mali-400 | Confirmed |
| Packaging | Android `boot.img`, `name = sun8i` | Confirmed |
| Load addresses | kernel `0x40008000`, ramdisk `0x41000000` | Confirmed |
| Size | kernel 12.60 MB, initramfs 2.90 MB (gzip) | Confirmed |
| Hardware configuration | `script.bin` (not DTB) | Confirmed |
| Header `cmdline` | **empty** — bootargs come from U-Boot | Confirmed |

The 2012 toolchain is worth noting: this kernel was built with a gcc that
was already old when the hardware shipped in 2025.

The initramfs is **LibreELEC**-derived — it uses `/flash`, `/storage`,
`/sysroot`, `SYSTEM`, and the same `init` script. See
[emuelec-defects.en.md](emuelec-defects.en.md).

This kernel is the **only proven working baseline** for this board. Modern public EmuELEC builds do not work on this hardware.

## How to confirm on your unit

Run on the console and commit the output:

```bash
cat /proc/cpuinfo    # should show sun8i / an Allwinner identifier
uname -a             # should indicate a sunxi kernel (e.g. 3.4.39)
dmesg                # should report Mali-400 and sunxi strings
ls -la /lib/modules  # available modules
```

If the first three outputs confirm sunxi/A33, the "RK3326" silkscreen on the chip is **remarking** — the silkscreen is not a definitive source.

## Why not to recompile

The 3.4.x kernel is a legacy tree, out of mainline for over a decade. Recompiling would require:

- the exact toolchain and source tree used in the original build (**not available**);
- complete understanding of how this board's `script.bin` maps GPIO, display, clocks and audio;
- the ability to recover the console over serial or FEL when boot fails — and it will fail during the attempts.

None of these prerequisites is currently satisfied. Recompiling is therefore explicitly out of scope — see [scope.en.md](scope.en.md).

## Why modern kernels do not boot *today*

The wording matters. It is not that the A33 is incompatible with modern
Linux — **it has mainline support**. What is missing is the integration work
for this specific board.

| Barrier | Detail | Surmountable? |
|---|---|---|
| Configuration format | Modern kernels expect a DTB; this board uses `script.bin` | Yes — translation; values already extracted in [device-tree.en.md](device-tree.en.md) |
| Mali-400 driver | Legacy blob tied to 3.4 | Yes — **Lima** (Mesa) covers Mali-400 with GLES 2.0 in mainline |
| Packaging | U-Boot expects an Android `boot.img`, not `zImage` | Yes — either package the same way, or replace U-Boot (sunxi is well maintained in mainline) |
| Panel driver | `jd9366_8inch` does not exist in mainline | **This is the real new work** |
| Failure diagnosis | `loglevel=0`: failure = mute black screen | ✅ Solved — [serial-console.en.md](serial-console.en.md) |

What already exists in mainline for this SoC:

| Component | Status |
|---|---|
| SoC | `sun8i-a33.dtsi` |
| Mali-400 GPU | Lima (Mesa), GLES 2.0 |
| Display Engine | `sun4i-drm` + `sun8i-mixer` |
| MIPI DSI | `sun6i-mipi-dsi` |
| AXP223 PMIC | `axp20x` |
| MMC / USB / I2C / UART | supported |

**The order that makes sense:** serial first, device tree next, kernel last.
Swapping the kernel before having serial is blind debugging — every failed
attempt produces exactly the same black screen, with no information.

## Limits no kernel can fix

Worth recording so no false expectations are set. These are hardware
limits, not software ones:

- **ARMv7 32-bit.** Nothing requiring ARM64 runs here — including `box64`.
- **Mali-400: GLES 2.0, no S3TC.** DXT textures need software
  decompression.
- **~850 MB usable RAM.** Of 1 GB physical, the bootargs reserve 176 MB of
  CMA and 150 MB of carveout.

Updating the kernel improves stability, drivers and modern tooling. It
changes none of the lines above.

## Pending

- [x] Dump `boot.img` and read the header
- [x] Boot log over serial — pins identified (wiring still to do)
- [ ] Extract the initramfs and commit the vendor `init`
- [ ] Full listing of modules loaded at runtime
- [ ] Capture complete `dmesg` into a committed file
- [ ] Extract the DSI init sequence from the `jd9366_8inch` driver in `SYSTEM`
