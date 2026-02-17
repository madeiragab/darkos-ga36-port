# Hardware Overview — GA36-MB (V1.1) — documentação local

**Propósito:** consolidar fatos confirmados sobre a placa que você abriu (GA36-MB V1.1-20251025) e ligar esses fatos à autópsia publicada (V1.0). Documento operacional: atualizar sempre que confirmar algo novo.

---

## Metadados
- **Board:** GA36-MB  
- **Revisão (este dispositivo):** V1.1 (`GA36-MB V1.1-20251025`) — confirmado por silk na PCB (foto).  
- **Referência externa:** R36S console clone autopsy (GA36-MB V1.0) — ver `reference_autopsy.md`.  
- **SoC:** Allwinner A33 (ARM Cortex-A7, quad-core) — CONFIRMADO.  
- **Firmware stock:** EmuELEC ES v4.7 (build `GA36-UDT-EE-TF-R-20250818`) — CONFIRMADO.  
- **Boot:** a partir de microSD (bootimg + script.bin / partições conforme autopsy) — CONFIRMADO.  
- **Estado atual do dispositivo:** Boot funcional; backup do SD feito.

---

## Componentes identificados (fotos em `/images/`)
- **SoC:** Allwinner A33 (posicionado centro-superior) — foto: `images/ga36_mb_v1.1_soc.jpg` (adicione).  
- **Memória RAM:** 2x chips DDR3 ao lado do SoC — ler marca/modelo nas fotos macro (ACTION).  
- **Conector de display:** FPC central acima dos botões.  
- **Speaker:** integrado (centro) com conector `SPK`.  
- **Conector de bateria:** JST (marcado `BAT`).  
- **Entradas:** dois módulos analógicos (joysticks), múltiplos botões (soldados diretamente).  
- **Portas externas:** microSD, micro-USB OTG, porta DC (inferior).  
- **Silk/Pads relevantes:** marcações `GND TX RX` perto do topo (possível pad serial) — CONFIRMAR com foto macro.

---

## Diferenças importantes vs autópsia (V1.0)
- **Revisão:** você tem V1.1; autópsia principal documenta V1.0.  
- **Risco:** V1.1 pode ter variações em pinos GPIO, enable pins de backlight/áudio ou reguladores. Não assumir compatibilidade elétrica completa.  
- **Oportunidade:** a autópsia contém dumps e recovery image que provavelmente funcionam como baseline; usar como referência reduz risco.

---

## Partições / storage (confirmar com comandos)
**A fazer agora** (cole as saídas em `dumps/partitions/`):
- `lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINT`  
- `blkid`  
- `sudo fdisk -l /dev/sdX` (no PC, SD inserido)

**O que esperamos (segundo autopsy):**
- pequena partição FAT (~32M) com `script.bin` / boot resources
- partição raw com U-Boot config
- boot partition com Android bootimg (kernel+ramdisk)
- SYSTEM squashfs
- partition overlay rw (configs, logs, cores)

*(Não sobrescrever, apenas ler e salvar dumps.)*

---

## Boot / Kernel / DTB
- **Kernel detectado no autopsy:** Linux `3.4.39` (sunxi).  
- **Formato de DTB:** sistema usa `script.bin` / `magic.bin` (Allwinner legacy) — **sem DTB separado** no sentido moderno.  
- **Implicação:** port para kernel moderno ou deploy de DarkOS requer (A) manter bootimg/script.bin ou (B) converter/recriar DTB e adaptar bootchain. Ambas ações têm trabalho não trivial.

---

## Pontos para confirmar (checklist imediato)
Coloque resultados em `dumps/` e atualize esse arquivo:

- [ ] Foto macro do SoC com leitura do ID do chip.  
- [ ] Foto macro dos chips de RAM com marca/modelo.  
- [ ] Localizar pads TX/RX/GND (serial) e tirar foto (marcar coordenada aproximada na PCB).  
- [ ] `cat /proc/cpuinfo` (quando rodar EmuELEC) → salvar em `dumps/bootlogs/cpuinfo.txt`.  
- [ ] `uname -a` → salvar em `dumps/bootlogs/uname.txt`.  
- [ ] `dmesg > dumps/bootlogs/dmesg.txt`.  
- [ ] `ls /lib/modules -la > dumps/kernel/modules_list.txt`.  
- [ ] `lsblk`, `blkid`, `fdisk -l` do SD (no PC) → salvar em `dumps/partitions/`.

---

## Comandos recomendados (cole saídas em `dumps/`)
Executar no EmuELEC/console (ou chroot se extrair SYSTEM):

```bash
# no sistema em execução:
cat /proc/cpuinfo > dumps/bootlogs/cpuinfo.txt
uname -a > dumps/bootlogs/uname.txt
dmesg > dumps/bootlogs/dmesg.txt
ls /lib/modules -la > dumps/bootlogs/modules.txt

# no PC com SD montado:
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINT > dumps/partitions/lsblk.txt
blkid > dumps/partitions/blkid.txt
sudo fdisk -l /dev/sdX > dumps/partitions/fdisk.txt
