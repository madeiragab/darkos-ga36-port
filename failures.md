> 🇧🇷 **Português** · 🇬🇧 [English](failures.en.md)

# Registro de falhas e becos sem saída

Este arquivo existe para que **ninguém repita o mesmo erro duas vezes** —
nem eu, nem quem encontrar este repositório com o mesmo console na mão.

Falha documentada é conhecimento. Falha esquecida é console brickado.

## Como registrar

Uma entrada por tentativa, no formato:

```markdown
### AAAA-MM-DD — Título curto do que foi tentado

**Hipótese:** o que se esperava que acontecesse
**Ação:** o que foi feito exatamente (comandos, arquivos, versões)
**Resultado:** o que aconteceu de fato
**Diagnóstico:** por que falhou (ou "desconhecido")
**Recuperação:** como o console voltou ao estado funcional
**Lição:** o que muda na próxima tentativa
```

Registrar **antes** de tentar de novo. Se o resultado for "desconhecido",
registre assim mesmo — meia informação vale mais que nenhuma.

---

## Falhas conhecidas (herdadas da comunidade e da autópsia)

Estas não foram testadas nesta unidade — estão aqui porque o resultado é
previsível e destrutivo. **Não sirva de cobaia para confirmá-las.**

### Gravar imagem pública de R36S / RK3326

**Resultado:** não boota. O SoC real é Allwinner A33, não RK3326.
**Agravante:** o processo sobrescreve o SD original. Sem backup, o console
fica inutilizável.
**Lição:** o silk do chip não é fonte de verdade — ver
[docs/kernel.md](docs/kernel.md) para confirmar o SoC real.

### Gravar EmuELEC oficial (build pública)

**Resultado:** não boota. O sistema de fábrica é uma build custom
(`GA36-UDT-EE-TF-R-20250818`) compilada para A33.
**Lição:** a build custom é o único baseline funcional comprovado.

### Reparticionar o SD com ferramenta gráfica

**Resultado:** brick. O boot depende do layout físico e de uma partição raw
(~16 MB, U-Boot) que ferramentas gráficas tratam como espaço não alocado.
**Lição:** backup bit-a-bit com `dd`, nunca cópia de arquivos — ver
[docs/storage.md](docs/storage.md).

### Trocar o kernel mantendo o resto

**Resultado:** falha silenciosa — tela preta, sem log, sem indicação do
estágio que quebrou.
**Diagnóstico:** o kernel novo não interpreta o `script.bin` legado, e o
U-Boot espera `boot.img` no formato Android.
**Lição:** sem acesso serial, esse tipo de falha é indepurável — ver
[docs/device-tree.md](docs/device-tree.md).

---

## Falhas registradas nesta unidade

_Nenhuma até o momento — nenhuma modificação destrutiva foi tentada._

O estado atual é: boot funcional, backup do SD realizado, hardware
identificado. Toda tentativa futura deve ser registrada acima **antes** de
ser repetida.
