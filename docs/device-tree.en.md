> 🇬🇧 **English** · 🇧🇷 [Português](device-tree.md)

# Hardware configuration: script.bin, not Device Tree

This is the difference that most confuses people arriving at this board from
modern ARM hardware.

## What changes

| | Modern system | GA36-MB (Allwinner legacy) |
|---|---|---|
| File | `.dtb` (compiled from `.dts`) | `script.bin` |
| Format | Device Tree Blob, open and documented | Proprietary/legacy (compiled `FEX`) |
| Tool | `dtc` | `fex2bin` / `bin2fex` (sunxi-tools) |
| Where it lives | Boot partition, next to the kernel | **Raw area**, embedded alongside U-Boot |
| Editable? | Yes, with `dtc` | Yes — **at your own risk** |

## Confirmed location

**`script.bin` sits at `0x01366000` (19.40 MB), in the raw area** next to
U-Boot — **not** in the `Volumn` FAT16 partition, as this page previously
claimed. That FAT16 holds only fonts, `bootlogo.bmp` and `magic.bin`.

It contains **78 sections**. Extracted and parsed with
[`tools/scriptbin_parse.py`](../tools/scriptbin_parse.py); method and other
offsets in [image-autopsy.en.md](image-autopsy.en.md).

Sections present (partial):

```
product platform target key_detect_en fel_key power_sply card_boot
card0_boot_para card2_boot_para twi_para uart_para force_uart_para
jtag_para clock pm_para dram_para wakeup_src_para twi0 twi1 twi2
uart0 uart1 uart2 uart3 uart4 spi0 spi1 spi_devices spi_board0
ctp_para ctp_list_para tkey_para motor_para ths_para cooler_table
nand0_para disp_init lcd0_para pwm0_para ...
```

## Extracted values

These are the data a new Device Tree must reproduce. All read from the unit,
not from generic A33 documentation.

### Display — `lcd0_para`

| Key | Value |
|---|---|
| `lcd_used` | 1 |
| `lcd_driver_name` | **`jd9366_8inch`** |
| `lcd_if` | 4 (MIPI DSI) |
| `lcd_x` × `lcd_y` | **640 × 480** |
| `lcd_dclk_freq` | 30 (MHz) |
| `lcd_hbp` / `lcd_ht` / `lcd_hspw` | 120 / 1040 / 40 |
| `lcd_vbp` / `lcd_vt` / `lcd_vspw` | 12 / 518 / 6 |
| `lcd_dsi_if` | 2 |
| `lcd_dsi_lane` | 2 |
| `lcd_dsi_format` | 0 |
| `lcd_dsi_eotp` | 1 |
| `lcd_pwm_used` | 1 |
| `lcd_pwm_ch` / `lcd_pwm_freq` / `lcd_pwm_pol` | 0 / 20000 / 0 |
| `lcd_power` | **`axp22_dc1sw`** |

And from `disp_init`: `screen0_output_type = 1`, `lcd0_backlight = 204`,
`fb0_format = 10`.

> The driver name `jd9366_8inch` says "8inch", but the resolution is
> 640×480 — a name inherited from the panel vendor, not an indication of
> this unit's real physical size.

### UART

Detailed in [serial-console.en.md](serial-console.en.md).

| Section | `uart_used` | TX | RX |
|---|---|---|---|
| `uart0` | 0 | PF2 (mux 3) | PF4 (mux 3) |
| `uart1` | 1 | PG6 (mux 2) | PG7 (mux 2) |
| `uart2` | 1 | **PB0** (mux 2) | **PB1** (mux 2) |

`uart_para`: `uart_debug_port = 2`, TX `PB0`, RX `PB1`.

### PMIC — `power_sply`

Confirms **AXP22x** (the A33's AXP223 family).

| Rail | Voltage (mV) |
|---|---|
| `dcdc1_vol` | 3000 |
| `dcdc2_vol` | 1100 |
| `dcdc3_vol` | 1200 |
| `dcdc4_vol` | 0 (off) |
| `dcdc5_vol` | 1500 |
| `aldo2_vol` | 2500 |
| `aldo3_vol` | 3000 |
| `dldo3_vol` | 3000 |

### DRAM

The real memory parameters do not come from `script.bin` but from boot0's
eGON header — see [image-autopsy.en.md](image-autopsy.en.md) §2.

## Why it is critical

Without the correct `script.bin`:

- RAM may fail to initialize;
- the screen stays off;
- **boot fails silently** — no log, no message, no indication of which
  stage broke.

That last point now has a solution: see
[serial-console.en.md](serial-console.en.md).

## Practical consequences

1. **There is no "just swap the DTB".** A mainline A33 `.dtb` is read
   neither by this U-Boot nor by this kernel.
2. **Editing requires understanding.** sunxi-tools converts
   `script.bin` ↔ readable `FEX`, but one wrong DRAM or display value
   leaves the console with no image.
3. **Porting a modern system = rebuilding this as a Device Tree.** The good
   part: the values needed are no longer locked inside the blob, they are in
   the tables above.

## Path to a mainline Device Tree

The A33 (`sun8i-a33`) **has mainline support**. What already exists:

| Component | Mainline status |
|---|---|
| SoC | `sun8i-a33.dtsi` |
| Mali-400 GPU | **Lima** (Mesa), GLES 2.0 |
| Display Engine | `sun4i-drm` + `sun8i-mixer` |
| MIPI DSI | `sun6i-mipi-dsi` |
| AXP223 PMIC | `axp20x` |
| MMC / USB / I2C / UART | supported |
| `jd9366` panel | **missing — this is the new work** |

The panel's DSI init sequence has to be extracted from the `jd9366_8inch`
driver inside the vendor's 3.4 kernel (`SYSTEM`, lzo squashfs).

## Open items

- [x] Locate `script.bin`
- [x] Parse and document display, UART and PMIC
- [ ] Convert to FEX (`bin2fex`) and version the full readable form
- [ ] Map the control GPIO pins (buttons and analog sticks)
- [ ] Extract the DSI sequence from the vendor kernel's `jd9366_8inch` driver
- [ ] Write the board `.dts` and validate over serial
