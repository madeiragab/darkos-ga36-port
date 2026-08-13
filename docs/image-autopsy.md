> 🇧🇷 **Português** · 🇬🇧 [English](image-autopsy.en.md)

# Autópsia da imagem (software)

Complemento da autópsia física em [`reference/autopsy/`](../reference/autopsy/).
Enquanto aquela documenta a PCB, esta documenta o **conteúdo do cartão**:
offsets, estruturas, configuração e defeitos, todos extraídos por leitura
direta de uma imagem de recovery de 2425 MB.

**Método:** parsing offline, sem montar nada e sem depender de Linux.
Ferramentas em [`tools/`](../tools/). Todo valor abaixo tem um offset
verificável — nada aqui é inferido de documentação de terceiros.

**Amostra:** `r36s-a33-recovery.img`, 2 543 237 120 bytes.
**Unidade:** GA36-MB V1.1 (2025-10-25).

---

## 1. Identificação definitiva do SoC

O silk diz RK3326. Não é. Quatro evidências independentes, todas na imagem:

| Evidência | Offset | Valor |
|---|---|---|
| String de máquina | 0x01a307e7f | `sun8iw5p1` |
| String de máquina | 0x005bb2518 | `sun8iw5` |
| Nome no header do boot.img | 0x05400000 | `sun8i` |
| Assinatura do bootloader | 0x00002004 | `eGON.BT0` |
| Endereço de carga do kernel | header | `0x40008000` (ARM 32-bit) |

`sun8iw5p1` é o codinome interno da Allwinner para o **A33**. Não há
ambiguidade: não é A133 (`sun50iw10`), não é H3 (`sun8iw7`), não é
Rockchip.

**Consequência:** Cortex-A7, **ARMv7 32-bit**. Qualquer software que exija
ARM64 (box64, builds aarch64) está descartado por arquitetura, não por
desempenho.

---

## 2. Memória — parâmetros de DRAM do boot0

O header eGON em `0x2000` carrega a estrutura `dram_para` usada pelo boot0
para inicializar a memória. Estes valores são o que a placa realmente usa:

| Campo | Offset | Valor |
|---|---|---|
| `dram_clk` | 0x2038 | 552 MHz |
| `dram_type` | 0x203C | 3 (DDR3) |
| `dram_zq` | 0x2040 | `0x00003bbb` |
| `dram_odt_en` | 0x2044 | 1 |
| `dram_para1` | 0x2048 | `0x10f20200` |
| `dram_para2` | 0x204C | 0 |
| `dram_mr0` | 0x2050 | `0x1840` |
| `dram_mr1` | 0x2054 | `0x40` |
| `dram_mr2` | 0x2058 | `0x8` |
| `dram_mr3` | 0x205C | 0 |

`dram_para1 = 0x10f20200` com os 2 chips DDR3 da placa decodifica em
15 linhas × 10 colunas × 8 bancos × barramento 32 bits = **1 GB**.

> A decodificação do encoding de `para1` é inferência e deve ser confirmada
> com `free -h` ou `dmesg | grep -i memory` na unidade.

**RAM realmente disponível é menor.** Os bootargs reservam:

```
ion_cma_1g=176m  ion_carveout_1g=150m  coherent_pool=4m
```

Sobram aproximadamente **850 MB** para o sistema.

---

## 3. Cadeia de boot — offsets exatos

Fecha a pendência "offsets exatos de cada estágio" de
[boot-chain.md](boot-chain.md).

| Estágio | Offset | Tamanho | Detalhe |
|---|---|---|---|
| boot0 (`eGON.BT0`) | `0x00002000` (setor 16) | 32 768 B | `pub_head_size = 48` |
| U-Boot | `~0x01320000` (20,06 MB) | — | `U-Boot 2017.09-g05bceb2-dirty #lxl (Jul 14 2025 - 11:58:12 +0800)` |
| `script.bin` | `0x01366000` (19,40 MB) | — | 78 seções |
| Environment do U-Boot | `0x04400000` (68 MB) | — | ver seção 4 |
| `boot.img` | `0x05400000` (84 MB) | — | header Android |

### Header do `boot.img`

