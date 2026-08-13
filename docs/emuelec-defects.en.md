> 🇬🇧 **English** · 🇧🇷 [Português](emuelec-defects.md)

# EmuELEC 4.7 defects on this board

The stock system is an unofficial fork of EmuELEC 4.7 (`EE_VERSION` =
`4.7`, upstream by Shanti Gilbert). Official EmuELEC 4.7 **never had a
sun8i/A33 target** — the vendor adapted it on their own, and several things
were left broken along the way.

This document lists defects **verified in the image contents**, not
impressions from use. Each one comes with its evidence and its fix.

---

## 1. Save loss when powering off with the button

The most complained-about symptom. It is not one bug — it is **four stacked
failures**, and any one of them alone would already lose the save.

### 1.1 RetroArch never writes during play

`/storage/.config/retroarch/retroarch.cfg`:

```
autosave_interval = "0"
```

At zero, SRAM only reaches disk when the core unloads (on exiting the game).
Cutting power mid-game means the entire session never existed on disk.
**This is the primary cause.**

### 1.2 Saves land on FAT32 with no journal

```
savefiles_in_content_dir = "true"
savefile_directory = "/saves"
```

With `savefiles_in_content_dir` on, the save is written next to the ROM —
that is, on the FAT32 partition. And `init` mounts that partition like this:

```sh
mount -t "${ROM_FS_TYPE}" -o utf8 "${ROMS_PART_PATH}" /storage/roms
```

Only `utf8`. No `flush`, no `sync`. vfat holds writes in cache, and FAT32
has no journal: an interrupted write corrupts the directory entry, not just
the file.

(`savefile_directory = "/saves"` points at the system root, which is
read-only squashfs — an incoherent setting that only fails to break because
`savefiles_in_content_dir` takes precedence.)

### 1.3 Nothing repairs on the next boot

See section 2.

### 1.4 The power button cuts power without telling the system

Behaviour observed on the unit: holding the power button **loses** the save.
Exiting the emulator with `Start` + `Select` (returning to EmulationStation)
**writes** it.

This is the exact signature of problem 1.1: SRAM is only written when the
core unloads. `Start`+`Select` unloads the core; the power button does not —
it cuts at the PMIC (AXP22x) before any flush.

Until the button handler is fixed, **the safe shutdown is `Start`+`Select`
first, button afterwards**.

The handler lives inside `SYSTEM` (lzo squashfs) and has not been inspected
yet.

### 1.5 No writeback tuning

`/storage/.config/sysctl.d/` contains only a `README`. Kernel defaults
apply, `vm.dirty_expire_centisecs = 3000` — data can sit in RAM for up to
30 s before touching the card.

### Fix

Applied through `/storage/.config/custom_start.sh`, which EmuELEC runs
before the frontend:

| Setting | From | To |
|---|---|---|
| `autosave_interval` | `0` | `10` |
| `savefiles_in_content_dir` | `true` | `false` |
| `savefile_directory` | `/saves` | `/storage/savefiles` (ext4, journalled) |
| `savestate_directory` | `~/roms/savestates/gb` | `/storage/savestates` |
| ROM partition mount | `utf8` | `remount,flush` |
| `vm.dirty_expire_centisecs` | 3000 | 200 |

`savestate_directory` pointed at a hardcoded `gb` folder — a leftover from
someone testing a Game Boy title; savestates from every system landed there.

---

## 2. `fsck.auto` does not exist in the initramfs

`init` calls it without specifying a type:

```sh
fsck -T -M -p -a $RUN_FSCK_DISKS
```

Detection fails and it looks for `/sbin/fsck.auto`. The initramfs ships
`e2fsck`, `fsck.ext2`, `fsck.fat` and `fsck.exfat` — but **no `fsck.ext4`
and no `fsck.auto`**. The image's own `init.log` records it:

```
fsck: fsck.auto: No such file or directory
fsck: fsck.auto: No such file or directory
mount: mounting /run on /sysroot/run failed: Invalid argument
```

Result: `/storage` is never checked after an unclean shutdown.

**Fix:** requires repacking `boot.img` (create `fsck.ext4` as a link to
`e2fsck`, or pass `-t ext4`). Not done yet.

---

## 3. Silent `/storage` fallback to tmpfs

`init` has this path:

```sh
if [ -n "$disk" ]; then
    ...
    mount_part "$disk" "/storage" "rw,noatime"
else
    # /storage should always be writable
    mount -t tmpfs none /storage
fi
```

