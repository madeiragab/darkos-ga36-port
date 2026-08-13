> 🇧🇷 **Português** · 🇬🇧 [English](README.en.md)

# GA36-MB (R36S clone) — Autópsia, preservação e documentação

Este repositório documenta um console portátil amplamente vendido como “R36S / RK3326”, mas que **não utiliza o SoC anunciado**.  
Trata-se de um **clone extremo**, com hardware deliberadamente remarcado e firmware altamente customizado.

O objetivo principal deste projeto **não é portar um novo sistema**, mas sim **preservar, entender e documentar** um ambiente funcional que, se perdido, torna o dispositivo inutilizável.

---

## ⚠️ Aviso importante (leia antes de qualquer coisa)

Este console:

- **NÃO usa RK3326**, apesar do chip estar marcado como tal
- **NÃO roda EmuELEC oficial**
- **NÃO aceita imagens públicas padrão**
- **DEPENDE do cartão SD original**

👉 **Se o SD original for perdido ou corrompido, o console vira lixo eletrônico.**

Por isso, **backup completo do SD é obrigatório** antes de qualquer experimento.

---

## 🔍 Resumo técnico (confirmado)

- **Placa:** GA36-MB, revisão V1.1 (silk: `GA36-MB V1.1-20251025`)
- **SoC real:** Allwinner **A33** — codinome `sun8iw5p1`, Cortex-A7 quad,
  **ARMv7 32-bit**
- **GPU:** Mali-400 — GLES 2.0, **sem S3TC**
- **RAM:** 1 GB DDR3 @552 MHz, **~850 MB utilizáveis** (176 MB de CMA +
  150 MB de carveout)
- **Painel:** **640 × 480**, MIPI DSI 2 lanes, `jd9366_8inch`
- **PMIC:** AXP22x
- **Kernel:** Linux sunxi **3.4.39**, compilado com gcc 4.6.3 (2012)
- **Boot:** `boot.img` Android + `script.bin` (Allwinner legacy, não DTB)
- **Serial de debug:** **UART2 — TX=PB0, RX=PB1, 115200 8N1**
- **Sistema:** EmuELEC 4.7, fork não oficial adaptado para A33

O silk “RK3326” no chip é **remarking deliberado**. A identificação como A33
não vem de comportamento observado, e sim de quatro evidências lidas
diretamente da imagem — ver
[docs/image-autopsy.md](docs/image-autopsy.md).

---

## 📚 Documentação

| Documento | Assunto |
|---|---|
| [docs/scope.md](docs/scope.md) | O que está dentro e fora do escopo, e o critério de "confirmado" |
| [docs/hardware.md](docs/hardware.md) | Componentes, provas técnicas e fotos da placa |
| **[docs/image-autopsy.md](docs/image-autopsy.md)** | **Autópsia da imagem: offsets, estruturas e defeitos, com método** |
| **[docs/serial-console.md](docs/serial-console.md)** | **Console serial — pinos, ligação e captura** |
| [docs/boot-chain.md](docs/boot-chain.md) | Cadeia de boot com offsets confirmados e environment do U-Boot |
| [docs/device-tree.md](docs/device-tree.md) | `script.bin` — valores extraídos e caminho para um DT mainline |
| [docs/kernel.md](docs/kernel.md) | Kernel 3.4.39, o que trava a modernização e o que não |
| [docs/storage.md](docs/storage.md) | Layout de partições, backup, e o perigo específico do Windows |
| **[docs/emuelec-defects.md](docs/emuelec-defects.md)** | **Defeitos do sistema de fábrica: perda de save, fsck, desempenho** |
| [docs/darkos-expectations.md](docs/darkos-expectations.md) | O que faltaria para um port real acontecer |
| [failures.md](failures.md) | Registro de falhas — leia antes de tentar qualquer coisa |
| **[tools/](tools/)** | **Scripts de análise offline (Python puro, somente leitura)** |
| [reference/autopsy/](reference/autopsy) | Catálogo dos artefatos da autópsia de referência |

---

## 🎯 Objetivos do projeto

Este projeto existe para:

