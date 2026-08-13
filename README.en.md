> 🇧🇷 [Português](README.md) · 🇬🇧 **English**

# GA36-MB (R36S clone) — Autopsy, preservation and documentation

This repository documents a handheld console widely sold as "R36S / RK3326" which **does not use the advertised SoC**.
It is an **extreme clone**, with deliberately remarked hardware and heavily customized firmware.

The main goal of this project **is not to port a new system**, but to **preserve, understand and document** a working environment which, if lost, renders the device unusable.

---

## ⚠️ Important warning (read before anything else)

This console:

- **Does NOT use an RK3326**, despite the chip being marked as such
- **Does NOT run official EmuELEC**
- **Does NOT accept standard public images**
- **DEPENDS on the original SD card**

👉 **If the original SD is lost or corrupted, the console becomes e-waste.**

For that reason, **a full SD backup is mandatory** before any experiment.

---

## 🔍 Technical summary (confirmed)

- **Board:** GA36-MB, revision V1.1 (silkscreen: `GA36-MB V1.1-20251025`)
- **Actual SoC:** Allwinner **A33** — codename `sun8iw5p1`, Cortex-A7 quad,
  **ARMv7 32-bit**
- **GPU:** Mali-400 — GLES 2.0, **no S3TC**
- **RAM:** 1 GB DDR3 @552 MHz, **~850 MB usable** (176 MB CMA +
  150 MB carveout)
- **Panel:** **640 × 480**, MIPI DSI 2 lanes, `jd9366_8inch`
- **PMIC:** AXP22x
- **Kernel:** Linux sunxi **3.4.39**, built with gcc 4.6.3 (2012)
- **Boot:** Android `boot.img` + `script.bin` (Allwinner legacy, not DTB)
- **Debug serial:** **UART2 — TX=PB0, RX=PB1, 115200 8N1**
- **System:** EmuELEC 4.7, unofficial fork adapted to the A33

The "RK3326" silkscreen on the chip is **deliberate remarking**. The A33
identification does not rest on observed behaviour but on four pieces of
evidence read directly from the image — see
[docs/image-autopsy.en.md](docs/image-autopsy.en.md).

---

## 📚 Documentation

| Document | Subject |
|---|---|
| [docs/scope.en.md](docs/scope.en.md) | What is in and out of scope, and the criterion for "confirmed" |
| [docs/hardware.en.md](docs/hardware.en.md) | Components, technical evidence and board photos |
| **[docs/image-autopsy.en.md](docs/image-autopsy.en.md)** | **Image autopsy: offsets, structures and defects, with method** |
| **[docs/serial-console.en.md](docs/serial-console.en.md)** | **Serial console — pins, wiring and capture** |
| [docs/boot-chain.en.md](docs/boot-chain.en.md) | Boot chain with confirmed offsets and the U-Boot environment |
| [docs/device-tree.en.md](docs/device-tree.en.md) | `script.bin` — extracted values and the path to a mainline DT |
| [docs/kernel.en.md](docs/kernel.en.md) | Kernel 3.4.39, what blocks modernisation and what does not |
| [docs/storage.en.md](docs/storage.en.md) | Partition layout, backup, and the Windows-specific hazard |
| **[docs/emuelec-defects.en.md](docs/emuelec-defects.en.md)** | **Stock system defects: save loss, fsck, performance** |
| [docs/darkos-expectations.en.md](docs/darkos-expectations.en.md) | What would be missing for a real port to happen |
| [failures.en.md](failures.en.md) | Failure log — read before attempting anything |
| **[tools/](tools/)** | **Offline analysis scripts (pure Python, read-only)** |
| [reference/autopsy/](reference/autopsy) | Catalogue of the reference autopsy artefacts |

---

## 🎯 Project goals

This project exists to:

- Correctly document the GA36-MB (A33) hardware
- Preserve dumps, logs and critical information
- Make the current system **reproducible**
- Prevent other users from bricking the console
- Build a solid technical basis for future study

Porting modern systems (e.g. DarkOS) **is not an immediate goal** and will only be considered after the boot chain and hardware are fully understood.

---

## 📂 Repository structure

```text
/
├─ README.md                   → Project overview (pt-BR)
├─ README.en.md                → Project overview (English)
├─ failures.md                 → Failure log and dead ends
├─ docs/
│  ├─ scope.md                 → What is in and out of scope
│  ├─ hardware.md              → Detailed board documentation
│  ├─ image-autopsy.md         → Image autopsy: offsets and defects
│  ├─ serial-console.md        → Serial console (PB0/PB1 @115200)
│  ├─ boot-chain.md            → Boot chain (BROM → U-Boot → kernel)
│  ├─ device-tree.md           → script.bin and extracted values
│  ├─ kernel.md                → Kernel 3.4.39 and the path to mainline
│  ├─ storage.md               → Partition layout and SD backup
│  ├─ emuelec-defects.md       → Stock system defects
│  ├─ darkos-expectations.md   → Why the port has not happened yet
│  └─ reference_autopsy.md     → Summary of the external (third-party) autopsy
├─ tools/                      → Analysis scripts (Python, read-only)
├─ reference/autopsy/          → Catalogue of reference artefacts
└─ images/                     → Board and component photos
```

Each document has an `.en.md` counterpart in English.

---

## 🧠 Important references

This work is based on and validated against an independent autopsy of the same console, which correctly identified the use of an Allwinner A33 and documented the boot and partition layout.

A summary of that analysis is in [docs/reference_autopsy.en.md](docs/reference_autopsy.en.md).

---

## ❌ What NOT to do

- Do not format the original SD without a backup
- **Do not copy files to the `Volumn` partition** — Windows mounts it with
  the wrong size and can write over `boot.img`
- Do not let Windows "repair" any volume on the card
- Do not flash generic EmuELEC images
- Do not try modern kernels before having a serial console
- Do not assume RK3326 compatibility

These actions almost always result in a permanent brick.

---

## ✅ Current status

| Item | State |
|---|---|
| Hardware identified (GA36-MB V1.1 / Allwinner A33) | ✅ Confirmed |
| Fake RK3326 confirmed | ✅ Confirmed |
| Working system preserved (SD backup) | ✅ Done |
| Boot chain documented with exact offsets | ✅ Done |
| U-Boot environment extracted | ✅ Done |
| `script.bin` located and parsed | ✅ Done |
| Serial console pins identified | ✅ **PB0/PB1 @115200** |
| `boot.img` analysed (header, kernel, initramfs) | ✅ Done |
| Analysis tooling under version control | ✅ Done |
| Serial boot log captured | ⬜ Pending (requires wiring the adapter) |
| `script.bin` converted to full FEX | ⬜ Pending |
| Control GPIO mapped | ⬜ Pending |
| `jd9366` panel DSI sequence extracted | ⬜ Pending |
| Board device tree written | ⬜ Pending |
| Console diagnostic dumps under version control | ⬜ Pending |

Details of the pending items in [docs/scope.en.md](docs/scope.en.md) and [docs/darkos-expectations.en.md](docs/darkos-expectations.en.md).

---

## 📌 Final notice

This project has no affiliation with manufacturers or vendors.
All the documentation here exists because **the hardware lies about itself**.

If you own this console, back it up before doing anything.