When `/storage` fails to mount, the system **boots anyway**, with `/storage`
in RAM. The effect is subtle and very confusing:

- there is no `.config`, so EmuELEC copies defaults from `SYSTEM`;
- no customization survives a reboot;
- there are no ROMs, and EmulationStation shows `we can't find any systems`;
- **nothing is written to the ext4** — which can be confirmed from outside
  with [`tools/verify_card.py`](../tools/verify_card.py).

Practical diagnosis: if the `ext4 /storage` region comes out **identical**
to the image after a boot, `/storage` did not mount. If differences appear,
it did.

> This fallback also makes any change under `/storage/.config` useless while
> the problem is present — the section 1 fix never runs.

---

## 4. Frontend performance

> **Correction.** An earlier version of this document claimed the system
> rendered at 1920×1080 and scaled down to 640×480, because of
> `ee_videomode=1080p60hz` in `emuelec.conf`. **That is wrong.**
>
> `script.bin`'s `disp_init` has `fb0_width = 0`, `fb0_height = 0` and
> `fb0_scaler_mode_enable = 0`. Zero means "use the panel size", so the
> framebuffer **is already 640×480** and there is no scaler in the path.
> `ee_videomode` is an Amlogic concept (it writes to
> `/sys/class/display/mode`), a path that does not exist on this Allwinner
> platform — the key is **inert**.
>
> Do not change `ee_videomode` expecting a gain: there is none.

The real frontend cost is elsewhere.

### `retroarch.cfg`

| Key | Stock value | Problem |
|---|---|---|
| `menu_driver` | `xmb` | animated 3D menu, expensive on Mali-400 |
| `menu_shader_pipeline` | `1` | shader-animated background |
| `auto_shaders_enable` | `true` | auto-loads shaders — worst case on this GPU |
| `menu_dynamic_wallpaper_enable` | `true` | wallpaper decoding |
| `menu_show_sublabels` | `true` | a second text line per item |
| `menu_ticker_smooth` | `true` | smooth title scrolling = continuous redraw |
| `log_verbosity` | `true` | verbose logging, written to the card for nothing |
| `menu_widget_scale_factor` | `2.0` | widgets at 2× scale on a 640×480 panel |

### RGUI aspect ratio is wrong

```
rgui_aspect_ratio = "6"
```

Value 6 is **3:2 centered**. The panel is **4:3** (640×480), which is value
`0`. With 6, RGUI draws letterboxed and wastes screen area.

### `es_settings.cfg`

| Key | Stock value | Problem |
|---|---|---|
| `GamelistViewStyle` | `detailed` | renders image and metadata per item |
| `ScreenSaverBehavior` | `slideshow` | decodes images in a loop |
| `ScrapeVideos` | `true` | video previews inside the gamelist |

`TransitionStyle` and `GameTransitionStyle` already ship as `instant` —
those were right from the factory.

### `emuelec.conf`

| Key | Stock value | Problem |
|---|---|---|
| `audio.bgmusic` | `1` | continuous music decoding in the frontend |
| `updates.enabled` | `1` | no wifi, and no real upstream for this fork |
| `system.timezone` | `America/Mexico_City` | vendor default |

**Quick on-device check:** if the RetroArch menu opens in RGUI (plain text)
instead of XMB (3D waves), the fixes are active.

---

## 5. Other observations

- `system.timezone=America/Mexico_City` — vendor default.
- `system.hostname=UDT` — vendor branding in the build
  (`GA36-UDT-EE-TF-R-20250818`).
- `ee_ssh.enabled=1` with `wifi.enabled=0`: SSH is on, but with no network
  there is no way to reach it.
- `global.maxperf=1` already ships at maximum.
- `es_systems.cfg` defines **106 systems**. EmulationStation hides any whose
  folder is empty — a folder created without a ROM will not show up.

---

## Inspecting without mounting anything

```bash
python tools/ext4_reader.py IMAGE 0x37400000 ls:/.config
python tools/ext4_reader.py IMAGE 0x37400000 cat:/.config/emuelec/configs/emuelec.conf
python tools/ext4_reader.py IMAGE 0x37400000 cat:/.config/retroarch/retroarch.cfg
python tools/ext4_reader.py IMAGE 0x37400000 cat:/init.log
```

The initramfs `init` lives inside `boot.img`; to extract it, use the `dd`
command that [`tools/boot_header.py`](../tools/boot_header.py) prints.
