> 🇧🇷 [Português](scope.md) · 🇬🇧 **English**

# Project scope

This document defines **what this repository is and what it is not**, to avoid the kind of expectations that lead to a brick.

## In scope

1. **Document** the real hardware of the GA36-MB V1.1 board (Allwinner A33), contradicting the "RK3326" silkscreen printed on the package.
2. **Preserve** the working environment: backup of the original SD, cataloguing of boot artefacts, and recording of diagnostic output.
3. **Explain** why the current system works — boot chain, hardware configuration via `script.bin`, legacy kernel.
4. **Prevent bricking** other units, by recording what not to do and what has already failed.

## Out of scope (for now)

- **Porting DarkOS, modern EmuELEC or any new distribution.** This will only be considered once the boot chain is fully understood — see [darkos-expectations.en.md](darkos-expectations.en.md).
- **Recompiling the kernel.** The legacy sunxi 3.4.x kernel is the only proven working baseline. This is a sequencing decision, **not** a claim of impossibility: the A33 has mainline support, and the path is described in [kernel.en.md](kernel.en.md).
- **Redistributing third-party binaries.** Reference autopsy artefacts are catalogued and described, never committed here — see [../reference/autopsy/files.en.md](../reference/autopsy/files.en.md).

## What has entered scope

Fixing stock-system defects **is now in scope**, because they are verifiable
in the image and the fixes are reversible:

- save loss on power-off;
- unusable ROM partition in the recovery image;
- wrong RGUI aspect ratio and frontend render cost.

See [emuelec-defects.en.md](emuelec-defects.en.md).

Tooling the analysis is in scope too: the scripts in
[`../tools/`](../tools/) exist so anyone can reproduce the findings on their
own unit, without Linux and without mounting anything.

## Working principle

The order is always the same, and inverting it is how consoles get bricked:

1. understand what works;
2. document why it works;
3. only then consider changes.

## Criterion for "confirmed"

In this repository a piece of information is marked **confirmed** only when it comes from one of these sources:

| Source | Example |
|---|---|
| Silkscreen read directly on the PCB | revision `GA36-MB V1.1-20251025` |
| **Image read with a citable offset** | `sun8iw5p1` at `0x01a307e7f` |
| Command output on the unit | `/proc/cpuinfo`, `uname -a`, `dmesg` |
| Log from the running system | Mali-400 GPU detection |
| Independent third-party autopsy | partition layout, boot artefacts |

The second row is the strongest of the five and has become the preferred one:
anyone with the same image can re-run the tool and get the same byte at the
same offset. It does not depend on the console booting, nor on interpretation.

Everything else is explicitly marked as **pending** or **unconfirmed**.

> A distinction this repository maintains: **measured** ≠ **inferred**. The
> 1 GB RAM figure, for instance, comes from decoding `dram_para1`, and is
> marked as an inference until confirmed with `free -h` on the unit.
