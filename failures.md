> 🇧🇷 **Português** · 🇬🇧 [English](failures.en.md)

# Registro de falhas e becos sem saída

Este arquivo existe para que **ninguém repita o mesmo erro duas vezes** —
nem eu, nem quem encontrar este repositório com o mesmo console na mão.

Falha documentada é conhecimento. Falha esquecida é console brickado.

## Como registrar

Uma entrada por tentativa, no formato:

```markdown
### AAAA-MM-DD — Título curto do que foi tentado

**Hipótese:** o que se esperava que acontecesse
**Ação:** o que foi feito exatamente (comandos, arquivos, versões)
**Resultado:** o que aconteceu de fato
**Diagnóstico:** por que falhou (ou "desconhecido")
**Recuperação:** como o console voltou ao estado funcional
**Lição:** o que muda na próxima tentativa
```

Registrar **antes** de tentar de novo. Se o resultado for "desconhecido",
registre assim mesmo — meia informação vale mais que nenhuma.

---

## Falhas conhecidas (herdadas da comunidade e da autópsia)

Estas não foram testadas nesta unidade — estão aqui porque o resultado é
previsível e destrutivo. **Não sirva de cobaia para confirmá-las.**

### Gravar imagem pública de R36S / RK3326

**Resultado:** não boota. O SoC real é Allwinner A33, não RK3326.
**Agravante:** o processo sobrescreve o SD original. Sem backup, o console
fica inutilizável.
**Lição:** o silk do chip não é fonte de verdade — ver
[docs/kernel.md](docs/kernel.md) para confirmar o SoC real.

### Gravar EmuELEC oficial (build pública)

**Resultado:** não boota. O sistema de fábrica é uma build custom
(`GA36-UDT-EE-TF-R-20250818`) compilada para A33.
**Lição:** a build custom é o único baseline funcional comprovado.

### Reparticionar o SD com ferramenta gráfica

**Resultado:** brick. O boot depende do layout físico e de uma partição raw
(~16 MB, U-Boot) que ferramentas gráficas tratam como espaço não alocado.
**Lição:** backup bit-a-bit com `dd`, nunca cópia de arquivos — ver
[docs/storage.md](docs/storage.md).

### Trocar o kernel mantendo o resto

**Resultado:** falha silenciosa — tela preta, sem log, sem indicação do
estágio que quebrou.
**Diagnóstico:** o kernel novo não interpreta o `script.bin` legado, e o
U-Boot espera `boot.img` no formato Android.
**Lição:** sem acesso serial, esse tipo de falha é indepurável — ver
[docs/device-tree.md](docs/device-tree.md).

---

## Falhas registradas nesta unidade

### 2026-08-12 — Windows esvaziou as partições do cartão

**Hipótese:** plugar o cartão no PC para inspecionar seria inofensivo.
**Ação:** cartão inserido no Windows 11, volumes montados automaticamente.
**Resultado:** as partições `Volumn` e de ROMs apareceram vazias; o conteúdo
de fábrica (fontes, `bootlogo.bmp`, `magic.bin`) sumiu. A partição de ROMs
apareceu reformatada como exFAT.
**Diagnóstico:** o Windows monta a `Volumn` usando o **BPB**, que declara
128 MB, enquanto a entrada da MBR declara 32 MB. Ele considera gravável a
faixa de 36 MB a 164 MB do cartão, onde estão o `boot.img` (84 MB) e o
`SYSTEM` (116 MB). Além disso cria `System Volume Information` sozinho ao
montar. Ver [docs/image-autopsy.md](docs/image-autopsy.md) §6.3.
**Recuperação:** regravação da imagem de recovery.
**Lição:** **nunca deixe o Windows montar esse cartão sem necessidade.** Se
precisar, desligue o automount antes (`diskpart` → `automount disable`) e
nunca clique em "Formatar" quando ele oferecer.

### 2026-08-12 — Imagem de recovery gera partição de ROMs de 5,42 MB

