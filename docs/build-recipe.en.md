> 🇬🇧 **English** · 🇧🇷 [Português](build-recipe.md)

# Recipe: from recovery image to a working build

Complete, reproducible procedure to turn the distributed recovery image —
which is **not usable as shipped** — into a build with intact saves and a
light frontend.

State frozen at tag **`v1.0-working`**.

## What this recipe fixes

| Problem | Cause |
|---|---|
| 5.42 MB ROM partition, EmulationStation finds no systems | truncated image |
| Save lost when powering off with the button | 4 stacked failures |
| RGUI letterboxed | `rgui_aspect_ratio = 6` on a 4:3 panel |
| Heavy menu, logging to the card for nothing | factory configuration |

Diagnosis for each in [emuelec-defects.en.md](emuelec-defects.en.md) and
[image-autopsy.en.md](image-autopsy.en.md).

---

## Prerequisites

- Python 3 (no external dependencies)
- Windows: PowerShell **as Administrator** for the steps that touch the
  card. Linux: `sudo`, replacing `\\.\PhysicalDrive1` with `/dev/sdX`.
- The recovery image for your unit

> **Before anything:** take a bit-for-bit backup of the original SD and keep
> the hash. See [storage.en.md](storage.en.md). If you have not done that,
> stop here.

---

## Step 1 — Flash the image

Any raw-write tool (Rufus, balenaEtcher in DD mode, `dd`).

**When it finishes, do not let Windows mount the card.** If "You need to
format the disk" appears, click **Cancel**. The reason is in
[storage.en.md](storage.en.md) — the `Volumn` partition lies about its own
size and Windows can write over `boot.img`.

Check integrity at any time, **read-only**:

```bash
python tools/verify_card.py recovery.img \\.\PhysicalDrive1
```

## Step 2 — Fix the ROM partition

```bash
python tools/fix_rom_partition.py --apply
```

Rewrites the MBR entry (start LBA 4956160, aligned, through the end of the
card) and generates a fresh FAT32 labelled `EEROMS`.

## Step 3 — Create the ROM folders

EmulationStation hides any system whose folder is empty. The 106 expected
names come from `es_systems.cfg` itself:

```bash
python tools/ext4_reader.py \\.\PhysicalDrive1 0x37400000 cat:/.config/emulationstation/es_systems.cfg
```

Create the folders at the root of the ROM partition and **put at least one
ROM in** — an empty folder will not show up.

## Step 4 — Configuration

```bash
python tools/patch_config.py \\.\PhysicalDrive1 0x37400000 --apply
```

Covers `retroarch.cfg`, `emuelec.conf` and `es_settings.cfg` in one pass.
Idempotent: it skips anything already at the desired value.

## Step 5 — Writeback hook

```bash
python tools/fat16_write.py \\.\PhysicalDrive1 0x7400000 --put boot-hooks/post-flash.sh post-flash.sh --apply
```

Without this, step 4 is not enough: SRAM is written every 10 s but sits in
the page cache for up to 30 s. The hook brings that down to ~2 s. Details
and the **recovery path** in [../boot-hooks/README.md](../boot-hooks/README.md).

## Step 6 — Verify on the device

| Signal | Meaning |
|---|---|
| RetroArch menu in **RGUI** (text), not XMB | step 4 applied |
| `dmesg \| grep post-flash` shows `writeback ajustado` | step 5 applied |
| Systems appear in EmulationStation | steps 2 and 3 ok |
| Save, play 30 s, hold the button, reboot: save intact | full fix working |

---

## Freezing your build

Once validated, take an image of the **working** card. It is the only
artefact that restores this state without repeating the recipe:

```bash
sudo dd if=/dev/sdX of=ga36-working-v1.0.img bs=4M status=progress
sha256sum ga36-working-v1.0.img > ga36-working-v1.0.img.sha256
```

On Windows any raw-read tool will do; keep the hash alongside it.

> Full SD images are **not** versioned in this repository. The recipe is
> reproducible precisely so they do not have to be.

---

## What this recipe does not fix

- **The power button cuts at the PMIC** without telling the system. The
  handler is inside `SYSTEM` (read-only squashfs). Mitigated, not fixed: you
  lose at most ~12 s instead of the whole session. Clean shutdown is still
  `Start`+`Select` before the button.
- **Missing `fsck.auto`** in the initramfs — requires repacking `boot.img`.
- **PSP, Stardew Valley, and anything needing ARM64 or GLES 3.** Hardware
  wall. See [kernel.en.md](kernel.en.md), "Limits no kernel can fix".
