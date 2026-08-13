> 🇧🇷 **Português** · 🇬🇧 [English](build-recipe.en.md)

# Receita: da imagem de recovery a uma build funcional

Procedimento completo e reproduzível para transformar a imagem de recovery
distribuída — que **não é utilizável como está** — numa build com saves
íntegros e frontend leve.

Estado congelado na tag **`v1.0-working`**.

## O que esta receita corrige

| Problema | Origem |
|---|---|
| Partição de ROMs de 5,42 MB, EmulationStation sem sistemas | imagem truncada |
| Save perdido ao desligar pelo botão | 4 falhas empilhadas |
| RGUI em letterbox | `rgui_aspect_ratio = 6` num painel 4:3 |
| Menu pesado, log gravando no cartão à toa | configuração de fábrica |

Diagnóstico de cada um em [emuelec-defects.md](emuelec-defects.md) e
[image-autopsy.md](image-autopsy.md).

---

## Pré-requisitos

- Python 3 (sem dependências externas)
- Windows: PowerShell **como Administrador** para os passos que tocam o
  cartão. Linux: `sudo`, trocando `\\.\PhysicalDrive1` por `/dev/sdX`.
- A imagem de recovery da sua unidade

> **Antes de tudo:** faça o backup bit-a-bit do SD original e guarde o hash.
> Ver [storage.md](storage.md). Se ainda não fez, pare aqui.

---

## Passo 1 — Gravar a imagem

Qualquer ferramenta de escrita crua (Rufus, balenaEtcher em modo DD, `dd`).

**Ao terminar, não deixe o Windows montar o cartão.** Se aparecer
"É preciso formatar o disco", clique **Cancelar**. O motivo está em
[storage.md](storage.md) — a partição `Volumn` mente o próprio tamanho e o
Windows pode gravar por cima do `boot.img`.

Conferir integridade a qualquer momento, **somente leitura**:

```bash
python tools/verify_card.py recovery.img \\.\PhysicalDrive1
```

## Passo 2 — Corrigir a partição de ROMs

```bash
python tools/fix_rom_partition.py --apply
```

Reescreve a entrada da MBR (início LBA 4956160, alinhado, até o fim do
cartão) e gera um FAT32 novo com label `EEROMS`.

## Passo 3 — Criar as pastas de ROMs

O EmulationStation esconde qualquer sistema cuja pasta esteja vazia. Os 106
nomes esperados saem do próprio `es_systems.cfg`:

```bash
python tools/ext4_reader.py \\.\PhysicalDrive1 0x37400000 cat:/.config/emulationstation/es_systems.cfg
```

Crie as pastas na raiz da partição de ROMs e **ponha pelo menos uma ROM** —
pasta vazia não aparece.

> **A pasta de NES chama-se `nes-user`, não `nes`.** O `mount_romfs.sh`
> despeja 205 ROMs do fabricante em `nes/` a cada boot, e por isso o
> EmulationStation foi repontado. Ver
> [emuelec-defects.md](emuelec-defects.md) §5.

## Passo 4 — Configuração

```bash
python tools/patch_config.py \\.\PhysicalDrive1 0x37400000 --apply
```

Cobre `retroarch.cfg`, `emuelec.conf` e `es_settings.cfg` num passo. É
idempotente: pula o que já está no valor desejado.

## Passo 5 — Hook de writeback

```bash
python tools/fat16_write.py \\.\PhysicalDrive1 0x7400000 --put boot-hooks/post-flash.sh post-flash.sh --apply
```

Sem este passo os passos 4 não bastam: a SRAM é gravada a cada 10 s, mas
fica na page cache até 30 s. O hook derruba isso para ~2 s. Detalhes e
**caminho de recuperação** em [../boot-hooks/README.md](../boot-hooks/README.md).

## Passo 6 — Verificar no aparelho

| Sinal | Significado |
|---|---|
| Menu do RetroArch em **RGUI** (texto), não XMB | passo 4 aplicado |
| `dmesg \| grep post-flash` mostra `writeback ajustado` | passo 5 aplicado |
| Sistemas aparecem no EmulationStation | passos 2 e 3 ok |
| Salvar, jogar 30 s, segurar o botão, religar: save intacto | correção completa |

---

## Congelar a sua build

Depois de validar, tire uma imagem do cartão **funcionando**. É o único
artefato que devolve este estado sem repetir a receita:

```bash
sudo dd if=/dev/sdX of=ga36-working-v1.0.img bs=4M status=progress
sha256sum ga36-working-v1.0.img > ga36-working-v1.0.img.sha256
```

No Windows, qualquer ferramenta de leitura crua serve; guarde o hash junto.

> Imagens completas do SD **não** são versionadas neste repositório. A
> receita é reproduzível justamente para que não precisem ser.

---

## O que esta receita não resolve

- **Botão de power: não mexa.** O toque suspende, e o serviço do vendor
  (`udt_pwr.service`) já executa `sync` antes — o save está protegido. Duas
  tentativas de converter para `poweroff` quebraram o boot; ambas estão
  documentadas em [../failures.md](../failures.md). O script mexe em
  backlight e áudio **antes** de chamar o `systemctl`, então interceptar só
  o final deixa o aparelho num estado que nenhum ramo do script desfaz.
  Segurar o botão continua cortando na PMIC — isso é hardware.
- **`fsck.auto` ausente** no initramfs — exige repack do `boot.img`.
- **PSP, Stardew Valley e qualquer coisa que exija ARM64 ou GLES 3.**
  Parede de hardware. Ver [kernel.md](kernel.md), "Limites que kernel nenhum
  resolve".
