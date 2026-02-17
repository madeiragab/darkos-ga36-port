# Reference: R36S console clone — Autopsy (resumo técnico)

**Origem:** https://github.com/phaseloop/R36S-console-clone---GA36-MB-V1.0-20250730/blob/main/README.md
repositório público contendo autópsia / recovery image para GA36-MB (R36S clone).  
**Link citado no original:** Mediafire (r36-a33-recovery-img.zip) — ver README da autópsia.

## Resumo técnico (o que o autor documentou)
- **Placa alvo do autor:** GA36-MB V1.0 (silk: `GA36-MB V1.0-20250730`).
- **SoC identificado:** Allwinner A33 (apresenta GPU Mali-400).
- **Kernel reportado no boot:** `Linux version 3.4.39` (sunxi / Linux-sunxi family).
- **Formato de boot:** Android-style bootimg (kernel + ramdisk), com uso de `script.bin` (formato antigo do Allwinner) — **sem DTB moderno**.
- **Partition scheme (exemplo do image dump):**
Device Start End Size
img1 (FAT32) 4.956.160 104.855.550 ~47.6G (ROMs)
img2 (FAT16) 73.728 139.263 32M (magic.bin/script.bin, boot resources)
img5 (raw) 139.264 172.031 16M (U-Boot config raw)
img6 (bootimg) 172.032 237.567 32M (Android bootimg: kernel + ramdisk)
img7 (squashfs) 237.568 1.810.431 768M (SYSTEM squashfs - EmuELEC)
img8 (rw overlay) 1.810.432 4.956.159 1.5G (userdata / overlay)

- **Bootloader:** U-Boot / sunxi tools; uboot config em partição separada (conteúdo legível com prefixo binário).
- **Sistema root:** `SYSTEM` contém squashfs com EmuELEC custom (LibreELEC/EmuELEC derivado).
- **Observações-chave do autor:**
- O console recebe um *franken-kernel* baseado em Linux-sunxi (antigo).
- Muitos artefatos são de targets Android/LibreELEC, daí o formato bootimg e ramdisk.
- `script.bin` / `magic.bin` age como DTB antigo; pode ser convertido manualmente para DTB.
- Sem o SD original funcionando, o dispositivo fica difícil de recuperar com imagens genéricas.

## Conclusões práticas do autor
- Reaproveitar kernel/DTB do autopsy é a abordagem mais segura para esse hardware.
- Portar para um kernel moderno ou DTB “padrão” exige trabalho significativo (sunxi script.bin → DTB conversion, ajustes de boot).
- O autor disponibiliza uma recovery image e dumps que servem como baseline.

## Uso deste documento
- Este arquivo **deve** ser referência primária para qualquer trabalho de port ou modificação no seu GA36-MB.
- Antes de qualquer tentativa de substituição de kernel/DTB, comparar seu `bootimg`, `script.bin` e partições com os dumps do autopsy.