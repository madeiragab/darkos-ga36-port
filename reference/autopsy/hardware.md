# Hardware — GA36-MB (R36S clone com Allwinner A33)

Este documento descreve o hardware físico do console portátil clone do R36S
baseado na placa **GA36-MB**, conforme inspeção visual direta e comparação com
autópsia técnica de referência.

O foco é **documentar o que existe de fato**, não o que o fabricante afirma.

---

## Visão geral

- **Produto:** Console portátil estilo R36S (clone)
- **Placa:** GA36-MB
- **Revisões conhecidas:**  
  - V1.0 (`GA36-MB V1.0-20250730`)  
  - V1.1 (`GA36-MB V1.1-20251025`)
- **Estado atual:** funcional com sistema original
- **Boot:** via cartão microSD

---

## SoC (System on Chip)

- **SoC real:** Allwinner A33
- **Arquitetura:** ARMv7 (Cortex-A7 quad-core)
- **Frequência típica:** ~1.0–1.2 GHz (não confirmada via clock real)
- **GPU:** ARM Mali-400 MP2
- **Processo:** legacy (sunxi)

⚠️ **Observação crítica**  
O encapsulamento do chip apresenta marcações falsas indicando **RK3326**.
Logs de boot e identificação de GPU confirmam, sem ambiguidade, Allwinner A33.

---

## Memória RAM

- **Tipo:** DDR3 (provável)
- **Capacidade estimada:** 512 MB (não confirmada via dump)
- **Configuração:** definida via `script.bin / magic.bin`

⚠️ A inicialização de DRAM depende fortemente da configuração legada Allwinner.
Sem esse arquivo, o sistema não inicializa.

---

## Armazenamento

### Cartão microSD

- **Função:** boot + sistema + ROMs
- **Layout:** não padrão (legacy Allwinner)
- **Dependência:** alta — SD original é crítico para recuperação

### Partições (resumo)

- FAT16: boot/configuração (`script.bin`, recursos)
- bootimg: kernel + ramdisk (Android-style)
- squashfs: sistema (EmuELEC custom)
- overlay RW: dados do usuário
- partições raw: U-Boot / environment

---

## Display

- **Tipo:** LCD (resolução exata não confirmada)
- **Interface:** RGB / paralelo (provável)
- **Inicialização:** via `script.bin`
- **Estado:** funcional com sistema original

⚠️ Display não inicializa sem configuração correta no boot.

---

## Controles e input

- **D-Pad:** físico
- **Botões de ação:** físicos
- **Triggers:** físicos
- **Start / Select:** físicos
- **Interface:** GPIO (sunxi)

Mapeamento tratado via sistema e overlays.

---

## Áudio

- **Saída:** alto-falante interno + fone (provável)
- **Codec:** integrado ou externo simples (não identificado)
- **Estado:** funcional

---

## Conectividade

- **USB:** presente (provavelmente USB OTG do A33)
- **Wi-Fi:** não identificado / não presente
- **Bluetooth:** não identificado / não presente

---

## Energia

- **Bateria:** Li-ion / Li-Po (interna)
- **Gerenciamento:** circuito dedicado (não identificado)
- **Carga:** via USB

---

## Bootloader

- **Tipo:** U-Boot legacy (sunxi)
- **Local:** partição raw no SD
- **Compatibilidade:** específica para GA36 / A33
- **Substituição:** alto risco sem dump funcional

---

## Interface serial (UART)

- **Pads identificados na placa:**
  - GND
  - TX
  - RX
- **Nível lógico:** 3.3V (assumido)
- **Uso:** não explorado neste projeto

⚠️ Console serial permitiria logs detalhados de boot, mas não é requisito imediato.

---

## Diferenças entre revisões conhecidas

- **V1.0 vs V1.1:**
  - Mudanças visuais no layout
  - Nenhuma evidência de mudança de SoC
  - Kernel e sistema permanecem compatíveis

---

## Limitações conhecidas do hardware

- Kernel extremamente antigo (Linux 3.4.x)
- Dependência de configuração legada (script.bin)
- GPU limitada (OpenGL ES 2.0)
- Port para sistemas modernos exige trabalho significativo

---

## Conclusão técnica

Este hardware é um **Allwinner A33 clássico**, reutilizado em um produto moderno
com rotulagem enganosa.

Não se trata de hardware “misterioso”, mas sim:
- mal documentado
- deliberadamente ofuscado
- tecnicamente limitado

Qualquer tentativa de port ou modificação deve respeitar:
- o kernel funcional existente
- o bootloader legacy
- a configuração original de hardware

Ignorar esses pontos resulta, quase certamente, em brick.
