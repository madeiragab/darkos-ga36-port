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
- **Recompiling the kernel.** The legacy sunxi 3.4.x kernel is the only proven working baseline.
- **Redistributing third-party binaries.** Reference autopsy artefacts are catalogued and described, never committed here — see [../reference/autopsy/files.md](../reference/autopsy/files.en.md).

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
| Command output on the unit | `/proc/cpuinfo`, `uname -a`, `dmesg` |
| Log from the running system | Mali-400 GPU detection |
| Independent third-party autopsy | partition layout, boot artefacts |

Everything else is explicitly marked as **pending** or **unconfirmed**.
