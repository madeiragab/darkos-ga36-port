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

- **Board:** GA36-MB
- **Revision documented in this repo:** V1.1 (silkscreen: `GA36-MB V1.1-20251025`)
- **Actual SoC:** Allwinner A33 (sunxi)
- **GPU:** Mali-400 (confirmed by EmuELEC logs)
- **Kernel:** Linux sunxi 3.4.x (legacy)
- **Boot:** Android-style `bootimg` + `ramdisk`
- **Hardware configuration:** `script.bin` (Allwinner legacy, not DTB)
- **System:** EmuELEC 4.7 customized specifically for the A33

The "RK3326" silkscreen on the chip is **deliberate remarking**.
Electrical behaviour, the kernel, the bootloader and the GPU all confirm this is **not a real RK3326**.

---

## 📚 Documentation

| Document | Subject |
|---|---|
| [docs/scope.en.md](docs/scope.en.md) | What is in and out of scope, and the criterion for "confirmed" |
| [docs/hardware.en.md](docs/hardware.en.md) | Components, technical evidence and board photos |
| [docs/boot-chain.en.md](docs/boot-chain.en.md) | Full boot chain and why each link matters |
| [docs/device-tree.en.md](docs/device-tree.en.md) | Legacy `script.bin` — what it is and why you cannot "just swap the DTB" |
| [docs/kernel.en.md](docs/kernel.en.md) | sunxi 3.4.x kernel, how to confirm it and why not to recompile |
| [docs/storage.en.md](docs/storage.en.md) | Partition layout and how to back up the SD correctly |
| [docs/darkos-expectations.en.md](docs/darkos-expectations.en.md) | What would be missing for a real port to happen |
| [failures.en.md](failures.en.md) | Failure log — read before attempting anything |
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
│  ├─ boot-chain.md            → Boot chain (BROM → U-Boot → kernel)
│  ├─ device-tree.md           → Legacy script.bin (not a DTB)
│  ├─ kernel.md                → sunxi 3.4.x kernel and why not to recompile
│  ├─ storage.md               → Partition layout and SD backup
│  ├─ darkos-expectations.md   → Why the port has not happened yet
│  └─ reference_autopsy.md     → Summary of the external (third-party) autopsy
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
- Do not flash generic EmuELEC images
- Do not try modern kernels without understanding the boot chain
- Do not assume RK3326 compatibility

These actions almost always result in a permanent brick.

---

## ✅ Current status

| Item | State |
|---|---|
| Hardware identified (GA36-MB V1.1 / Allwinner A33) | ✅ Confirmed |
| Fake RK3326 confirmed | ✅ Confirmed |
| Working system preserved (SD backup) | ✅ Done |
| Boot chain documented at a high level | ✅ Done |
| Diagnostic dumps under version control | ⬜ Pending |
| Bootimg extracted and analysed | ⬜ Pending |
| `script.bin` extracted and translated to FEX | ⬜ Pending |
| Serial access (TX/RX/GND pads) | ⬜ Pending |

Details of the pending items in [docs/scope.en.md](docs/scope.en.md) and [docs/darkos-expectations.en.md](docs/darkos-expectations.en.md).

---

## 📌 Final notice

This project has no affiliation with manufacturers or vendors.
All the documentation here exists because **the hardware lies about itself**.

If you own this console, back it up before doing anything.