- Documentar corretamente o hardware GA36-MB (A33)
- Preservar dumps, logs e informações críticas
- Tornar o sistema atual **reproduzível**
- Evitar que outros usuários brickem o console
- Criar uma base técnica sólida para estudos futuros

Portar sistemas modernos (ex: DarkOS) **não é objetivo imediato** e só será considerado após entendimento completo do boot e do hardware.

---

## 📂 Estrutura do repositório

```text
/
├─ README.md                   → Visão geral do projeto
├─ failures.md                 → Registro de falhas e becos sem saída
├─ docs/
│  ├─ scope.md                 → O que está dentro e fora do escopo
│  ├─ hardware.md              → Documentação detalhada da placa
│  ├─ image-autopsy.md         → Autópsia da imagem: offsets e defeitos
│  ├─ serial-console.md        → Console serial (PB0/PB1 @115200)
│  ├─ boot-chain.md            → Cadeia de boot (BROM → U-Boot → kernel)
│  ├─ device-tree.md           → script.bin e valores extraídos
│  ├─ kernel.md                → Kernel 3.4.39 e caminho para o mainline
│  ├─ storage.md               → Layout de partições e backup do SD
│  ├─ emuelec-defects.md       → Defeitos do sistema de fábrica
│  ├─ darkos-expectations.md   → Por que o port ainda não aconteceu
│  └─ reference_autopsy.md     → Resumo da autópsia externa (terceiros)
├─ tools/                      → Scripts de análise (Python, somente leitura)
├─ reference/autopsy/          → Catálogo dos artefatos de referência
└─ images/                     → Fotos da placa e componentes
```

Todo documento existe em português (`.md`) e inglês (`.en.md`).

---

## 🧠 Referências

Este trabalho parte de uma autópsia independente do mesmo console, que
identificou corretamente o Allwinner A33 e documentou o layout de boot.
Resumo em [docs/reference_autopsy.md](docs/reference_autopsy.md).

A camada de software foi levantada de forma independente, por parsing
offline da imagem de recovery — método e resultados em
[docs/image-autopsy.md](docs/image-autopsy.md).

---

## ❌ O que NÃO fazer

- Formatar o SD original sem backup
- **Copiar arquivos para a partição `Volumn`** — o Windows monta ela com o
  tamanho errado e pode gravar sobre o `boot.img`
- Deixar o Windows "reparar" qualquer volume do cartão
- Gravar imagens genéricas de EmuELEC
- Tentar kernels modernos antes de ter console serial
- Assumir compatibilidade com RK3326

Essas ações quase sempre resultam em brick permanente.

---

## ✅ Status atual

| Item | Estado |
|---|---|
| Hardware identificado (GA36-MB V1.1 / Allwinner A33) | ✅ Confirmado |
| Fake RK3326 confirmado | ✅ Confirmado |
| Sistema funcional preservado (backup do SD) | ✅ Feito |
| Cadeia de boot documentada com offsets exatos | ✅ Feito |
| Environment do U-Boot extraído | ✅ Feito |
| `script.bin` localizado e parseado | ✅ Feito |
| Pinos do console serial identificados | ✅ **PB0/PB1 @115200** |
| `boot.img` analisado (header, kernel, initramfs) | ✅ Feito |
| Ferramentas de análise versionadas | ✅ Feito |
| Log de boot via serial capturado | ⬜ Pendente (requer ligar o adaptador) |
| `script.bin` convertido para FEX completo | ⬜ Pendente |
| GPIO dos controles mapeado | ⬜ Pendente |
| Sequência DSI do painel `jd9366` extraída | ⬜ Pendente |
| Device tree da placa escrito | ⬜ Pendente |
| Dumps de diagnóstico do console versionados | ⬜ Pendente |

Detalhamento em [docs/scope.md](docs/scope.md) e
[docs/darkos-expectations.md](docs/darkos-expectations.md).

---

## 📌 Aviso final

Este projeto não tem vínculo com fabricantes ou vendedores.
Toda a documentação aqui existe porque o hardware mente sobre si mesmo.

Se você possui este console, **faça backup antes de qualquer coisa**.