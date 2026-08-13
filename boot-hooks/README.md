# Hooks de boot

O `init` do initramfs faz `source` de três arquivos, se existirem, na
partição `/flash` (`mmcblk0p7`, FAT16 rotulada `EMUELEC`, offset `0x7400000`):

| Hook | Linha do `init` | Quando roda | Observação |
|---|---|---|---|
| `post-flash.sh` | 666 | logo após montar `/flash` | incondicional, não substitui nada — **o mais seguro** |
| `post-sysroot.sh` | 296 | após montar `/sysroot` | |
| `mount-storage.sh` | 723 | **no lugar** da montagem do `/storage` | substitui lógica; errar aqui deixa o sistema sem `/storage` |

> O hook documentado pelo EmuELEC upstream, `/storage/.config/custom_start.sh`,
> **não é executado por este fork**. Ver [../failures.md](../failures.md).

## `post-flash.sh`

Ajusta o writeback do kernel para que o dado chegue ao cartão em ~2 s em vez
de até 30 s. Valores em `/proc/sys` sobrevivem ao `switch_root` e valem para
o boot inteiro — é por isso que este hook, apesar de rodar no initramfs,
resolve um problema do sistema em execução.

Sem ele, mesmo com `autosave_interval = "10"` o save fica na page cache e um
corte de energia pelo botão leva tudo junto.

## Instalar

`/flash` não é montável pelo Windows. Use
[`../tools/fat16_write.py`](../tools/fat16_write.py):

```bash
python tools/fat16_write.py \\.\PhysicalDrive1 0x7400000 --put boot-hooks/post-flash.sh post-flash.sh --apply
```

Em Linux, `/dev/sdX` no lugar do `\\.\PhysicalDriveN`. Ou simplesmente monte
a partição e copie o arquivo.

## Remover (recuperação)

**Se o console parar de bootar depois de instalar um hook, é isto que
desfaz:**

```bash
python tools/fat16_write.py \\.\PhysicalDrive1 0x7400000 --delete post-flash.sh --apply
```

## Regra ao editar

Estes arquivos são **sourced** pelo shell do initramfs. Um erro de
**sintaxe** aborta o boot — e com `loglevel=0` o sintoma é tela preta muda.

Por isso `post-flash.sh` contém apenas redirecionamentos de `echo`: sem
condicional, sem substituição de comando, sem loop. Erro de *execução* (um
caminho que não existe) é inofensivo, só imprime mensagem. Erro de
*sintaxe* não é.

Antes de instalar qualquer alteração:

```bash
sh -n boot-hooks/post-flash.sh
```

E garanta terminadores **LF**. Um `\r` no fim da linha torna o caminho
inválido e, pior, pode quebrar a sintaxe. O `fat16_write.py` se recusa a
gravar arquivos com CRLF.
