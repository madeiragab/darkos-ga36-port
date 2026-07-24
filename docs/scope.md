# Escopo do projeto

Este documento define **o que este repositório é e o que ele não é**, para
evitar expectativas que levam a brick.

## O que está no escopo

1. **Documentar** o hardware real da placa GA36-MB V1.1 (Allwinner A33),
   contrariando o silk "RK3326" impresso no encapsulamento.
2. **Preservar** o ambiente funcional: backup do SD original, catalogação
   dos artefatos de boot e registro das saídas de diagnóstico.
3. **Explicar** por que o sistema atual funciona — cadeia de boot,
   configuração de hardware por `script.bin`, kernel legado.
4. **Evitar brick** em outras unidades, registrando o que não fazer e o que
   já falhou.

## O que está fora do escopo (por enquanto)

- **Portar DarkOS, EmuELEC moderno ou qualquer distribuição nova.** Só será
  considerado depois que a cadeia de boot estiver completamente entendida —
  ver [darkos-expectations.md](darkos-expectations.md).
- **Recompilar o kernel.** O kernel legado sunxi 3.4.x é o único baseline
  funcional comprovado.
- **Redistribuir binários de terceiros.** Os artefatos da autópsia de
  referência são catalogados e descritos, nunca versionados aqui — ver
  [../reference/autopsy/files.md](../reference/autopsy/files.md).

## Princípio de trabalho

A ordem é sempre a mesma, e inverter essa ordem é como se brica um console:

1. entender o que funciona;
2. documentar por que funciona;
3. só então considerar mudanças.

## Critério de "confirmado"

Neste repositório uma informação só é marcada como **confirmada** quando vem
de uma destas fontes:

| Fonte | Exemplo |
|---|---|
| Silk lido diretamente na PCB | revisão `GA36-MB V1.1-20251025` |
| Saída de comando na unidade | `/proc/cpuinfo`, `uname -a`, `dmesg` |
| Log do sistema em execução | detecção da GPU Mali-400 |
| Autópsia independente de terceiros | layout de partições, artefatos de boot |

Tudo o mais é marcado explicitamente como **pendente** ou **não confirmado**.
