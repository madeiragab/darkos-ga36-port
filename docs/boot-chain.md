# Cadeia de boot

Entender esta cadeia é pré-requisito para qualquer modificação. Cada elo
depende do anterior de forma rígida — o Allwinner A33 com U-Boot legado é
sensível ao **layout físico** do cartão SD, não apenas ao conteúdo das
partições.

## Visão geral

```text
BROM (ROM interna do SoC, imutável)
   │  procura bootloader em offset fixo do microSD
   ▼
U-Boot (partição raw, ~16 MB)
   │  específico da placa; entende o layout antigo do SD
   │  lê a configuração de hardware
   ▼
script.bin / magic.bin (Allwinner legacy)
   │  inicializa DRAM, GPIO, clocks, display
   ▼
bootimg (formato Android, ~32 MB)
   │  contém kernel + ramdisk
   ▼
Kernel Linux sunxi 3.4.x
   │  monta as partições do sistema
   ▼
EmuELEC 4.7 (build GA36-UDT-EE-TF-R-20250818)
```

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

## Estado da documentação

| Elo | Estado |
|---|---|
| Existência e ordem da cadeia | Confirmado pela autópsia de referência |
| Offsets exatos de cada estágio | **Pendente** — requer dump e análise do primeiro KB do SD |
| Conteúdo do environment do U-Boot | **Pendente** |
| Log completo de boot via serial | **Pendente** — requer identificar os pads TX/RX/GND |

Fonte primária dos artefatos:
[../reference/autopsy/files.md](../reference/autopsy/files.md).
