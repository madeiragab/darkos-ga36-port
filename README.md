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

- **Placa:** GA36-MB  
- **Revisão documentada neste repo:** V1.1 (silk: `GA36-MB V1.1-20251025`)
- **SoC real:** Allwinner A33 (sunxi)
- **GPU:** Mali-400 (confirmada por logs do EmuELEC)
- **Kernel:** Linux sunxi 3.4.x (legado)
- **Boot:** Android-style `bootimg` + `ramdisk`
- **Configuração de hardware:** `script.bin` (Allwinner legacy, não DTB)
- **Sistema:** EmuELEC 4.7 customizado especificamente para A33

O silk “RK3326” no chip é **remarking deliberado**.  
O comportamento elétrico, o kernel, o bootloader e a GPU confirmam que **não se trata de RK3326 real**.

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
├─ README.md                → Visão geral do projeto
├─ hardware.md              → Documentação detalhada do hardware
├─ docs/
│  └─ reference_autopsy.md  → Resumo da autópsia externa (terceiros)
├─ images/                  → Fotos da placa e componentes
└─ dumps/
   ├─ bootlogs/              → Logs do sistema em execução
   └─ partitions/            → Informações de partições do SD

 🧠 Referências importantes
Este trabalho é baseado e validado por uma autópsia independente do mesmo console,
que identificou corretamente o uso de Allwinner A33 e documentou o layout de boot e partições.

Resumo dessa análise pode ser encontrado em:

docs/reference_autopsy.md

❌ O que NÃO fazer
Não formatar o SD original sem backup

Não gravar imagens genéricas de EmuELEC

Não tentar kernels modernos sem entender o boot

Não assumir compatibilidade com RK3326

Essas ações quase sempre resultam em brick permanente.

✅ Status atual
 Hardware identificado

 Fake RK3326 confirmado

 Sistema funcional preservado

 Dumps completos versionados

 Bootimg analisado

 Script.bin documentado

📌 Aviso final
Este projeto não tem vínculo com fabricantes ou vendedores.
Toda a documentação aqui existe porque o hardware mente sobre si mesmo.

Se você possui este console, faça backup antes de qualquer coisa.