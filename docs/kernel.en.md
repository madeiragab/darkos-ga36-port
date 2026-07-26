> 🇧🇷 [Português](kernel.md) · 🇬🇧 **English**

# Kernel

## Working baseline

| Item | Value | State |
|---|---|---|
| Family | Linux-sunxi (legacy) | Confirmed |
| Version | 3.4.x (`3.4.39` observed in the dump) | Confirmed |
| Architecture | ARM Cortex-A7 quad-core (Allwinner A33 / `sun8i`) | Confirmed |
| GPU | Mali-400, correctly detected by the kernel | Confirmed |
| Packaging | Android `boot.img` (kernel + ramdisk) | Confirmed |
| Hardware configuration | `script.bin` (not DTB) | Confirmed |

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

## Why modern kernels do not boot

| Barrier | Detail |
|---|---|
| Configuration format | Modern kernels expect a DTB; this board uses legacy `script.bin` |
| A33 support in mainline | It exists, but with completely different bindings and device tree |
| Mali-400 driver | Legacy blob, tied to the old kernel version |
| Packaging | This board's U-Boot expects an Android `boot.img`, not `zImage`/`uImage` |

Swapping the kernel without solving **all** of these barriers results in silent failure: dark screen, no log, no indication of which stage failed.

## Pending

- [ ] Dump `boot.img` and extract kernel and ramdisk separately
- [ ] Full listing of modules loaded at runtime
- [ ] Capture complete `dmesg` into a committed file
- [ ] Boot log over serial (requires identifying the TX/RX/GND pads)
