# Arquivos de referência da autópsia (GA36 / R36S clone)

Este documento cataloga e descreve os arquivos disponibilizados no repositório de autópsia
utilizado como **referência técnica primária** para este projeto.

⚠️ Importante:
- Estes arquivos **NÃO foram produzidos neste projeto**
- Eles pertencem ao autor da autópsia original
- Neste repositório, eles são usados **apenas como referência técnica**
- Arquivos binários **não são versionados aqui**, apenas documentados

---

## Lista de arquivos analisados

### 1. `first-1kb-of-sd-card-image.img.gz`

**Tipo:** dump binário (1 KB inicial do cartão SD)  
**Origem:** Autópsia GA36-MB (repositório original)

**Descrição técnica:**
Dump dos primeiros 1024 bytes do cartão SD original do console.
Contém:
- MBR
- offsets de partições
- informações iniciais de boot (sunxi legacy)

**Importância:**
Alta.  
Allwinner A33 com U-Boot antigo é extremamente sensível ao layout físico do SD.
Este dump permite:
- entender o esquema real de partições
- evitar recriação incorreta do layout

**Uso neste projeto:**
- Referência para comparação de layout
- Não utilizado diretamente em flash ou boot

**Status:** Referência externa (não versionado neste repositório)

---

### 2. `kernel.img.zip`

**Tipo:** imagem de kernel compactada  
**Origem:** Autópsia GA36-MB

**Descrição técnica:**
Kernel funcional utilizado pelo console GA36 clone.
Características observadas:
- Linux-sunxi (kernel antigo)
- Compatível com Allwinner A33
- GPU Mali-400 detectada corretamente
- Utilizado via Android-style `boot.img`

**Importância:**
Crítica.  
Builds públicas modernas do EmuELEC **não funcionam** neste hardware.
Este kernel representa um **baseline funcional comprovado**.

**Uso neste projeto:**
- Referência para entendimento de compatibilidade
- Base conceitual para qualquer tentativa futura de port

**Status:** Referência externa (não versionado neste repositório)

---

### 3. `magic.bin`

**Tipo:** binário de configuração de hardware (Allwinner legacy)  
**Origem:** Autópsia GA36-MB

**Descrição técnica:**
Arquivo clássico do ecossistema Allwinner antigo.
Funciona como:
- DTB legado
- Configuração de DRAM
- Mapeamento de GPIO
- Inicialização de display, clocks e periféricos

Equivalente conceitual a um DTB moderno, porém em formato proprietário/antigo.

**Importância:**
Máxima.  
Sem este arquivo:
- RAM pode não inicializar
- Tela não liga
- Boot falha silenciosamente

**Uso neste projeto:**
- Referência obrigatória para entendimento do hardware
- Qualquer alteração de kernel depende dele

**Status:** Referência externa (não versionado neste repositório)

---

### 4. `uboot-partition.img.gz`

**Tipo:** dump de partição raw (U-Boot)  
**Origem:** Autópsia GA36-MB

**Descrição técnica:**
Imagem da partição que contém:
- U-Boot
- environment
- parâmetros específicos da placa

Este U-Boot:
- entende o layout antigo do SD
- carrega `boot.img` no formato Android
- é específico para Allwinner A33 / GA36-MB

**Importância:**
Crítica.  
U-Boot genérico ou moderno **não é compatível** sem adaptação profunda.

**Uso neste projeto:**
- Referência para recuperação
- Entendimento do processo de boot real

**Status:** Referência externa (não versionado neste repositório)

---

### 5. `overlays.zip`

**Tipo:** conjunto de overlays/configurações  
**Origem:** Autópsia GA36-MB

**Descrição técnica:**
Arquivos auxiliares utilizados pelo sistema em runtime.
Possíveis funções:
- ajustes de framebuffer
- input (botões/controles)
- áudio
- periféricos menores

**Importância:**
Média.  
O sistema pode bootar sem eles, mas com funcionalidades quebradas.

**Uso neste projeto:**
- Referência para entender ajustes específicos
- Possível reaproveitamento futuro

**Status:** Referência externa (não versionado neste repositório)

---

## Diretriz do projeto sobre estes arquivos

- Nenhum destes arquivos será modificado sem entendimento prévio
- Nenhum será redistribuído sem necessidade clara
- Toda tentativa de port ou modificação **parte destes dados**
- Este conjunto define o **baseline técnico funcional** do hardware GA36 clone

---

## Observação final

Este projeto não tenta “modernizar à força” o hardware.
A prioridade é:
1. entender o que funciona
2. documentar por que funciona
3. só então considerar mudanças

Qualquer abordagem fora disso tende a resultar em brick.
