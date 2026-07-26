> 🇧🇷 [Português](failures.md) · 🇬🇧 **English**

# Failure log and dead ends

This file exists so that **nobody repeats the same mistake twice** — neither me, nor whoever finds this repository with the same console in hand.

A documented failure is knowledge. A forgotten failure is a bricked console.

## How to record

One entry per attempt, in this format:

```markdown
### YYYY-MM-DD — Short title of what was attempted

**Hypothesis:** what was expected to happen
**Action:** exactly what was done (commands, files, versions)
**Result:** what actually happened
**Diagnosis:** why it failed (or "unknown")
**Recovery:** how the console was brought back to a working state
**Lesson:** what changes on the next attempt
```

Record **before** trying again. If the result is "unknown", record it as such — half the information is worth more than none.

---

## Known failures (inherited from the community and the autopsy)

These have **not** been tested on this unit — they are listed here because the outcome is predictable and destructive. **Do not volunteer as the test subject.**

### Flashing a public R36S / RK3326 image

**Result:** does not boot. The actual SoC is an Allwinner A33, not an RK3326.
**Aggravating factor:** the process overwrites the original SD. Without a backup, the console becomes unusable.
**Lesson:** the chip silkscreen is not a source of truth — see [docs/kernel.en.md](docs/kernel.en.md) to confirm the real SoC.

### Flashing official EmuELEC (public build)

**Result:** does not boot. The factory system is a custom build (`GA36-UDT-EE-TF-R-20250818`) compiled for the A33.
**Lesson:** the custom build is the only proven working baseline.

### Repartitioning the SD with a graphical tool

**Result:** brick. Boot depends on the physical layout and on a raw partition (~16 MB, U-Boot) that graphical tools treat as unallocated space.
**Lesson:** bit-for-bit backup with `dd`, never a file copy — see [docs/storage.en.md](docs/storage.en.md).

### Swapping the kernel and keeping everything else

**Result:** silent failure — black screen, no log, no indication of which stage broke.
**Diagnosis:** the new kernel does not interpret the legacy `script.bin`, and U-Boot expects a `boot.img` in Android format.
**Lesson:** without serial access, this class of failure is undebuggable — see [docs/device-tree.en.md](docs/device-tree.en.md).

---

## Failures recorded on this unit

_None so far — no destructive modification has been attempted._

The current state is: working boot, SD backup taken, hardware identified. Every future attempt must be recorded above **before** being repeated.
