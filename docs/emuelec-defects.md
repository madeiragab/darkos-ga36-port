> 🇧🇷 **Português** · 🇬🇧 [English](emuelec-defects.en.md)

# Defeitos do EmuELEC 4.7 desta placa

O sistema de fábrica é um fork não oficial do EmuELEC 4.7 (`EE_VERSION` =
`4.7`, upstream de Shanti Gilbert). O EmuELEC 4.7 oficial **nunca teve
target sun8i/A33** — o vendor adaptou por conta própria, e várias coisas
ficaram pelo caminho.

Este documento lista defeitos **verificados no conteúdo da imagem**, não
impressões de uso. Cada um traz a evidência e a correção.

---

## 1. Perda de save ao desligar pelo botão

O sintoma mais reclamado. Não é um bug — são **quatro falhas empilhadas**,
e cada uma sozinha já bastaria para perder o save.

### 1.1 O RetroArch nunca grava durante o jogo

`/storage/.config/retroarch/retroarch.cfg`:

```
autosave_interval = "0"
```

Com zero, a SRAM só vai para o disco quando o core é descarregado (ao sair
do jogo). Cortar a energia jogando significa que a sessão inteira nunca
existiu em disco. **Esta é a causa principal.**

### 1.2 O save cai em FAT32 sem journal

```
savefiles_in_content_dir = "true"
savefile_directory = "/saves"
```

Com `savefiles_in_content_dir` ligado, o save é gravado ao lado da ROM — ou
seja, na partição FAT32. E o `init` monta essa partição assim:

```sh
mount -t "${ROM_FS_TYPE}" -o utf8 "${ROMS_PART_PATH}" /storage/roms
```

Só `utf8`. Sem `flush`, sem `sync`. O vfat segura escrita em cache, e o
FAT32 não tem journal: escrita interrompida corrompe a entrada de diretório,
não apenas o arquivo.

(`savefile_directory = "/saves"` aponta para a raiz do sistema, que é
squashfs somente leitura — configuração incoerente que só não quebra porque
`savefiles_in_content_dir` tem precedência.)

### 1.3 Nada repara no boot seguinte

Ver seção 2.

### 1.4 O botão de power corta a energia sem avisar o sistema

Comportamento observado na unidade: segurar o botão de desligar **perde** o
save. Sair do emulador com `Start` + `Select` (volta ao EmulationStation)
**grava**.

Isso é a assinatura exata do problema 1.1: a SRAM só é escrita quando o core
é descarregado. `Start`+`Select` descarrega o core; o botão de power não —
ele corta na PMIC (AXP22x) antes de qualquer flush.

Enquanto o handler do botão não for corrigido, **o desligamento seguro é
`Start`+`Select` primeiro, botão depois**.

O handler vive no `SYSTEM` (squashfs lzo) e ainda não foi inspecionado.

### 1.5 Sem tuning de writeback

`/storage/.config/sysctl.d/` contém apenas um `README`. Vale o padrão do
kernel, `vm.dirty_expire_centisecs = 3000` — dado pode ficar até 30 s em RAM
antes de tocar o cartão.

### Correção

> **Primeira tentativa falhou.** O hook `/storage/.config/custom_start.sh`,
> documentado pelo próprio EmuELEC, **não é executado por este fork** —
> registrado em [../failures.md](../failures.md). A correção real usa dois
> pontos que comprovadamente rodam:
>
> 1. **`/flash/post-flash.sh`** — o `init` faz `source` dele na linha 666,
>    logo após montar `/flash`. Ajusta o writeback do kernel; valores em
>    `/proc/sys` sobrevivem ao `switch_root`. Ver
>    [../boot-hooks/](../boot-hooks/).
> 2. **Escrita direta no `retroarch.cfg`**, sem depender de hook nenhum. Ver
>    [`../tools/patch_retroarch.py`](../tools/patch_retroarch.py).

Valores aplicados:

| Ajuste | De | Para |
|---|---|---|
| `autosave_interval` | `0` | `10` |
| `savefiles_in_content_dir` | `true` | `false` |
| `savefile_directory` | `/saves` | `/storage/savefiles` (ext4, com journal) |
| `savestate_directory` | `~/roms/savestates/gb` | `/storage/savestates` |
| montagem das ROMs | `utf8` | `remount,flush` |
| `vm.dirty_expire_centisecs` | 3000 | 200 |

O `savestate_directory` apontava para uma pasta `gb` fixa — resquício de
alguém testando um jogo de Game Boy; todos os savestates de todos os
sistemas caíam ali.

---

## 2. `fsck.auto` não existe no initramfs

O `init` chama sem especificar tipo:

```sh
fsck -T -M -p -a $RUN_FSCK_DISKS
```

A detecção falha e ele procura `/sbin/fsck.auto`. O initramfs traz
`e2fsck`, `fsck.ext2`, `fsck.fat` e `fsck.exfat` — **não traz `fsck.ext4`
nem `fsck.auto`**. O próprio `init.log` da imagem registra:

```
fsck: fsck.auto: No such file or directory
fsck: fsck.auto: No such file or directory
mount: mounting /run on /sysroot/run failed: Invalid argument
```

Resultado: o `/storage` nunca é verificado após desligamento sujo.

