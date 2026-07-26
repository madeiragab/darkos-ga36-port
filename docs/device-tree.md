> 🇧🇷 **Português** · 🇬🇧 [English](device-tree.en.md)

# Configuração de hardware: script.bin, não Device Tree

Esta é a diferença que mais confunde quem chega a esta placa vindo de
hardware ARM moderno.

## O que muda

| | Sistema moderno | GA36-MB (Allwinner legacy) |
|---|---|---|
| Arquivo | `.dtb` (compilado de `.dts`) | `script.bin` / `magic.bin` |
| Formato | Device Tree Blob, aberto e documentado | Proprietário/antigo (`FEX` compilado) |
| Ferramenta | `dtc` | `fex2bin` / `bin2fex` (sunxi-tools) |
| Onde vive | Partição de boot, ao lado do kernel | Partição FAT16 (~32 MB) de recursos de boot |
| Editável? | Sim, com `dtc` | Sim, com sunxi-tools — **com risco** |

## O que o script.bin controla

É o equivalente conceitual a um DTB, e responde por:

- **Inicialização da DRAM** — timings e parâmetros de memória
- **Mapeamento de GPIO** — botões, analógicos, enables
- **Clocks** — frequências de CPU, GPU e periféricos
- **Display** — inicialização do painel e do FPC
- **Áudio** — pino de enable do speaker

## Por que ele é crítico

Sem o `script.bin` correto:

- a RAM pode não inicializar;
- a tela não liga;
- **o boot falha silenciosamente** — sem log, sem mensagem, sem indicação de
  qual estágio quebrou.

É por isso que a autópsia de referência classifica a importância deste
arquivo como **máxima**: qualquer alteração de kernel depende dele.

## Consequências práticas

1. **Não existe "só trocar o DTB".** Um `.dtb` mainline para A33 não é lido
   por este U-Boot nem por este kernel.
2. **Editar exige entender.** As sunxi-tools conseguem converter
   `script.bin` ↔ `FEX` legível, mas um valor errado de DRAM ou de display
   deixa o console sem imagem — e sem imagem não há como diagnosticar sem
   acesso serial.
3. **Portar sistema moderno = reconstruir isto do zero** como Device Tree,
   a partir de valores que hoje só existem neste blob.

## Pendências

- [ ] Extrair o `script.bin` da partição de boot
- [ ] Converter para FEX (`bin2fex`) e versionar a versão legível
- [ ] Mapear e documentar os pinos de GPIO dos controles
- [ ] Documentar os timings do display

> Enquanto essas pendências existirem, qualquer tentativa de port é
> tentativa e erro com risco de brick. Ver [scope.md](scope.md).
