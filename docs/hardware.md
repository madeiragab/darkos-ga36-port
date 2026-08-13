> 🇧🇷 **Português** · 🇬🇧 [English](hardware.en.md)

# Hardware — GA36-MB (V1.1) — documentação local

**Propósito:** reunir de forma concisa e verificável tudo o que sabemos sobre a placa do console que você abriu (GA36-MB V1.1).  
Este arquivo é operacional: atualize sempre que confirmar algo novo (fotos, dumps, leituras).

---

## Metadados

```
Board:     GA36-MB
Revision:  V1.1 (2025-10-25)
SoC:       Allwinner A33 (sun8iw5p1) — Cortex-A7 quad, ARMv7 32-bit
GPU:       Mali-400 (GLES 2.0)
RAM:       1 GB DDR3 @552 MHz (~850 MB utilizáveis)
Panel:     640x480, MIPI DSI 2 lanes, jd9366_8inch
PMIC:      AXP22x
Kernel:    Linux 3.4.39 (sunxi legacy)
OS_stock:  EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
Boot:      microSD (boot.img Android + script.bin)
Serial:    UART2 — TX=PB0, RX=PB1, 115200 8N1
State:     boot funcional, backup do SD verificado
```


---

## Identificação e resumo curto

- **Placa:** `GA36-MB`
- **Revisão confirmada nesta unidade:** **V1.1** (`GA36-MB V1.1-20251025`) — confirmado pelo silk na PCB.
- **SoC real:** **Allwinner A33** (`sun8iw5p1`) — ARM Cortex-A7 quad-core,
  **ARMv7 32-bit**.
- **Observação sobre remarking:** o encapsulamento do chip traz silk
  indicando Rockchip RK3326. É remarking. Ver seção "Provas".
- **Firmware stock:** EmuELEC 4.7 (`EE_VERSION` = `4.7`), build
  `GA36-UDT-EE-TF-R-20250818` — fork não oficial adaptado para A33.
- **Boot:** formato Android `boot.img` (kernel + ramdisk) e **script.bin**
  (Allwinner legacy) — **não** DTB padrão.

---

## Fotos

Já no repositório:

- [`images/pcb_front.jpg`](../images/pcb_front.jpg) — placa inteira
- [`images/soc_allwinner_a33.png`](../images/soc_allwinner_a33.png) — close do SoC
- [`images/ram_ddr_chips.png`](../images/ram_ddr_chips.png) — close dos chips de RAM
- [`images/serial_pads.png`](../images/serial_pads.png) — pads candidatos a TX/RX/GND

Ainda faltando:

- `images/display_fpc.*` — conector FPC do display
- Foto anotada correlacionando os pads de serial com **PB0/PB1** — ver
  [serial-console.md](serial-console.md) para o método de identificação.

---

## Componentes identificados (estado atual)

| Componente | Valor | Origem da confirmação |
|---|---|---|
| SoC | Allwinner A33 (`sun8iw5p1`), Cortex-A7 quad | strings da imagem, header do boot.img |
| GPU | Mali-400 (GLES 2.0, sem S3TC) | logs do EmuELEC |
| Memória | **1 GB DDR3 @552 MHz**, 2 chips, barramento 32 bits | `dram_para` do header eGON |
| RAM utilizável | **~850 MB** (176 MB de CMA + 150 MB de carveout) | bootargs do U-Boot |
| PMIC | **AXP22x** (família AXP223) | `power_sply` e `lcd_power` do script.bin |
| Display | **640 × 480**, MIPI DSI 2 lanes, painel `jd9366_8inch` | `lcd0_para` do script.bin |
| Backlight | PWM canal 0 @20 kHz | `lcd0_para` |
| Armazenamento | slot microSD (boot exclusivo pelo SD) | — |
| Serial de debug | **UART2, TX=PB0, RX=PB1, 115200** | `uart_para` do script.bin |
| Entradas | 2 analógicos + botões (GPIO) | **mapeamento ainda não documentado** |
| Áudio | speaker mono | pino de enable ainda não localizado |

Trilhas da PMIC (`power_sply`, em mV): `dcdc1`=3000, `dcdc2`=1100,
`dcdc3`=1200, `dcdc4`=0, `dcdc5`=1500, `aldo2`=2500, `aldo3`=3000,
`dldo3`=3000.

Detalhes e offsets: [image-autopsy.md](image-autopsy.md) e
[device-tree.md](device-tree.md).

---

## Provas técnicas que confirmam Allwinner A33

Confirmado por leitura direta da imagem, sem depender de acesso ao console:

| Evidência | Offset | Valor |
|---|---|---|
| String de máquina | `0x01a307e7f` | `sun8iw5p1` |
| String de máquina | `0x005bb2518` | `sun8iw5` |
| Nome no header do boot.img | `0x05400000` | `sun8i` |
| Assinatura do bootloader | `0x00002004` | `eGON.BT0` |
| Versão do kernel | `0x005a4e899` | `Linux version 3.4.39 (lxl@lxl)` |
| Endereço de carga | header | `0x40008000` (ARM 32-bit) |

`sun8iw5p1` é o codinome interno da Allwinner para o A33 — não é A133
(`sun50iw10`), não é H3 (`sun8iw7`), não é Rockchip.

Confirmação adicional no aparelho:

```bash
cat /proc/cpuinfo    # sun8i / identificador Allwinner
uname -a             # kernel sunxi 3.4.39
free -h              # confirmar a decodificação de 1 GB
dmesg | grep -i mali # Mali-400
```

> O silk do chip **não** é fonte definitiva.

---

## Layout de partições

Layout completo e confirmado em **[storage.md](storage.md)**. Resumo:

| Dispositivo | Offset | Tamanho | Conteúdo |
|---|---|---|---|
| `mmcblk0p1` | 2420 MB | ROMs | FAT32 |
| `mmcblk0p2` | 36 MB | 32 MB | `Volumn` — fontes, bootlogo |
| `mmcblk0p5` | 68 MB | 16 MB | environment do U-Boot (raw) |
| `mmcblk0p6` | 84 MB | 32 MB | `boot.img` (raw) |
| `mmcblk0p7` | 116 MB | 768 MB | `/flash` — contém `SYSTEM` |
| `mmcblk0p8` | 884 MB | 1536 MB | `/storage` (ext4) |

> **ATENÇÃO:** não sobrescrever nem formatar sem backup bit-a-bit. E leia o
> aviso sobre o Windows em [storage.md](storage.md) — ele pode gravar sobre
> o `boot.img` sem você pedir.

---

## Comandos essenciais 
Execute **exatamente** estes comandos e commite as saídas:

```bash
mkdir -p dumps/bootlogs dumps/partitions
cat /proc/cpuinfo > dumps/bootlogs/cpuinfo.txt
uname -a > dumps/bootlogs/uname.txt
dmesg > dumps/bootlogs/dmesg.txt
ls /lib/modules -la > dumps/bootlogs/modules.txt
No PC com o SD inserido (substitua /dev/sdX pelo seu dispositivo):

lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINT > dumps/partitions/lsblk.txt
blkid > dumps/partitions/blkid.txt
sudo fdisk -l /dev/sdX > dumps/partitions/fdisk.txt
