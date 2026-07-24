# DarkOS: expectativas vs. realidade

O nome do repositório (`darkos-ga36-port`) reflete a **motivação inicial** do
projeto. Este documento explica por que o port não aconteceu, o que seria
necessário para acontecer, e por que documentar veio antes.

## A expectativa inicial

O console é vendido como "R36S / RK3326". Como existem imagens de DarkOS e
de outros sistemas para R36S genuíno, a expectativa natural é:
baixar a imagem, gravar no SD, pronto.

## A realidade

O console **não usa o SoC anunciado**. É um clone com chip remarcado:

| Anunciado | Real |
|---|---|
| Rockchip RK3326 | Allwinner A33 (`sun8i`, Cortex-A7 quad) |
| Imagens públicas compatíveis | EmuELEC 4.7 custom, build específica |
| Device Tree (DTB) | `script.bin` legado |
| Kernel razoavelmente recente | Linux sunxi 3.4.x |

**Gravar uma imagem de R36S neste console não boota** — e, se o SD original
for sobrescrito no processo, o console vira lixo eletrônico.

## O que seria necessário para um port real

Em ordem de dependência — cada item exige o anterior:

1. **Backup íntegro do SD original**, verificado por hash.
   → ver [storage.md](storage.md)
2. **Cadeia de boot completamente mapeada**: offsets, environment do U-Boot,
   formato exato do `boot.img`.
   → ver [boot-chain.md](boot-chain.md)
3. **`script.bin` extraído e traduzido** para FEX legível, com GPIO, display,
   DRAM e clocks documentados.
   → ver [device-tree.md](device-tree.md)
4. **Acesso serial funcionando** (pads TX/RX/GND identificados e soldados).
   Sem console serial, uma falha de boot é uma tela preta sem diagnóstico —
   é a diferença entre depurar e adivinhar.
5. **Device Tree novo construído do zero** para A33, a partir dos valores do
   passo 3, mais um kernel mainline com suporte a A33 e à Mali-400.
6. **Caminho de recuperação testado** (FEL mode ou regravação do SD) —
   comprovadamente funcional **antes** da primeira tentativa de boot
   modificado.

Hoje os passos 2 a 6 estão pendentes. O passo 1 está feito.

## Por que documentar veio primeiro

Porque a alternativa é o padrão conhecido: alguém tenta gravar uma imagem,
o console não boota, o SD original já foi sobrescrito, e o aparelho vira
lixo. O valor deste repositório não é um sistema novo — é que o **ambiente
funcional continue existindo** e que outra pessoa com o mesmo console
descubra a verdade sobre o hardware antes de destruí-lo.

## Posição atual

Portar DarkOS **não é objetivo imediato** e só será reconsiderado quando os
seis pré-requisitos acima estiverem satisfeitos. Ver [scope.md](scope.md).
