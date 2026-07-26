> 🇧🇷 [Português](device-tree.md) · 🇬🇧 **English**

# Hardware configuration: script.bin, not Device Tree

This is the difference that most confuses anyone arriving at this board from modern ARM hardware.

## What changes

| | Modern system | GA36-MB (Allwinner legacy) |
|---|---|---|
| File | `.dtb` (compiled from `.dts`) | `script.bin` / `magic.bin` |
| Format | Device Tree Blob, open and documented | Proprietary/legacy (compiled `FEX`) |
| Tool | `dtc` | `fex2bin` / `bin2fex` (sunxi-tools) |
| Where it lives | Boot partition, next to the kernel | FAT16 partition (~32 MB) of boot resources |
| Editable? | Yes, with `dtc` | Yes, with sunxi-tools — **at your own risk** |

## What script.bin controls

It is the conceptual equivalent of a DTB, and is responsible for:

- **DRAM initialisation** — memory timings and parameters
- **GPIO mapping** — buttons, analog sticks, enables
- **Clocks** — CPU, GPU and peripheral frequencies
- **Display** — panel and FPC initialisation
- **Audio** — speaker enable pin

## Why it is critical

Without the correct `script.bin`:

- RAM may fail to initialise;
- the screen stays off;
- **boot fails silently** — no log, no message, no indication of which stage broke.

This is why the reference autopsy rates the importance of this file as **maximum**: any kernel change depends on it.

## Practical consequences

1. **There is no "just swap the DTB".** A mainline `.dtb` for the A33 is read neither by this U-Boot nor by this kernel.
2. **Editing requires understanding.** sunxi-tools can convert `script.bin` ↔ readable `FEX`, but a wrong DRAM or display value leaves the console with no picture — and with no picture there is no way to diagnose without serial access.
3. **Porting a modern system = rebuilding this from scratch** as a Device Tree, from values that today exist only inside this blob.

## Pending

- [ ] Extract `script.bin` from the boot partition
- [ ] Convert to FEX (`bin2fex`) and commit the readable version
- [ ] Map and document the control GPIO pins
- [ ] Document the display timings

> While these items remain open, any port attempt is trial and error with brick risk. See [scope.en.md](scope.en.md).