| Campo | Valor |
|---|---|
| `page_size` | 2048 |
| kernel | 13 213 848 B (12,60 MB) @ `0x40008000` |
| ramdisk | 3 040 904 B (2,90 MB) @ `0x41000000` |
| second | 0 |
| `tags_addr` | `0x40000100` |
| `name` | `sun8i` |
| `cmdline` | **vazia** |
| ramdisk | `0x0609b000`, gzip (`1f8b0800`) |

A `cmdline` vazia no header é o motivo de os bootargs virem inteiramente do
environment do U-Boot.

---

## 4. Environment do U-Boot

Fecha a pendência "conteúdo do environment do U-Boot". Extraído de
`0x04400000`:

```
bootdelay=0
bootcmd=run setargs_mmc boot_normal
console=ttyS2,115200
nand_root=/dev/nandd
mmc_root=/dev/mmcblk0p7
init=/init
disk=/dev/mmcblk0p8
loglevel=0
setargs_mmc=setenv bootargs console=${console} root=${mmc_root} init=${init} disk=${disk} ion_cma_512m=8m ion_cma_1g=176m ion_carveout_512m=0m ion_carveout_1g=150m coherent_pool=4m loglevel=${loglevel} partitions=${partitions}
boot_normal=sunxi_flash read 40007800 boot;boota 40007800
```

Pontos que importam:

- `boot_normal` usa **`sunxi_flash`**, ou seja, a tabela de partições
  proprietária da Allwinner — não a MBR. A MBR existe em paralelo, para o
  kernel.
- `loglevel=0` e `bootdelay=0`: silêncio total no boot. Ver
  [serial-console.md](serial-console.md) para por que isso é o maior
  obstáculo prático do projeto.
- `disk=/dev/mmcblk0p8` e `root=/dev/mmcblk0p7` estão **corretos** e
  correspondem ao layout real.

---

## 5. Layout de partições

Fecha a tabela aproximada que existia em [storage.md](storage.md).

### MBR primária

| Slot | Tipo | Início (LBA) | Setores | Conteúdo |
|---|---|---|---|---|
| p1 | `0x0b` FAT32 | 4 956 161 | 11 099 (5,42 MB) | ROMs — **ver defeito abaixo** |
| p2 | `0x06` FAT16 | 73 728 | 65 536 (32 MB) | `Volumn` — flag de boot `0x80` |
| p3 | `0x85` estendida | 1 | 4 956 160 (2420 MB) | contêiner da área do fabricante |

### Partições lógicas (dentro de p3)

| Dispositivo | Início (LBA) | Tamanho | Filesystem | Papel |
|---|---|---|---|---|
| `mmcblk0p5` | 139 264 (68 MB) | 16 MB | raw | environment do U-Boot |
| `mmcblk0p6` | 172 032 (84 MB) | 32 MB | raw | `boot.img` |
| `mmcblk0p7` | 237 568 (116 MB) | 768 MB | FAT16 `EMUELEC` | `/flash` — contém `SYSTEM` |
| `mmcblk0p8` | 1 810 432 (884 MB) | 1536 MB | ext4 | `/storage` |

### Conteúdo relevante

- **p7** (`/flash`): `SYSTEM` (425 447 424 B) e `LOW_PWR.BMP`.
  `SYSTEM` é squashfs **lzo**, 405,74 MB, bloco 524 288, 12 276 inodes,
  compilado em **2025-08-22 12:45**.
- **p2** (`Volumn`): `font32.sft`, `font24.sft`, `bootlogo.bmp`,
  `magic.bin` (512 B), `bat/`.
- **p8** (`/storage`): ext4, bloco 4096, 98 304 inodes, inode de 256 B.
  `state = clean`, contador de montagens **53**, último check 2025-05-13.

### Compatibilidade do ext4 com o kernel 3.4

Verificado por leitura do superbloco — importa porque descarta uma hipótese
comum de falha:

```
compat    0x0000003c : has_journal, ext_attr, resize_inode, dir_index
incompat  0x000002c2 : filetype, extents, 64bit, flex_bg
ro_compat 0x0000006b : sparse_super, large_file, huge_file, dir_nlink, extra_isize
```

Nenhuma feature fora do que o Linux 3.4 suporta. O `/storage` **monta em
leitura e escrita** sem restrição.

