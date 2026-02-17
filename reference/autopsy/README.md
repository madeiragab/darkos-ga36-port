# Autópsia técnica de referência — GA36 / R36S clone

Este diretório contém a **autópsia técnica de referência** utilizada como baseline
para o estudo, documentação e possível port de sistema no console portátil
clone do R36S baseado na placa **GA36-MB**.

⚠️ Este NÃO é um trabalho original deste projeto.  
Toda a análise técnica detalhada, dumps e imagens foram produzidos pelo autor da
autópsia original, devidamente creditado em `sources.md`.

Este projeto utiliza essa autópsia **exclusivamente como referência técnica**.

---

## Objetivo deste diretório

O objetivo deste material é:

- Consolidar informações confiáveis sobre o hardware real do GA36
- Evitar engenharia reversa redundante
- Estabelecer um **baseline funcional comprovado**
- Reduzir risco de brick durante testes futuros

Este diretório **não contém binários**, apenas documentação e referências.

---

## Hardware documentado pela autópsia

- **Placa:** GA36-MB (V1.0 / V1.1)
- **SoC real:** Allwinner A33
- **Arquitetura:** ARMv7 (sunxi)
- **GPU:** Mali-400
- **Bootloader:** U-Boot (sunxi legacy)
- **Kernel:** Linux 3.4.39 (sunxi)
- **Formato de boot:** Android-style `boot.img`
- **Configuração de hardware:** `script.bin` / `magic.bin` (formato legado Allwinner)

A autópsia confirma que o dispositivo **não utiliza RK3326**, apesar das marcações
presentes no encapsulamento do chip.

---

## Por que essa autópsia é crítica

- Builds públicas modernas do EmuELEC **não bootam** neste hardware
- O layout de partições é não padrão e dependente de U-Boot antigo
- O kernel e a configuração de hardware são altamente específicos
- Sem o SD original ou dumps equivalentes, o dispositivo é difícil de recuperar

Portanto, qualquer tentativa de modificação **deve partir exatamente deste estado funcional conhecido**.

---

## Estrutura deste diretório

- `README.md`  
  Contexto e escopo da autópsia de referência

- `files.md`  
  Catálogo técnico dos arquivos disponibilizados na autópsia original

- `notes.md`  
  Observações e comparações com o hardware real deste projeto

- `sources.md`  
  Links, créditos e fontes externas

---

## Diretriz do projeto

> Nenhum componente do sistema será substituído antes de ser compreendido.

Essa regra vale para:
- kernel
- bootloader
- layout de partições
- configuração de hardware

Qualquer violação dessa diretriz aumenta drasticamente o risco de brick.

---

## Estado atual

- Autópsia validada como compatível com o hardware deste projeto
- Sistema funcional confirmado via EmuELEC 4.7 customizado
- Próximo passo: documentação detalhada do hardware físico (`hardware.md`)
