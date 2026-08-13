> 🇧🇷 **Português** · 🇬🇧 [English](boot-chain.en.md)

# Cadeia de boot

Entender esta cadeia é pré-requisito para qualquer modificação. Cada elo
depende do anterior de forma rígida — o Allwinner A33 com U-Boot legado é
sensível ao **layout físico** do cartão SD, não apenas ao conteúdo das
partições.

## Visão geral

Offsets confirmados por leitura direta da imagem — método em
[image-autopsy.md](image-autopsy.md).

```text
BROM (ROM interna do SoC, imutável)
   │  procura o bootloader no setor 16 do microSD
   ▼
boot0 "eGON.BT0"                          @0x00002000  (setor 16, 32 KB)
   │  inicializa a DRAM com os parâmetros do próprio header
   ▼
U-Boot 2017.09                            @0x01320000  (~20 MB)
   │  build do vendor: -g05bceb2-dirty #lxl (Jul 14 2025)
   ▼
script.bin (Allwinner legacy)             @0x01366000  (19,40 MB)
   │  GPIO, clocks, display, UART, PMIC — 78 seções
   ▼
environment do U-Boot                     @0x04400000  (68 MB)
   │  monta os bootargs; define root= e disk=
   ▼
boot.img (formato Android)                @0x05400000  (84 MB)
   │  kernel 12,60 MB @0x40008000 + initramfs 2,90 MB gzip
   ▼
Kernel Linux sunxi 3.4.39
   │  monta /flash (mmcblk0p7) e /storage (mmcblk0p8)
   ▼
EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
```

> Correção em relação a versões anteriores deste documento: o `script.bin`
> **não** fica na partição FAT16 `Volumn`. Ele está na área raw, junto ao
> U-Boot. A FAT16 contém apenas fontes, `bootlogo.bmp` e `magic.bin`.

## Por que cada elo importa

### BROM
Gravada no silício, não pode ser alterada. Ela busca o bootloader em um
offset fixo do cartão — é por isso que **recriar o SD com um particionador
comum quebra o boot** mesmo que todos os arquivos estejam presentes.

### U-Boot
Reside em uma partição **raw** (sem sistema de arquivos), com environment e
parâmetros específicos da placa. Carrega o `boot.img` no formato Android.

> U-Boot genérico ou moderno **não é compatível** sem adaptação profunda.

### script.bin / magic.bin
O equivalente conceitual a um Device Tree, em formato proprietário antigo —
detalhes em [device-tree.md](device-tree.md). Sem ele: a RAM pode não
inicializar, a tela não liga e o boot falha **silenciosamente**, sem
mensagem de erro.

### bootimg
Formato Android (kernel + ramdisk empacotados). Não é um `zImage` solto nem
um `uImage` — ferramentas que esperam esses formatos não servem aqui.

### Kernel
Linux sunxi legado (3.4.x). Ver [kernel.md](kernel.md).

## Implicações práticas

| Se você… | Resultado provável |
|---|---|
| Reparticionar o SD com layout novo | Brick — a BROM não acha o U-Boot |
| Gravar uma imagem pública de EmuELEC | Não boota (kernel incompatível com A33) |
| Trocar só o kernel, mantendo o script.bin | Falha silenciosa se o kernel não entender o formato legado |
| Perder o SD original sem backup | Console inutilizável |

## Environment do U-Boot

Extraído de `0x04400000`. É ele que constrói a linha de comando do kernel —
o header do `boot.img` tem `cmdline` **vazia**.

```
bootdelay=0
bootcmd=run setargs_mmc boot_normal
console=ttyS2,115200
mmc_root=/dev/mmcblk0p7
disk=/dev/mmcblk0p8
init=/init
loglevel=0
boot_normal=sunxi_flash read 40007800 boot;boota 40007800
```

Duas consequências importantes:

1. **`boot_normal` usa `sunxi_flash`**, ou seja, a tabela de partições
   proprietária da Allwinner — não a MBR. A MBR existe em paralelo, para o
   kernel. Por isso reparticionar com ferramenta comum quebra o boot mesmo
   quando os arquivos continuam lá.
2. **`loglevel=0` e `bootdelay=0`**: o boot é silencioso por projeto.
   Qualquer falha aparece como tela preta muda, indistinguível de aparelho
   sem energia.

## Estado da documentação

| Elo | Estado |
|---|---|
| Existência e ordem da cadeia | Confirmado |
| Offsets exatos de cada estágio | ✅ **Confirmado** — ver diagrama acima |
| Conteúdo do environment do U-Boot | ✅ **Confirmado** |
| Pinos do console serial | ✅ **PB0/PB1 @115200** — ver [serial-console.md](serial-console.md) |
| Log completo de boot via serial | **Pendente** — requer ligar o adaptador |
| Acesso ao prompt do U-Boot | **Pendente** — `bootdelay=0` sugere que não há janela |

Fonte primária dos artefatos:
[../reference/autopsy/files.md](../reference/autopsy/files.md) e
[image-autopsy.md](image-autopsy.md).