---

## 6. Defeitos encontrados na imagem

### 6.1 MBR com erro de um setor na p1

A entrada 1 da MBR aponta para **LBA 4956161**. O boot sector FAT32 real
está em **LBA 4956160**. Além de errado, 4956161 não é alinhado a 2048,
enquanto 4956160 é exatamente `2048 × 2420`.

Efeito: o Windows formata um filesystem novo no offset errado e desalinha
a partição, com penalidade permanente de desempenho em cartão SD.

### 6.2 Partição de ROMs truncada

A imagem de recovery distribuída declara a p1 com **11 099 setores
(5,42 MB)**, embora o BPB FAT32 interno declare 48 779 MB. Quem grava essa
imagem recebe uma partição de ROMs inutilizável e o EmulationStation falha
com:

```
we can't find any systems
```

Correção: reescrever a entrada da MBR e gerar um FAT32 novo ocupando o
cartão. Ver [`tools/`](../tools/).

### 6.3 `Volumn` mente o próprio tamanho — risco de brick

**Este é o defeito mais perigoso do conjunto.**

| Fonte | Tamanho declarado |
|---|---|
| Entrada da MBR (p2) | **32 MB** |
| BPB dentro da partição | **128 MB** |

O Windows monta o volume usando o **BPB**, então enxerga 128 MB e considera
gravável a faixa de 36 MB a 164 MB do cartão. Dentro dessa faixa estão:

- `boot.img` em **84 MB**
- `SYSTEM` em **116 MB**

Qualquer escrita do Windows que ultrapasse os 32 MB reais grava **em cima
do boot**. E o Windows escreve sozinho: cria `System Volume Information`
ao montar.

> **Nunca copie nada para a partição `Volumn`. Nunca deixe o Windows
> "reparar" esse volume.** Se ele oferecer formatação, cancele.

### 6.4 `fsck.auto` não existe no initramfs

O `init` chama, sem especificar tipo:

```sh
fsck -T -M -p -a $RUN_FSCK_DISKS
```

A detecção de tipo falha e ele procura `/sbin/fsck.auto`. O initramfs tem
`e2fsck`, `fsck.ext2`, `fsck.fat`, `fsck.exfat` — **não tem `fsck.ext4` nem
`fsck.auto`**. Resultado registrado no próprio `init.log` da imagem:

```
fsck: fsck.auto: No such file or directory
fsck: fsck.auto: No such file or directory
mount: mounting /run on /sysroot/run failed: Invalid argument
```

O `/storage` nunca é verificado após desligamento sujo.

---

## 7. Ferramentas

Todas em [`tools/`](../tools/), Python puro, somente leitura salvo onde
indicado. Rodam em Windows sem WSL.

| Ferramenta | Função |
|---|---|
| `ext4_reader.py` | Lê ext4 (extents, inodes, diretórios) direto de imagem crua |
| `scriptbin_parse.py` | Localiza e parseia `script.bin` legacy Allwinner |
| `partition_map.py` | MBR + cadeia de partições estendidas |
| `boot_header.py` | Header do `boot.img` Android + varredura de superblocos |
| `uboot_env.py` | Extrai o environment do U-Boot |
| `verify_card.py` | Compara cartão × imagem byte a byte (somente leitura) |

---

## 8. O que isto muda no escopo do projeto

[kernel.md](kernel.md) afirmava que recompilar estava fora de alcance por
falta de informação sobre a placa. Boa parte dessa informação agora existe:

| Pré-requisito | Antes | Agora |
|---|---|---|
| Backup verificado | ✅ | ✅ |
| Mapa da cadeia de boot | ❌ | ✅ offsets exatos |
| Environment do U-Boot | ❌ | ✅ completo |
| Acesso serial | ❌ | ✅ PB0/PB1 identificados |
| Dados para device tree | ❌ | ✅ LCD, PMIC, UART, DRAM |
| Device tree e kernel novos | ❌ | ❌ **trabalho restante** |
| Procedimento de recuperação | parcial | parcial |

O que falta virou concreto e enumerável, em vez de desconhecido. Ver
[device-tree.md](device-tree.md) para os valores extraídos e
[serial-console.md](serial-console.md) para o próximo passo prático.
