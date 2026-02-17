# Notas de validação — Autópsia vs hardware real (GA36)

Este documento registra as observações feitas a partir da comparação entre
a **autópsia de referência** e o **hardware físico real** analisado neste projeto.

O objetivo é identificar:
- o que já foi confirmado como compatível
- o que ainda é incerto
- o que difere entre revisões de placa

---

## Estado do hardware analisado

- Console funcional
- Sistema original ainda operacional
- SD original preservado
- Placa aberta para inspeção visual
- Sem acesso a console serial no momento

---

## Identificação da placa

**Autópsia de referência:**
- GA36-MB V1.0 (`GA36-MB V1.0-20250730`)

**Hardware deste projeto:**
- GA36-MB V1.1 (`GA36-MB V1.1-20251025`)

**Conclusão:**
As revisões diferem apenas em layout/roteamento.
Não há indícios visuais de mudança de SoC ou arquitetura.

---

## SoC (System on Chip)

**Autópsia:**
- Allwinner A33 (confirmado por logs de boot e GPU Mali-400)

**Hardware deste projeto:**
- Chip fisicamente rotulado como “RK3326”
- Logs do sistema indicam:
  - GPU Mali-400
  - OpenGL ES 2.0
  - Arquitetura ARM

**Conclusão:**
O SoC real é Allwinner A33.
A rotulagem RK3326 é falsa.

Status: **confirmado**

---

## GPU

**Autópsia:**
- Mali-400

**Hardware deste projeto:**
- EmuELEC reporta OpenGL ES 2.0
- Shader ES 3.20 (camada de compatibilidade)

**Conclusão:**
Compatível com Mali-400.

Status: **confirmado**

---

## Kernel e boot

**Autópsia:**
- Linux 3.4.39 (sunxi)
- Boot via Android-style `boot.img`
- Uso de `script.bin` / `magic.bin`

**Hardware deste projeto:**
- Sistema original reporta EmuELEC 4.7 custom
- Build pública do EmuELEC não inicializa

**Conclusão:**
O mesmo modelo de kernel/boot está em uso.
Alta dependência de configuração legada Allwinner.

Status: **compatível (indireto)**

---

## Layout de partições

**Autópsia:**
- Layout não padrão
- Partições raw e squashfs
- FAT16 para `script.bin`

**Hardware deste projeto:**
- Ainda não dumpado localmente
- Sistema funciona apenas com SD original

**Conclusão:**
Layout altamente provável de ser idêntico ou muito próximo.

Status: **assumido (não verificado)**

---

## U-Boot

**Autópsia:**
- U-Boot legacy específico
- Configuração armazenada em partição raw

**Hardware deste projeto:**
- Boot funcional apenas com SD original
- Sem evidência de U-Boot moderno

**Conclusão:**
U-Boot compatível com autópsia.
Substituição sem dump é arriscada.

Status: **assumido (alto grau de confiança)**

---

## Periféricos

### Display
- Autópsia: display inicializado via script.bin
- Hardware real: display funcional
- Status: **compatível**

### Controles / botões
- Autópsia: input tratado por overlays
- Hardware real: controles funcionais
- Status: **compatível**

### Áudio
- Autópsia: suporte básico
- Hardware real: áudio funcional
- Status: **compatível**

---

## Console serial

- Pads serigrafados como:
  - GND
  - TX
  - RX

- Não utilizado neste projeto até o momento
- Nenhum log serial capturado

Status: **não explorado**

---

## Riscos identificados

- Perda do SD original pode tornar o console irrecuperável
- Kernel e boot dependem fortemente de configuração legada
- Tentativas de port sem baseline funcional são propensas a brick

---

## Conclusão geral

O hardware analisado neste projeto é **compatível com a autópsia de referência**.

Diferenças observadas:
- Revisão da placa (V1.1 vs V1.0)
- Nenhuma diferença crítica identificada até o momento

A autópsia permanece válida como baseline técnico para:
- documentação
- estudo
- tentativas futuras de port ou modificação

Qualquer avanço deve preservar:
- kernel funcional
- script.bin / magic.bin
- layout de partições
