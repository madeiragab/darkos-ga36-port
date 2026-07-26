> 🇧🇷 **Português** · 🇬🇧 [English](kernel.en.md)

# Kernel

## Baseline funcional

| Item | Valor | Estado |
|---|---|---|
| Família | Linux-sunxi (legado) | Confirmado |
| Versão | 3.4.x (`3.4.39` observado no dump) | Confirmado |
| Arquitetura | ARM Cortex-A7 quad-core (Allwinner A33 / `sun8i`) | Confirmado |
| GPU | Mali-400, detectada corretamente pelo kernel | Confirmado |
| Empacotamento | Android `boot.img` (kernel + ramdisk) | Confirmado |
| Configuração de hardware | `script.bin` (não DTB) | Confirmado |

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

## Por que kernels modernos não bootam

| Barreira | Detalhe |
|---|---|
| Formato de configuração | Kernels modernos esperam DTB; esta placa usa `script.bin` legado |
| Suporte a A33 no mainline | Existe, mas com bindings e device tree completamente diferentes |
| Driver da Mali-400 | Blob legado, amarrado à versão antiga do kernel |
| Empacotamento | O U-Boot desta placa espera `boot.img` Android, não `zImage`/`uImage` |

Trocar o kernel sem resolver **todas** essas barreiras resulta em falha
silenciosa: tela apagada, sem log, sem indicação do estágio que falhou.

## Pendências

- [ ] Dump do `boot.img` e extração separada de kernel e ramdisk
- [ ] Listagem completa de módulos carregados em runtime
- [ ] Captura de `dmesg` completo em arquivo versionado
- [ ] Log de boot via serial (requer identificar os pads TX/RX/GND)
