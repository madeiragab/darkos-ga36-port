> 🇧🇷 **Português** · 🇬🇧 [English](storage.en.md)

# Armazenamento e layout de partições

O console **boota exclusivamente do microSD**. Não há eMMC nem NAND com
sistema de recuperação: se o cartão for perdido ou corrompido e não houver
backup, o console não tem como voltar a funcionar.

## Regra número um

> **Faça um backup bit-a-bit do SD original antes de qualquer experimento.**

Um backup de arquivos (copiar/colar) **não serve**. O boot depende do layout
físico do cartão, incluindo áreas raw fora de qualquer sistema de arquivos.

```bash
# No PC, com o SD inserido — substitua /dev/sdX pelo dispositivo correto.
# Confira DUAS VEZES o alvo: apontar para o disco errado destrói dados.
sudo dd if=/dev/sdX of=backup-sd-original.img bs=4M status=progress conv=sync,noerror
sha256sum backup-sd-original.img > backup-sd-original.img.sha256
```

Guarde a imagem **e** o hash em pelo menos dois lugares diferentes.

---

## ⚠️ Perigo específico do Windows

**Esta é a forma mais provável de destruir o console por acidente, e ela
não exige que você faça nada de errado conscientemente.**

A partição `Volumn` declara tamanhos contraditórios:

| Fonte | Tamanho |
|---|---|
| Entrada da MBR | **32 MB** |
| BPB dentro da partição | **128 MB** |

O Windows monta o volume usando o **BPB**. Ele acredita que pode escrever
de 36 MB a 164 MB do cartão. Nessa faixa estão:

- **`boot.img` em 84 MB**
- **`SYSTEM` em 116 MB**

E o Windows escreve por conta própria: ao montar o volume ele cria
`System Volume Information`.

**Regras práticas:**

- Nunca copie nada para a partição `Volumn` (aparece como `D:` ou similar).
- Se o Windows perguntar "é preciso formatar o disco", clique **Cancelar**.
- Nunca aceite "reparar" esse volume.
- Ao gravar uma imagem, deixe o disco desmontado e retire o cartão sem
  deixar o Windows remontá-lo. Desligar o automount ajuda:

```
diskpart
automount disable
```

(reversível com `automount enable`)

Para saber se o dano já ocorreu, use
[`tools/verify_card.py`](../tools/verify_card.py) — é somente leitura.

---

## Layout de partições (confirmado)

Medido na imagem de recovery da unidade V1.1. Método e offsets em
[image-autopsy.md](image-autopsy.md).

### MBR primária

| Slot | Tipo | Início (LBA) | Tamanho | Conteúdo |
|---|---|---|---|---|
| p1 | `0x0b` FAT32 | 4 956 161 | 5,42 MB¹ | ROMs, saves |
| p2 | `0x06` FAT16 | 73 728 | 32 MB | `Volumn` — fontes, bootlogo, `magic.bin` |
| p3 | `0x85` estendida | 1 | 2420 MB | contêiner da área do fabricante |

¹ tamanho da imagem de recovery distribuída — ver "Defeitos" abaixo.

### Partições lógicas (dentro de p3)

| Dispositivo | Início | Tamanho | Filesystem | Papel |
|---|---|---|---|---|
| `mmcblk0p5` | 68 MB | 16 MB | raw | environment do U-Boot |
| `mmcblk0p6` | 84 MB | 32 MB | raw | `boot.img` (kernel + initramfs) |
| `mmcblk0p7` | 116 MB | 768 MB | FAT16 `EMUELEC` | `/flash` — contém `SYSTEM` |
| `mmcblk0p8` | 884 MB | 1536 MB | ext4 | `/storage` |

O U-Boot referencia estas partições explicitamente:
`root=/dev/mmcblk0p7`, `disk=/dev/mmcblk0p8`.

Pontos que costumam pegar quem mexe pela primeira vez:

- **p5 e p6 são raw**: não têm sistema de arquivos. Ferramentas gráficas de
  particionamento as tratam como "espaço não alocado" e as destroem sem
  aviso.
- **`SYSTEM` é squashfs somente leitura** (405 MB, comprimido com lzo).
  Alterações de sistema vivem no ext4 de `mmcblk0p8`.
- **p2 e p3 se sobrepõem** na tabela — p2 fica dentro da faixa de p3. É
  assim de fábrica e funciona; não "conserte".
- **A ordem e os offsets importam** — ver [boot-chain.md](boot-chain.md).

---

## Defeitos da imagem de recovery distribuída

Além do problema do `Volumn` acima:

**Partição de ROMs truncada.** A entrada da MBR declara 11 099 setores
(5,42 MB) enquanto o BPB interno declara 48 779 MB. Quem grava a imagem
recebe uma partição inutilizável e o EmulationStation falha com
`we can't find any systems`.

**MBR com erro de um setor.** A entrada aponta LBA 4956161; o boot sector
FAT32 real está em 4956160 — que também é o valor alinhado a 2048.

Correção: reescrever a entrada da MBR (início 4956160, tamanho até o fim do
cartão) e gerar um FAT32 novo com label `EEROMS`. O Windows não formata
FAT32 acima de 32 GB com as ferramentas nativas, então isso precisa ser
feito com `mkfs.vfat -F 32` no Linux ou com um gerador próprio.

Depois de corrigir, o EmulationStation ainda esconde qualquer sistema cuja
pasta esteja vazia — é preciso pelo menos uma ROM. A lista de 106 pastas
esperadas está em `/storage/.config/emulationstation/es_systems.cfg`, que
pode ser lido sem montar nada:

```bash
python tools/ext4_reader.py IMAGEM 0x37400000 \
  cat:/.config/emulationstation/es_systems.cfg
```

---

## Como documentar a sua mídia

Offline, a partir de uma imagem ou do próprio cartão:

```bash
python tools/partition_map.py backup-sd-original.img
python tools/boot_header.py  backup-sd-original.img
python tools/uboot_env.py    backup-sd-original.img
```

No console:

```bash
mkdir -p dumps/bootlogs
cat /proc/cpuinfo   > dumps/bootlogs/cpuinfo.txt
uname -a            > dumps/bootlogs/uname.txt
dmesg               > dumps/bootlogs/dmesg.txt
free -h             > dumps/bootlogs/meminfo.txt
ls -la /lib/modules > dumps/bootlogs/modules.txt
```

> A pasta `dumps/` ainda **não existe** neste repositório — os comandos
> acima a criam. As saídas de texto podem ser versionadas; imagens binárias
> completas do SD, não.

## O que nunca fazer

- Formatar o SD original, mesmo "só uma partição"
- Copiar arquivos para a partição `Volumn`
- Deixar o Windows "reparar" qualquer volume do cartão
- Reparticionar com layout novo
- Gravar imagem genérica de EmuELEC por cima
- Expandir/mover partições com ferramenta gráfica

Qualquer uma dessas ações quase sempre resulta em brick permanente.
