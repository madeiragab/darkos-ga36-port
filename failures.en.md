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

### 2026-08-12 — Windows emptied the card's partitions

**Hypothesis:** plugging the card into a PC to inspect it would be harmless.
**Action:** card inserted into Windows 11, volumes auto-mounted.
**Result:** the `Volumn` and ROM partitions came up empty; the factory
content (fonts, `bootlogo.bmp`, `magic.bin`) was gone. The ROM partition had
been reformatted as exFAT.
**Diagnosis:** Windows mounts `Volumn` using the **BPB**, which declares
128 MB, while the MBR entry declares 32 MB. It treats the 36 MB–164 MB range
of the card as writable — where `boot.img` (84 MB) and `SYSTEM` (116 MB)
live. It also creates `System Volume Information` on its own at mount time.
See [docs/image-autopsy.en.md](docs/image-autopsy.en.md) §6.3.
**Recovery:** re-flashing the recovery image.
**Lesson:** **never let Windows mount this card without need.** If you must,
disable automount first (`diskpart` → `automount disable`) and never click
"Format" when it offers.

### 2026-08-12 — Recovery image yields a 5.42 MB ROM partition

**Hypothesis:** flashing the recovery image would restore the console to
factory state.
**Action:** byte-for-byte flash of `r36s-a33-recovery.img` (2425 MB).
**Result:** the console booted, but EmulationStation showed
`we can't find any systems`. Partition 1 ended up with 11 099 sectors
(5.42 MB).
**Diagnosis:** the distributed image is truncated — the MBR entry declares
5.42 MB while the internal FAT32 BPB declares 48 779 MB. The MBR also points
at LBA 4956161 when the real boot sector is at 4956160.
**Recovery:** rewriting the MBR entry (start 4956160, size to the end of the
card) and generating a fresh FAT32 labelled `EEROMS`.
**Lesson:** the recovery image is **not** usable as-is. See
[docs/storage.en.md](docs/storage.en.md).

### 2026-08-12 — Console would not power on; looked like a brick, was the battery

**Hypothesis:** after a successful boot the console stopped powering on —
immediate suspicion of boot corruption.
**Action:** byte-for-byte comparison of card against image
([`tools/verify_card.py`](tools/verify_card.py)).
**Result:** only 32.6 KB of difference, all in harmless areas (`Volumn` FAT
table and the ROM partition). `boot0`, `boot.img`, `SYSTEM` and the ext4 were
intact.
**Diagnosis:** deeply discharged battery. The charge LED lights well before
there is enough charge to boot.
**Recovery:** 2 hours on the charger without attempting to power on.
**Lesson:** with `loglevel=0` and `bootdelay=0`, a boot failure and a flat
battery produce exactly the same black screen. Verify the card by reading it
before assuming corruption, and charge properly before assuming a brick.

### 2026-08-13 — `custom_start.sh` is not executed by this fork

**Hypothesis:** the `/storage/.config/custom_start.sh` hook, documented by
EmuELEC itself as the place for boot scripts, would run before the frontend.
**Action:** patched `custom_start.sh` with `sed` to adjust
`autosave_interval`, `menu_driver` and 7 other `retroarch.cfg` keys.
**Result:** none of the keys changed. Confirmed by reading the live
`retroarch.cfg` off the card.
**Diagnosis:** **confirmed by reading `SYSTEM`.** In
`/usr/bin/emuelec_autostart.sh` the call is commented out:

```sh
# run custom_start before FE scripts
#/storage/.config/custom_start.sh before &
```

The file still carries, just above it, the upstream comment telling you to
use `custom_start.sh` — now orphaned. Fixing it at the source would require
repacking the squashfs, which is why the solution uses
`/flash/post-flash.sh` and direct file writes.
**Recovery:** none needed — the hook simply does not run, nothing broke.
**Lesson:** on this system, changing configuration means writing to the file
directly, not relying on hooks. See
[`tools/patch_retroarch.py`](tools/patch_retroarch.py).

### 2026-08-13 — Console powered itself off during boot

**Hypothesis:** swapping `systemctl suspend` for `poweroff`, via a function
in `profile.d`, would make a button tap shut the console down.
**Action:** `tools/powerkey_poweroff.py --apply`.
**Result:** the console powered on, passed the splash and **shut itself
down** exactly when EmulationStation was about to appear.
**Diagnosis:** `udt_pwr.service` starts with `Before=emuelec.target`, ahead
of the frontend. The first read of
`/sys/devices/platform/micro_gamepad/power_key` still returns `1` — a
leftover from the tap that **powered the device on**. The script then fires
its action. Before the change that became a mid-boot `suspend`, which failed
or resumed immediately with no visible symptom. After the change it became a
real `poweroff`.
**Recovery:** `tools/powerkey_poweroff.py --revert --apply`.
**Lesson:** the button can fire during boot itself. Any destructive action
bound to it needs a time guard. The fixed version only converts to
`poweroff` after **90 s of uptime**; before that it keeps stock behaviour.

### 2026-08-13 — `Set-Disk -IsOffline` fails on removable media

**Hypothesis:** taking the disk offline would free up raw writes on Windows.
**Action:** `Set-Disk -Number N -IsOffline $true` before rewriting the MBR.
**Result:** `Set-Disk : Not Supported — Removable media cannot be set to
offline.`
**Diagnosis:** Windows refuses by design on removable media.
**Recovery:** open each volume with `CreateFileW`, apply
`FSCTL_LOCK_VOLUME` and `FSCTL_DISMOUNT_VOLUME`, and **keep the handles
open** during the write — what imaging tools do.
**Lesson:** for raw card writes on Windows, lock + dismount per volume, not
offline per disk.

---

The current state is: working boot, SD backup verified, hardware identified,
ROM partition fixed. Every future attempt must be recorded above **before**
being repeated.
