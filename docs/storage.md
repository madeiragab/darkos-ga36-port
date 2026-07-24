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

## Layout de partições

Referência da autópsia (revisão V1.0) — comparar com a sua mídia antes de
assumir que é idêntico:

| Partição | Tipo | Tamanho aprox. | Conteúdo |
|---|---|---|---|
| `img1` | FAT32 | grande | ROMs, saves |
| `img2` | FAT16 | ~32 MB | `magic.bin`, recursos de boot |
| `img5` | raw | ~16 MB | configuração do U-Boot |
| `img6` | bootimg | ~32 MB | Android bootimg (kernel + ramdisk) |
| `img7` | squashfs | ~768 MB | SYSTEM do EmuELEC (somente leitura) |
| `img8` | overlay rw | ~1,5 GB | userdata, configs, cores |

Pontos que costumam pegar quem mexe pela primeira vez:

- **`img5` é raw**: não tem sistema de arquivos. Ferramentas gráficas de
  particionamento a tratam como "espaço não alocado" e a destroem sem aviso.
- **`img7` é squashfs**: somente leitura por design. Alterações de sistema
  vivem no overlay `img8`.
- **A ordem e os offsets importam** — ver [boot-chain.md](boot-chain.md).

## Como documentar a sua mídia

No console:

```bash
mkdir -p dumps/bootlogs
cat /proc/cpuinfo   > dumps/bootlogs/cpuinfo.txt
uname -a            > dumps/bootlogs/uname.txt
dmesg               > dumps/bootlogs/dmesg.txt
ls -la /lib/modules > dumps/bootlogs/modules.txt
```

No PC, com o SD inserido:

```bash
mkdir -p dumps/partitions
lsblk -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINT > dumps/partitions/lsblk.txt
blkid                                               > dumps/partitions/blkid.txt
sudo fdisk -l /dev/sdX                              > dumps/partitions/fdisk.txt
```

> A pasta `dumps/` ainda **não existe** neste repositório — os comandos
> acima a criam. As saídas de texto podem ser versionadas; imagens binárias
> completas do SD, não.

## O que nunca fazer

- Formatar o SD original, mesmo "só uma partição"
- Reparticionar com layout novo
- Gravar imagem genérica de EmuELEC por cima
- Expandir/mover partições com ferramenta gráfica

Qualquer uma dessas ações quase sempre resulta em brick permanente.
