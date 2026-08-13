> 🇬🇧 **English** · 🇧🇷 [Português](serial-console.md)

# Serial console (debug UART)

**Status: RESOLVED.** This document closes the open item listed in
[kernel.en.md](kernel.en.md), [boot-chain.en.md](boot-chain.en.md) and
step 4 of [darkos-expectations.en.md](darkos-expectations.en.md).

The pins were not found by probing the board — they were read out of the
unit's own `script.bin`. See [device-tree.en.md](device-tree.en.md) for the
method.

## Parameters

| Item | Value |
|---|---|
| Port | UART2 (`uart_debug_port = 2`) |
| Linux device | `/dev/ttyS2` |
| Baud rate | 115200 |
| Format | 8N1, no flow control |
| TX | **PB0** (`mux = 2`) |
| RX | **PB1** (`mux = 2`) |
| Logic level | **3.3 V** |

The U-Boot environment already carries `console=ttyS2,115200`, meaning
serial output is **enabled in software from boot0 onward**. Nothing has to
be recompiled to get a log — just connect.

## Every UART on the board

Extracted from `script.bin`:

| Section | `uart_used` | TX | RX | Note |
|---|---|---|---|---|
| `uart0` | 0 (disabled) | PF2 | PF4 | PF is the SD slot bus — this is Allwinner's FEL UART |
| `uart1` | 1 | PG6 | PG7 | |
| `uart2` | 1 | **PB0** | **PB1** | **debug console** |

`force_uart_para` repeats `port = 2`, `PB0`/`PB1` — the forced recovery
path targets the same pins.

## Why this matters more than it looks

This board's U-Boot is configured with:

```
loglevel=0
bootdelay=0
```

That means **the console prints nothing on screen during boot, by design**.
When boot fails, the symptom is a silent black screen — indistinguishable
from a dead device. That makes it impossible to tell apart:

- boot0 never started;
- U-Boot could not find `boot.img`;
- the kernel panicked;
- the kernel booted fine and only LCD init failed.

All four produce exactly the same screen. **Without serial, any attempt to
swap kernel or device tree is blind debugging.** With serial, each of them
is one line of log.

## Wiring

Required: a **3.3 V** USB-TTL adapter (CP2102, CH340G, or FT232RL with the
jumper set to 3.3 V).

```
Adapter              Board
-------              -----
RX      ──────────►  PB0  (console TX)
TX      ◄──────────  PB1  (console RX)
GND     ─────────── GND
```

> **Never connect the adapter's VCC.** The console has its own power.
> Feeding 5 V into a 3.3 V pin permanently damages the SoC.

Adapter TX goes to board RX and vice versa — crossed. If nothing shows up,
the first thing to try is swapping the two data wires; reversing TX and RX
damages nothing.

## Capturing

Linux:

```bash
screen /dev/ttyUSB0 115200
```

Windows (PuTTY): Serial, matching COM port, 115200, 8N1, flow control
`None`.

To version the log in this repository:

```bash
# Linux
cat /dev/ttyUSB0 | tee dumps/bootlogs/serial-boot.txt
```

## Locating the pads physically

`script.bin` gives the **SoC pin** (PB0/PB1), not the PCB coordinate. What
remains is correlating that with the visible pads in
[`images/serial_pads.png`](../images/serial_pads.png).

Method, with the console **powered off** and a multimeter in continuity
mode:

1. Find GND first — touch one probe to the USB shield or the battery
   negative and test each candidate pad.
2. With the console **powered on** and the multimeter in DC volts, measure
   the remaining pads against GND: the TX line idles near **3.3 V** and
   pulses low during boot; the RX line floats or sits pulled.
3. Confirm with a scope, or simply by connecting the adapter and checking
   whether readable text comes out at 115200.

Once confirmed, update this section with the board position and add an
annotated photo.

## Open items

- [ ] Correlate PB0/PB1 with the physical PCB pads
- [ ] Capture a full boot log and version it under `dumps/bootlogs/`
- [ ] Document whether the U-Boot prompt is reachable (`bootdelay=0`
      suggests there is no window — it may require interrupting over serial
      at the right instant, or rewriting the variable)
