> 🇧🇷 **Português** · 🇬🇧 [English](README.en.md)

# Ferramentas de análise

Scripts usados para produzir [`docs/image-autopsy.md`](../docs/image-autopsy.md).

**Python 3 puro, sem dependências externas.** Rodam em Windows sem WSL, e
em Linux sem instalar nada. Foram escritos porque as ferramentas usuais
(`losetup`, `mount`, `unsquashfs`, sunxi-tools) não estão disponíveis em
Windows e montar a imagem no Linux era desnecessário para só ler.

**Todas são somente leitura.** Nenhuma delas escreve na imagem ou no cartão.

## Uso

Todas recebem o caminho da imagem (ou do dispositivo) como argumento.

```bash
# mapa completo de partições, MBR + cadeia estendida + bootloader
python partition_map.py r36s-a33-recovery.img

# header do boot.img + varredura de superblocos
python boot_header.py r36s-a33-recovery.img

# environment do U-Boot
python uboot_env.py r36s-a33-recovery.img

# script.bin: lista as seções
python scriptbin_parse.py r36s-a33-recovery.img
# ... e despeja as que interessam
python scriptbin_parse.py r36s-a33-recovery.img uart_para lcd0_para power_sply

# ext4 /storage: listar e ler arquivos sem montar
python ext4_reader.py r36s-a33-recovery.img 0x37400000 ls:/
python ext4_reader.py r36s-a33-recovery.img 0x37400000 cat:/.config/EE_VERSION
```

## Comparar cartão com imagem

`verify_card.py` é a única que toca em hardware, e **só lê**. Serve para
responder "o boot foi corrompido?" sem arriscar piorar o estado.

```bash
# Linux
sudo python3 verify_card.py r36s-a33-recovery.img /dev/sdX
```

```powershell
# Windows, PowerShell como Administrador
python verify_card.py r36s-a33-recovery.img \\.\PhysicalDrive1
```

Ela verifica as quatro estruturas críticas (boot0, boot.img, SYSTEM, ext4),
compara tudo byte a byte e classifica cada diferença por região.

> Diferenças dentro do `ext4 /storage` são **normais** depois de qualquer
> boot — o EmuELEC grava log e configuração. Diferenças em `boot.img` ou na
> área raw **não são**, e indicam o problema descrito em
> [image-autopsy.md](../docs/image-autopsy.md) §6.3.

## Offsets desta placa

Valem para a imagem de recovery do GA36-MB V1.1. Confirme com
`partition_map.py` antes de assumir que a sua mídia é idêntica.

| Offset | Conteúdo |
|---|---|
| `0x00002000` | boot0 (`eGON.BT0`), setor 16 |
| `0x01320000` | U-Boot 2017.09 |
| `0x01366000` | `script.bin` |
| `0x04400000` | environment do U-Boot |
| `0x05400000` | `boot.img` |
| `0x07400000` | FAT16 `EMUELEC` (`/flash`, contém `SYSTEM`) |
| `0x37400000` | ext4 (`/storage`) |
| `0x97400000` | FAT32 (ROMs) |

## Limitações conhecidas

- `ext4_reader.py` não lê diretórios com hash tree quando o `rec_len`
  estiver corrompido; para uma imagem sadia funciona.
- `scriptbin_parse.py` decodifica os tipos word, string e GPIO. Valores do
  tipo multi-word aparecem como "não decodificado".
- O `SYSTEM` é squashfs comprimido com **lzo**, que a stdlib do Python não
  descomprime. Ler o conteúdo dele exige `unsquashfs` com suporte a lzo.
