> 🇧🇷 **Português** · 🇬🇧 [English](darkos-expectations.en.md)

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

1. ✅ **Backup íntegro do SD original**, verificado por hash.
   → [storage.md](storage.md)
2. ✅ **Cadeia de boot completamente mapeada**: offsets, environment do
   U-Boot, formato exato do `boot.img`. **Feito** por parsing offline da
   imagem. → [boot-chain.md](boot-chain.md), [image-autopsy.md](image-autopsy.md)
3. 🟡 **`script.bin` extraído e traduzido.** Localizado em `0x1366000`,
   78 seções. Display, UART e PMIC documentados. **Falta** o GPIO dos
   controles e a conversão completa para FEX.
   → [device-tree.md](device-tree.md)
4. 🟡 **Acesso serial.** Pinos identificados: **UART2, TX=PB0, RX=PB1,
   115200 8N1**, já habilitado no U-Boot. **Falta** correlacionar com os
   pads da PCB e soldar. → [serial-console.md](serial-console.md)
5. ⬜ **Device Tree novo para A33**, mais kernel mainline com Lima.
   **É o trabalho restante de verdade.**
6. 🟡 **Caminho de recuperação testado.** A regravação do SD foi validada
   na prática (o console foi recuperado duas vezes). FEL mode não foi
   testado.

O passo 5 é o único totalmente em aberto, e dentro dele o item concreto é
**escrever um driver para o painel `jd9366`**, que não existe no mainline.

## O que mudou desde a primeira versão deste documento

A frase "não dá para portar" era imprecisa. A precisa é: **o A33 tem
suporte mainline; falta a integração desta placa.**

| Componente | Situação no mainline |
|---|---|
| SoC `sun8i-a33` | `sun8i-a33.dtsi` |
| GPU Mali-400 | **Lima** (Mesa), GLES 2.0 |
| Display Engine | `sun4i-drm` + `sun8i-mixer` |
| MIPI DSI | `sun6i-mipi-dsi` |
| PMIC AXP223 | `axp20x` |
| MMC / USB / I2C / UART | suportados |
| Painel `jd9366` | **ausente** |

A ordem que funciona: **serial primeiro, device tree depois, kernel por
último.** Trocar o kernel antes de ter serial é depuração às cegas — toda
falha produz a mesma tela preta.

## Sobre PortMaster e Stardew Valley

Motivação comum de quem chega a este console, e vale registrar para não
gerar expectativa errada.

O PortMaster **suporta armhf**, então a infraestrutura não está barrada por
arquitetura. Ports 2D leves têm chance real. Mas o port de Stardew Valley
publicado para R36S **não transfere**:

| | R36S (alvo do port) | GA36-MB |
|---|---|---|
| Arquitetura | ARMv8 **64-bit** | ARMv7 **32-bit** |
| GPU | Mali-G31, GLES 3.2 | Mali-400, GLES 2.0, **sem S3TC** |
| RAM utilizável | 1 GB | ~850 MB |

As texturas do jogo são DXT comprimido; sem S3TC em hardware a
descompressão vira software, consumindo justamente a RAM e a CPU que já
faltam. **Kernel novo não muda nenhuma dessas linhas** — o limite é GPU e
memória. Ver [kernel.md](kernel.md), seção "Limites que kernel nenhum
resolve".

## Por que documentar veio primeiro

Porque a alternativa é o padrão conhecido: alguém tenta gravar uma imagem,
o console não boota, o SD original já foi sobrescrito, e o aparelho vira
lixo. O valor deste repositório não é um sistema novo — é que o **ambiente
funcional continue existindo** e que outra pessoa com o mesmo console
descubra a verdade sobre o hardware antes de destruí-lo.

## Posição atual

Portar DarkOS **não é objetivo imediato** e só será reconsiderado quando os
seis pré-requisitos acima estiverem satisfeitos. Ver [scope.md](scope.md).
