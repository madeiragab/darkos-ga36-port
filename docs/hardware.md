# Hardware — GA36-MB (V1.1) — documentação local

**Propósito:** reunir de forma concisa e verificável tudo o que sabemos sobre a placa do console que você abriu (GA36-MB V1.1).  
Este arquivo é operacional: atualize sempre que confirmar algo novo (fotos, dumps, leituras).

---

## Metadados 
Board: GA36-MB
Revision: V1.1 (2025-10-25)
SoC: Allwinner A33
OS_stock: EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
Boot: microSD (bootimg + script.bin)
State: boot funcional, SD backup realizado


---

## Identificação e resumo curto

- **Placa:** `GA36-MB`  
- **Revisão confirmada nesta unidade:** **V1.1** (`GA36-MB V1.1-20251025`) — confirmado pelo silk na PCB.  
- **SoC real (comportamento confirmado):** :contentReference[oaicite:0]{index=0} A33 (ARM Cortex-A7, quad-core).  
- **Observação importante sobre remarking:** o encapsulamento do chip pode trazer silk indicando outro fornecedor (ex.: Rockchip), mas o comportamento do boot/kernel/GPU confirma Allwinner A33 (ver seção "Provas").  
- **Firmware stock:** :contentReference[oaicite:1]{index=1} 4.7 — custom build para A33.  
- **Boot:** a imagem usa formato Android `bootimg` (kernel + ramdisk) e **script.bin** (Allwinner legacy) — **não** DTB padrão.

---

## Fotos 
Tire exatamente estas fotos, sem desmontar mais do que o necessário:

- `images/pcb_front.jpg` — placa inteira (referência de layout)  
- `images/soc_allwinner_a33.jpg` — close do SoC (leitura do silk)  
- `images/ram_ddr_chips.jpg` — close dos chips de RAM (leitura do silk)  
- `images/serial_pads.jpg` — pads TX/RX/GND (ou área suspeita)  
- `images/display_fpc.jpg` — conector FPC do display

Adicione legendas breves nas imagens no repositório (ex: `soc_allwinner_a33.jpg — silk lido: ...`).

---

## Componentes identificados (estado atual)
- **SoC:** Allwinner A33 — CONFIRMADO por logs e comportamento do sistema.  
- **GPU:** Mali-400 — detectado nos logs do EmuELEC.  
- **Memória:** 2 × chips DDR3 (leitura dos modelos pendente).  
- **Armazenamento:** slot microSD (boot a partir do SD).  
- **Display:** interface FPC (timings não confirmados).  
- **Entradas:** 2 analógicos + botões (GPIO) — mapeamento não documentado.  
- **Áudio:** speaker mono (pino de enable pode ser dependente do DTB/script.bin).  
- **Pads de debug/serial:** existe área com pads próximos ao topo — confirmar TX/RX/GND com foto macro.

---

## Provas técnicas que confirmam Allwinner A33 
- `/proc/cpuinfo` mostrando `sun8i` / Allwinner identificador.  
- `uname -a` indicando kernel sunxi (ex.: `3.4.39` no dump).  
- `dmesg` reportando Mali-400 ou strings `sunxi`.  

> Se as três saídas acima existirem, considerar remarking: silk do chip NÃO é fonte definitiva.

---

## Layout de partições 
(salve as saídas em `dumps/partitions/`)

Exemplo (autópsia V1.0 — comparar com sua mídia):
img1: FAT32 grande (~ROMs) → roms / saves

img2: FAT16 / small (~32 MB) → magic.bin / boot resources

img5: raw (~16 MB) → uboot config (raw)

img6: bootimg (~32 MB) → Android bootimg (kernel + ramdisk)

img7: SYSTEM squashfs (~768 MB) → EmuELEC SYSTEM

img8: overlay rw (~1.5 GB) → userdata / configs / cores


**ATENÇÃO:** Não sobrescrever ou formatar essas partições sem backup bit-a-bit.

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