**Correção:** exige repack do `boot.img` (criar `fsck.ext4` como link para
`e2fsck`, ou passar `-t ext4`). Ainda não feito.

---

## 3. Fallback silencioso do `/storage` para tmpfs

O `init` tem este caminho:

```sh
if [ -n "$disk" ]; then
    ...
    mount_part "$disk" "/storage" "rw,noatime"
else
    # /storage should always be writable
    mount -t tmpfs none /storage
fi
```

Quando o `/storage` não monta, o sistema **sobe assim mesmo**, com `/storage`
em RAM. O efeito é sutil e confunde muito:

- não existe `.config`, então o EmuELEC copia padrões do `SYSTEM`;
- nenhuma personalização sobrevive ao reboot;
- não há ROMs, e o EmulationStation mostra `we can't find any systems`;
- **nada é escrito no ext4** — o que dá para confirmar de fora com
  [`tools/verify_card.py`](../tools/verify_card.py).

Diagnóstico prático: se a região `ext4 /storage` aparecer **idêntica** à
imagem depois de um boot, o `/storage` não montou. Se aparecerem
diferenças, montou.

> Este fallback também torna qualquer alteração em `/storage/.config`
> inútil quando o problema está presente — a correção da seção 1 não roda.

---

## 4. Desempenho do frontend

> **Correção.** Uma versão anterior deste documento afirmava que o sistema
> renderizava a 1920×1080 e reduzia para 640×480, por causa de
> `ee_videomode=1080p60hz` no `emuelec.conf`. **Isso está errado.**
>
> O `disp_init` do `script.bin` traz `fb0_width = 0`, `fb0_height = 0` e
> `fb0_scaler_mode_enable = 0`. Zero significa "usar o tamanho do painel",
> então o framebuffer **já é 640×480** e não há scaler no caminho.
> `ee_videomode` é um conceito Amlogic (escreve em `/sys/class/display/mode`),
> caminho que não existe nesta plataforma Allwinner — a chave é **inerte**.
>
> Não altere `ee_videomode` esperando ganho: não há nenhum.

O custo real do frontend está em outro lugar.

### `retroarch.cfg`

| Chave | Valor de fábrica | Problema |
|---|---|---|
| `menu_driver` | `xmb` | menu 3D animado, caro em Mali-400 |
| `menu_shader_pipeline` | `1` | fundo animado por shader |
| `auto_shaders_enable` | `true` | carrega shader automático — pior caso nessa GPU |
| `menu_dynamic_wallpaper_enable` | `true` | decodificação de wallpaper |
| `menu_show_sublabels` | `true` | segunda linha de texto por item |
| `menu_ticker_smooth` | `true` | rolagem suave de títulos = redraw contínuo |
| `log_verbosity` | `true` | log verboso, gravando no cartão sem utilidade |
| `menu_widget_scale_factor` | `2.0` | widgets em escala 2× num painel de 640×480 |

### Erro de proporção no RGUI

```
rgui_aspect_ratio = "6"
```

O valor 6 é **3:2 centralizado**. O painel é **4:3** (640×480), que é o
valor `0`. Com 6, o RGUI desenha em letterbox e desperdiça área de tela.

### `es_settings.cfg`

| Chave | Valor de fábrica | Problema |
|---|---|---|
| `GamelistViewStyle` | `detailed` | renderiza imagem e metadados por item |
| `ScreenSaverBehavior` | `slideshow` | decodifica imagens em loop |
| `ScrapeVideos` | `true` | preview em vídeo dentro do gamelist |

`TransitionStyle` e `GameTransitionStyle` já vêm como `instant` — esses
estavam certos de fábrica.

### `emuelec.conf`

| Chave | Valor de fábrica | Problema |
|---|---|---|
| `audio.bgmusic` | `1` | decodificação contínua de música no frontend |
| `updates.enabled` | `1` | sem wifi e sem upstream real para este fork |
| `system.timezone` | `America/Mexico_City` | padrão do vendor |

**Verificação rápida no aparelho:** se o menu do RetroArch abrir em RGUI
(texto simples) em vez de XMB (ondas 3D), as correções estão ativas.

---

## 5. Outras observações

- `system.timezone=America/Mexico_City` — padrão do vendor, não do Brasil.
- `system.hostname=UDT` — marca do vendor no build
  (`GA36-UDT-EE-TF-R-20250818`).
- `ee_ssh.enabled=1` com `wifi.enabled=0`: SSH está ligado, mas sem rede
  não há como alcançá-lo.
- `global.maxperf=1` já vem no máximo.
- `es_systems.cfg` define **106 sistemas**. O EmulationStation esconde
  qualquer um cuja pasta esteja vazia — pasta criada sem ROM não aparece.

---

## Como inspecionar sem montar nada

```bash
python tools/ext4_reader.py IMAGEM 0x37400000 ls:/.config
python tools/ext4_reader.py IMAGEM 0x37400000 cat:/.config/emuelec/configs/emuelec.conf
python tools/ext4_reader.py IMAGEM 0x37400000 cat:/.config/retroarch/retroarch.cfg
python tools/ext4_reader.py IMAGEM 0x37400000 cat:/init.log
```

O `init` do initramfs fica dentro do `boot.img`; para extraí-lo use o
comando `dd` que [`tools/boot_header.py`](../tools/boot_header.py) imprime.
