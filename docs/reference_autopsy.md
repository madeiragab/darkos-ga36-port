Reference: R36S console clone — Autópsia técnica (baseline)

Fonte primária:
https://github.com/phaseloop/R36S-console-clone---GA36-MB-V1.0-20250730

Repositório público contendo autópsia técnica e imagem de recuperação do console clone R36S baseado na placa GA36-MB.

1. Identificação da placa analisada

Modelo da placa: GA36-MB

Revisão: V1.0

Silkscreen: GA36-MB V1.0-20250730

Esta placa corresponde ao mesmo modelo físico encontrado neste projeto, servindo como referência direta.

2. SoC e arquitetura real

SoC real identificado: Allwinner A33

GPU detectada em boot: Mali-400 (prova definitiva)

Arquitetura: ARMv7 (sunxi)

Apesar da marcação física do chip indicar RK3326, trata-se de rotulagem falsa.
Os logs de boot confirmam Allwinner A33 sem ambiguidade.

3. Kernel e boot

Kernel reportado: Linux version 3.4.39

Família: Linux-sunxi (kernel antigo, pré-mainline)

Formato de boot: Android-style boot.img (kernel + ramdisk)

Características importantes:

Não utiliza DTB moderno

Utiliza script.bin / magic.bin (formato legado da Allwinner)

Bootloader e kernel seguem padrão antigo do ecossistema Android/sunxi

4. Layout de partições (exemplo do dump original)
Partição	Tipo	Tamanho	Função
img1	FAT32	~47.6 GB	ROMs
img2	FAT16	32 MB	script.bin, magic.bin, recursos de boot
img5	raw	16 MB	Configuração do U-Boot
img6	bootimg	32 MB	Kernel + ramdisk (Android boot.img)
img7	squashfs	768 MB	SYSTEM (EmuELEC customizado)
img8	overlay RW	~1.5 GB	Userdata / overlay

Observação crítica:
Esse layout não segue padrões modernos e depende de U-Boot antigo.

5. Sistema operacional

Base: EmuELEC 4.7 altamente customizado

Origem: LibreELEC / Android híbrido

Root filesystem: squashfs (SYSTEM)

Características:

Kernel Android/sunxi antigo

Ramdisk custom

Incompatível com builds públicos oficiais do EmuELEC

Imagens genéricas não bootam

6. Observações técnicas críticas

O sistema utiliza um “franken-kernel” (sunxi + Android + LibreELEC)

script.bin funciona como DTB legado

Conversão para DTB moderno é possível, porém não trivial

Sem o SD original funcional, não há método público confiável de recuperação

7. Conclusões práticas (baseline do projeto)

Este hardware não suporta imagens modernas sem port específico

O reaproveitamento do kernel + script.bin da autópsia é o caminho mais seguro

Port para kernel moderno exige:

conversão script.bin → DTB

ajustes profundos de bootloader

provável perda de compatibilidade

8. Uso deste documento no projeto

Este arquivo é a referência técnica primária do projeto

Qualquer tentativa de modificação deve:

Comparar partições

Comparar boot.img

Comparar script.bin

Nunca substituir kernel/boot sem validação cruzada com esta autópsia