**Hipótese:** gravar a imagem de recovery restauraria o console ao estado
de fábrica.
**Ação:** gravação byte a byte da `r36s-a33-recovery.img` (2425 MB).
**Resultado:** o console bootou, mas o EmulationStation exibiu
`we can't find any systems`. A partição 1 ficou com 11 099 setores
(5,42 MB).
**Diagnóstico:** a imagem distribuída está truncada — a entrada da MBR
declara 5,42 MB enquanto o BPB FAT32 interno declara 48 779 MB. A MBR também
aponta LBA 4956161 quando o boot sector real está em 4956160.
**Recuperação:** reescrita da entrada da MBR (início 4956160, tamanho até o
fim do cartão) e geração de um FAT32 novo com label `EEROMS`.
**Lição:** a imagem de recovery **não** é utilizável como está. Ver
[docs/storage.md](docs/storage.md).

### 2026-08-12 — Console não ligava; parecia brick, era bateria

**Hipótese:** depois de um boot bem-sucedido, o console parou de ligar —
suspeita imediata de corrupção do boot.
**Ação:** comparação byte a byte entre cartão e imagem
([`tools/verify_card.py`](tools/verify_card.py)).
**Resultado:** apenas 32,6 KB de diferença, todos em áreas inofensivas
(tabela FAT da `Volumn` e partição de ROMs). `boot0`, `boot.img`, `SYSTEM` e
o ext4 estavam íntegros.
**Diagnóstico:** bateria muito descarregada. O LED de carga acende bem antes
de haver carga suficiente para dar boot.
**Recuperação:** 2 horas no carregador sem tentar ligar.
**Lição:** com `loglevel=0` e `bootdelay=0`, falha de boot e falta de energia
produzem exatamente a mesma tela preta. Verifique o cartão por leitura antes
de assumir corrupção, e carregue de verdade antes de assumir brick.

### 2026-08-13 — `custom_start.sh` não é executado por este fork

**Hipótese:** o hook `/storage/.config/custom_start.sh`, documentado pelo
próprio EmuELEC como o lugar para scripts de boot, seria executado antes do
frontend.
**Ação:** patch do `custom_start.sh` com `sed` para ajustar
`autosave_interval`, `menu_driver` e mais 7 chaves do `retroarch.cfg`.
**Resultado:** nenhuma das chaves mudou. Confirmado lendo o
`retroarch.cfg` vivo do cartão.
**Diagnóstico:** **confirmado lendo o `SYSTEM`.** Em
`/usr/bin/emuelec_autostart.sh` a chamada está comentada:

```sh
# run custom_start before FE scripts
#/storage/.config/custom_start.sh before &
```

O arquivo ainda traz, logo acima, o comentário do upstream mandando usar o
`custom_start.sh` — que ficou órfão. Corrigir na origem exigiria repack do
squashfs; por isso a solução usa `/flash/post-flash.sh` e escrita direta.
**Recuperação:** não foi necessária — o hook simplesmente não roda, nada
quebrou.
**Lição:** neste sistema, alterar configuração exige escrever direto no
arquivo, não depender de hooks. Ver
[`tools/patch_retroarch.py`](tools/patch_retroarch.py).

### 2026-08-13 — `Set-Disk -IsOffline` falha em mídia removível

**Hipótese:** colocar o disco offline liberaria escrita crua no Windows.
**Ação:** `Set-Disk -Number N -IsOffline $true` antes de reescrever a MBR.
**Resultado:** `Set-Disk : Not Supported — Removable media cannot be set to
offline.`
**Diagnóstico:** o Windows recusa por design em mídia removível.
**Recuperação:** abrir cada volume com `CreateFileW`, aplicar
`FSCTL_LOCK_VOLUME` e `FSCTL_DISMOUNT_VOLUME`, e **manter os handles
abertos** durante a escrita — é o que as ferramentas de imagem fazem.
**Lição:** para escrita crua em cartão no Windows, lock + dismount por
volume, não offline por disco.

---

O estado atual é: boot funcional, backup do SD verificado, hardware
identificado, partição de ROMs corrigida. Toda tentativa futura deve ser
registrada acima **antes** de ser repetida.
