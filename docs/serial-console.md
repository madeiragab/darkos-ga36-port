> 🇧🇷 **Português** · 🇬🇧 [English](serial-console.en.md)

# Console serial (UART de debug)

**Status: RESOLVIDO.** Este documento fecha a pendência que aparecia em
[kernel.md](kernel.md), [boot-chain.md](boot-chain.md) e no passo 4 de
[darkos-expectations.md](darkos-expectations.md).

Os pinos não foram descobertos por tentativa e erro na placa — foram lidos
do próprio `script.bin` da unidade. Ver [device-tree.md](device-tree.md)
para o método.

## Parâmetros

| Item | Valor |
|---|---|
| Porta | UART2 (`uart_debug_port = 2`) |
| Dispositivo no Linux | `/dev/ttyS2` |
| Velocidade | 115200 |
| Formato | 8N1, sem controle de fluxo |
| TX | **PB0** (`mux = 2`) |
| RX | **PB1** (`mux = 2`) |
| Nível lógico | **3,3 V** |

O environment do U-Boot já traz `console=ttyS2,115200`, ou seja, a saída
serial está **habilitada em software desde o boot0**. Não é preciso
recompilar nada para obter log — basta conectar.

## Todas as UARTs da placa

Extraído do `script.bin`:

| Seção | `uart_used` | TX | RX | Observação |
|---|---|---|---|---|
| `uart0` | 0 (desabilitada) | PF2 | PF4 | PF é o barramento do slot SD — é a UART de FEL do Allwinner |
| `uart1` | 1 | PG6 | PG7 | |
| `uart2` | 1 | **PB0** | **PB1** | **console de debug** |

`force_uart_para` repete `port = 2`, `PB0`/`PB1` — é o caminho de
recuperação forçada, mesmo alvo.

## Por que isto importa mais do que parece

O U-Boot desta placa está configurado com:

```
loglevel=0
bootdelay=0
```

Ou seja, **o console não imprime nada na tela durante o boot, por projeto**.
Quando o boot falha, o sintoma é tela preta muda — indistinguível de um
aparelho sem energia. Isso torna impossível diferenciar:

- boot0 não iniciou;
- U-Boot não achou o `boot.img`;
- kernel entrou em pânico;
- kernel subiu normalmente e apenas a inicialização do LCD falhou.

Os quatro casos produzem exatamente a mesma tela. **Sem serial, qualquer
tentativa de trocar kernel ou device tree é depuração às cegas.** Com
serial, cada um deles é uma linha de log.

## Ligação

Necessário: adaptador USB-TTL de **3,3 V** (CP2102, CH340G ou FT232RL com o
jumper em 3,3 V).

```
Adaptador            Placa
---------            -----
RX      ──────────►  PB0  (TX do console)
TX      ◄──────────  PB1  (RX do console)
GND     ─────────── GND
```

> **Nunca conecte o VCC do adaptador.** O console tem alimentação própria.
> Ligar 5 V em pino de 3,3 V danifica o SoC de forma permanente.

TX do adaptador vai no RX da placa e vice-versa — cruzado. Se não aparecer
nada, a primeira coisa a testar é inverter os dois fios de dados; trocar TX
com RX não queima nada.

## Captura

Linux:

```bash
screen /dev/ttyUSB0 115200
```

Windows (PuTTY): Serial, COM correspondente, 115200, 8N1, flow control
`None`.

Para versionar o log no repositório:

```bash
# Linux
cat /dev/ttyUSB0 | tee dumps/bootlogs/serial-boot.txt
```

## Localizar os pads fisicamente

O `script.bin` dá o **pino do SoC** (PB0/PB1), não a coordenada na PCB.
Falta correlacionar com os pads visíveis em
[`images/serial_pads.png`](../images/serial_pads.png).

Método, com o console **desligado** e multímetro em continuidade:

1. Ache o GND primeiro — encoste uma ponta no shield USB ou no negativo da
   bateria e teste cada pad candidato.
2. Com o console **ligado** e multímetro em tensão DC, meça os pads
   restantes contra o GND: a linha TX fica em repouso perto de **3,3 V** e
   cai em pulsos durante o boot; a linha RX fica flutuando ou puxada.
3. Confirme com o osciloscópio ou simplesmente conectando o adaptador e
   observando se sai texto legível a 115200.

Quando confirmar, atualize esta seção com a posição na placa e adicione a
foto anotada.

## Pendências

- [ ] Correlacionar PB0/PB1 com os pads físicos da PCB
- [ ] Capturar log de boot completo e versionar em `dumps/bootlogs/`
- [ ] Documentar se há acesso ao prompt do U-Boot (o `bootdelay=0` sugere
      que não há janela — pode ser necessário interromper via serial no
      instante certo ou reescrever a variável)
