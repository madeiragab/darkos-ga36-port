> 🇧🇷 **Português** · 🇬🇧 [English](kernel.en.md)

# Kernel

## Baseline funcional

| Item | Valor | Estado |
|---|---|---|
| Família | Linux-sunxi (legado) | Confirmado |
| Versão | **3.4.39** | Confirmado |
| Toolchain do build | gcc 4.6.3 (crosstool-NG linaro-1.13.1-2012.02) | Confirmado |
| Assinatura do build | `lxl@lxl` — mesmo builder do U-Boot | Confirmado |
| Arquitetura | ARM Cortex-A7 quad-core, **ARMv7 32-bit** (`sun8iw5p1`) | Confirmado |
| GPU | Mali-400 | Confirmado |
| Empacotamento | Android `boot.img`, `name = sun8i` | Confirmado |
| Endereço de carga | kernel `0x40008000`, ramdisk `0x41000000` | Confirmado |
| Tamanho | kernel 12,60 MB, initramfs 2,90 MB (gzip) | Confirmado |
| Configuração de hardware | `script.bin` (não DTB) | Confirmado |
| `cmdline` no header | **vazia** — os bootargs vêm do U-Boot | Confirmado |

A toolchain de 2012 vale ser notada: este kernel foi compilado com um gcc
que já era antigo quando o hardware saiu de fábrica em 2025.

O initramfs é derivado do **LibreELEC** — usa `/flash`, `/storage`,
`/sysroot`, `SYSTEM`, e o mesmo script `init`. Ver
[emuelec-defects.md](emuelec-defects.md).

Este kernel é o **único baseline funcional comprovado** para esta placa.
Builds públicas modernas do EmuELEC não funcionam neste hardware.

## Como confirmar na sua unidade

Executar no console e commitar as saídas:

```bash
cat /proc/cpuinfo    # deve mostrar sun8i / identificador Allwinner
uname -a             # deve indicar kernel sunxi (ex.: 3.4.39)
dmesg                # deve reportar Mali-400 e strings sunxi
ls -la /lib/modules  # módulos disponíveis
```

Se as três primeiras saídas confirmarem sunxi/A33, o silk "RK3326" no chip
é **remarking** — o silk não é fonte definitiva.

## Por que não recompilar

O kernel 3.4.x é uma árvore legada, fora do mainline há mais de uma década.
Recompilar exigiria:

- a toolchain e a árvore de fontes exatas usadas no build original
  (**não disponíveis**);
- entendimento completo de como o `script.bin` desta placa mapeia GPIO,
  display, clocks e áudio;
- capacidade de recuperar o console via serial ou FEL quando o boot falhar
  — e ele vai falhar durante as tentativas.

Nenhum desses pré-requisitos está satisfeito hoje. Por isso recompilar está
explicitamente fora do escopo — ver [scope.md](scope.md).

## Por que kernels modernos não bootam *hoje*

A formulação importa. Não é que o A33 seja incompatível com Linux moderno —
**ele tem suporte mainline**. O que falta é o trabalho de integração desta
placa específica.

| Barreira | Detalhe | Superável? |
|---|---|---|
| Formato de configuração | Kernels modernos esperam DTB; esta placa usa `script.bin` | Sim — tradução, valores já extraídos em [device-tree.md](device-tree.md) |
| Driver da Mali-400 | Blob legado amarrado ao 3.4 | Sim — **Lima** (Mesa) cobre Mali-400 com GLES 2.0 no mainline |
| Empacotamento | O U-Boot espera `boot.img` Android, não `zImage` | Sim — ou empacota igual, ou troca o U-Boot (sunxi é bem mantido no mainline) |
| Driver do painel | `jd9366_8inch` não existe no mainline | **É o trabalho novo de verdade** |
| Diagnóstico de falha | `loglevel=0`: falha = tela preta muda | ✅ Resolvido — [serial-console.md](serial-console.md) |

O que existe pronto no mainline para este SoC:

| Componente | Situação |
|---|---|
| SoC | `sun8i-a33.dtsi` |
| GPU Mali-400 | Lima (Mesa), GLES 2.0 |
| Display Engine | `sun4i-drm` + `sun8i-mixer` |
| MIPI DSI | `sun6i-mipi-dsi` |
| PMIC AXP223 | `axp20x` |
| MMC / USB / I2C / UART | suportados |

**A ordem que faz sentido:** serial primeiro, device tree depois, kernel por
último. Trocar o kernel antes de ter serial é depuração às cegas — cada
tentativa falhada produz exatamente a mesma tela preta, sem informação.

## Limites que kernel nenhum resolve

Vale registrar para não gerar expectativa errada. Estes são limites de
hardware, não de software:

- **ARMv7 32-bit.** Nada que exija ARM64 roda aqui — inclusive `box64`.
- **Mali-400: GLES 2.0, sem S3TC.** Texturas DXT precisam de
  descompressão em software.
- **~850 MB de RAM utilizável.** De 1 GB físico, os bootargs reservam
  176 MB de CMA e 150 MB de carveout.

Atualizar o kernel melhora estabilidade, drivers e ferramentas modernas.
Não muda nenhuma linha acima.

## Pendências

- [x] Dump do `boot.img` e leitura do header
- [x] Log de boot via serial — pinos identificados (falta ligar)
- [ ] Extração do initramfs e versionamento do `init` do vendor
- [ ] Listagem completa de módulos carregados em runtime
- [ ] Captura de `dmesg` completo em arquivo versionado
- [ ] Extrair a sequência de init DSI do driver `jd9366_8inch` do `SYSTEM`
