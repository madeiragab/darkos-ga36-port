> 🇧🇷 **Português** · 🇬🇧 [English](device-tree.en.md)

# Configuração de hardware: script.bin, não Device Tree

Esta é a diferença que mais confunde quem chega a esta placa vindo de
hardware ARM moderno.

## O que muda

| | Sistema moderno | GA36-MB (Allwinner legacy) |
|---|---|---|
| Arquivo | `.dtb` (compilado de `.dts`) | `script.bin` |
| Formato | Device Tree Blob, aberto e documentado | Proprietário/antigo (`FEX` compilado) |
| Ferramenta | `dtc` | `fex2bin` / `bin2fex` (sunxi-tools) |
| Onde vive | Partição de boot, ao lado do kernel | **Área raw**, embutido junto ao U-Boot |
| Editável? | Sim, com `dtc` | Sim — **com risco** |

## Localização confirmada

**`script.bin` está em `0x01366000` (19,40 MB), na área raw**, junto ao
U-Boot — **não** na partição FAT16 `Volumn`, como esta página afirmava
antes. A FAT16 contém apenas fontes, `bootlogo.bmp` e `magic.bin`.

Contém **78 seções**. Extraído e parseado com
[`tools/scriptbin_parse.py`](../tools/scriptbin_parse.py); método e demais
offsets em [image-autopsy.md](image-autopsy.md).

Seções presentes (parcial):

```
product platform target key_detect_en fel_key power_sply card_boot
card0_boot_para card2_boot_para twi_para uart_para force_uart_para
jtag_para clock pm_para dram_para wakeup_src_para twi0 twi1 twi2
uart0 uart1 uart2 uart3 uart4 spi0 spi1 spi_devices spi_board0
ctp_para ctp_list_para tkey_para motor_para ths_para cooler_table
nand0_para disp_init lcd0_para pwm0_para ...
```

## Valores extraídos

Estes são os dados que um Device Tree novo precisa reproduzir. Todos lidos
da unidade, não de documentação genérica do A33.

### Display — `lcd0_para`

| Chave | Valor |
|---|---|
| `lcd_used` | 1 |
| `lcd_driver_name` | **`jd9366_8inch`** |
| `lcd_if` | 4 (MIPI DSI) |
| `lcd_x` × `lcd_y` | **640 × 480** |
| `lcd_dclk_freq` | 30 (MHz) |
| `lcd_hbp` / `lcd_ht` / `lcd_hspw` | 120 / 1040 / 40 |
| `lcd_vbp` / `lcd_vt` / `lcd_vspw` | 12 / 518 / 6 |
| `lcd_dsi_if` | 2 |
| `lcd_dsi_lane` | 2 |
| `lcd_dsi_format` | 0 |
| `lcd_dsi_eotp` | 1 |
| `lcd_pwm_used` | 1 |
| `lcd_pwm_ch` / `lcd_pwm_freq` / `lcd_pwm_pol` | 0 / 20000 / 0 |
| `lcd_power` | **`axp22_dc1sw`** |

E de `disp_init`: `screen0_output_type = 1`, `lcd0_backlight = 204`,
`fb0_format = 10`.

> O nome do driver `jd9366_8inch` diz "8inch", mas a resolução é 640×480 —
> nome herdado do fornecedor do painel, não indicação do tamanho físico
> real desta unidade.

### UART

Detalhado em [serial-console.md](serial-console.md).

| Seção | `uart_used` | TX | RX |
|---|---|---|---|
| `uart0` | 0 | PF2 (mux 3) | PF4 (mux 3) |
| `uart1` | 1 | PG6 (mux 2) | PG7 (mux 2) |
| `uart2` | 1 | **PB0** (mux 2) | **PB1** (mux 2) |

`uart_para`: `uart_debug_port = 2`, TX `PB0`, RX `PB1`.

### PMIC — `power_sply`

Confirma **AXP22x** (a família AXP223 do A33).

| Trilho | Tensão (mV) |
|---|---|
| `dcdc1_vol` | 3000 |
| `dcdc2_vol` | 1100 |
| `dcdc3_vol` | 1200 |
| `dcdc4_vol` | 0 (desligado) |
| `dcdc5_vol` | 1500 |
| `aldo2_vol` | 2500 |
| `aldo3_vol` | 3000 |
| `dldo3_vol` | 3000 |

### DRAM

Os parâmetros de memória reais não vêm do `script.bin` e sim do header
eGON do boot0 — ver [image-autopsy.md](image-autopsy.md) §2.

## Por que ele é crítico

Sem o `script.bin` correto:

- a RAM pode não inicializar;
- a tela não liga;
- **o boot falha silenciosamente** — sem log, sem mensagem, sem indicação
  de qual estágio quebrou.

Este último ponto agora tem solução: ver
[serial-console.md](serial-console.md).

## Consequências práticas

1. **Não existe "só trocar o DTB".** Um `.dtb` mainline para A33 não é lido
   por este U-Boot nem por este kernel.
2. **Editar exige entender.** As sunxi-tools convertem `script.bin` ↔ `FEX`
   legível, mas um valor errado de DRAM ou de display deixa o console sem
   imagem.
3. **Portar sistema moderno = reconstruir isto como Device Tree.** A parte
   boa: os valores necessários deixaram de estar trancados no blob e estão
   nas tabelas acima.

## Caminho para um Device Tree mainline

O A33 (`sun8i-a33`) **tem suporte mainline**. O que já existe pronto:

| Componente | Situação no mainline |
|---|---|
| SoC | `sun8i-a33.dtsi` |
| GPU Mali-400 | **Lima** (Mesa), GLES 2.0 |
| Display Engine | `sun4i-drm` + `sun8i-mixer` |
| MIPI DSI | `sun6i-mipi-dsi` |
| PMIC AXP223 | `axp20x` |
| MMC / USB / I2C / UART | suportados |
| Painel `jd9366` | **ausente — é o trabalho novo** |

A sequência de inicialização DSI do painel precisa ser extraída do driver
`jd9366_8inch` dentro do kernel 3.4 do vendor (`SYSTEM`, squashfs lzo).

## Pendências

- [x] Localizar o `script.bin`
- [x] Parsear e documentar display, UART e PMIC
- [ ] Converter para FEX (`bin2fex`) e versionar a versão legível completa
- [ ] Mapear os pinos de GPIO dos controles (botões e analógicos)
- [ ] Extrair a sequência DSI do driver `jd9366_8inch` do kernel do vendor
- [ ] Escrever o `.dts` da placa e validar por serial
