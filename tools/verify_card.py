#!/usr/bin/env python3
r"""
SOMENTE LEITURA. Compara um cartao gravado com a imagem de origem, byte a
byte, e diz em qual regiao esta a diferenca.

Nao escreve absolutamente nada. Use para responder "o boot foi corrompido?"
sem arriscar piorar o estado do cartao.

Uso (Linux):
    sudo python3 verify_card.py imagem.img /dev/sdX

Uso (Windows, PowerShell como Administrador):
    python verify_card.py imagem.img \\.\PhysicalDrive1

Ver docs/image-autopsy.md para o mapa de regioes.

Read-only card vs image comparison.
"""
import os
import sys

SEC = 512
CHUNK = 8 * 1024 * 1024

# limites das regioes da imagem do GA36-MB, em bytes
ZONES = [
    (0x02400000, "area raw / boot0 / U-Boot / script.bin"),
    (0x04400000, "particao Volumn (FAT16)"),
    (0x05400000, "environment do U-Boot"),
    (0x07400000, "boot.img  <-- CRITICO"),
    (0x37400000, "SYSTEM (squashfs)"),
    (0x97400000, "ext4 /storage"),
    (1 << 62, "particao de ROMs"),
]

MARKS = [
    (0x2004, b"eGON.BT0", "boot0 (Allwinner)"),
    (0x5400000, b"ANDROID!", "boot.img (kernel+initramfs)"),
]


def zone_of(off):
    for limit, name in ZONES:
        if off < limit:
            return name
    return "?"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    img, dev = sys.argv[1], sys.argv[2]
    imgsz = os.path.getsize(img)
    print(f"imagem : {img} ({imgsz/1024**2:.0f} MB)")
    print(f"cartao : {dev}\n")

    print("--- estruturas criticas no cartao ---")
    try:
        c = open(dev, "rb")
    except PermissionError:
        raise SystemExit("permissao negada: use sudo (Linux) ou "
                         "PowerShell como Administrador (Windows).")
    with c:
        for off, magic, nome in MARKS:
            c.seek(off - off % SEC)
            blk = c.read(SEC * 2)
            rel = off % SEC
            got = blk[rel:rel + len(magic)]
            print(f"  {'OK   ' if got == magic else 'FALHA'} {nome:32s} "
                  f"@0x{off:08x}  esperado={magic!r} lido={got!r}")
        for off, nome in ((0x7400000, "FAT16 EMUELEC (SYSTEM)"),
                          (0x37400000, "ext4 /storage")):
            c.seek(off)
            b = c.read(SEC)
            if nome.startswith("FAT16"):
                ok = b[510:512] == b"\x55\xAA" and b[0x36:0x39] == b"FAT"
            else:
                c.seek(off + 0x438)
                ok = c.read(2) == b"\x53\xef"
            print(f"  {'OK   ' if ok else 'FALHA'} {nome:32s} @0x{off:08x}")

    print(f"\n--- comparando {imgsz/1024**2:.0f} MB byte a byte ---")
    diffs, pos = [], 0
    with open(img, "rb") as fi, open(dev, "rb") as fc:
        while pos < imgsz:
            want = min(CHUNK, imgsz - pos)
            want = (want + SEC - 1) // SEC * SEC
            a, b = fi.read(want), fc.read(want)
            if not a:
                break
            n = min(len(a), len(b))
            if a[:n] != b[:n]:
                i = 0
                while i < n:
                    if a[i] != b[i]:
                        j = i
                        while j < n and a[j] != b[j]:
                            j += 1
                        if diffs and pos + i - diffs[-1][1] < 65536:
                            diffs[-1] = (diffs[-1][0], pos + j)
                        else:
                            diffs.append((pos + i, pos + j))
                        i = j
                    else:
                        i += 1
            pos += n
            sys.stdout.write(f"\r  {100*pos/imgsz:5.1f}%  regioes diferentes: {len(diffs)}   ")
            sys.stdout.flush()
            if len(diffs) > 400:
                print("\n  (muitas diferencas, parando)")
                break
    print()

    if not diffs:
        print("\nRESULTADO: cartao identico a imagem.")
        return
    total = sum(e - s for s, e in diffs)
    print(f"\nRESULTADO: {len(diffs)} regiao(oes) diferentes, {total/1024:.1f} KB\n")
    for s, e in diffs[:25]:
        print(f"  0x{s:09x} ({s/1024**2:9.2f} MB)  {(e-s)/1024:8.1f} KB   {zone_of(s)}")
    if len(diffs) > 25:
        print(f"  ... e mais {len(diffs)-25}")
    print("\nDiferencas no ext4 /storage sao normais depois de um boot: o "
          "EmuELEC escreve log e config.\nDiferencas em boot.img ou na area "
          "raw NAO sao normais -- ver docs/image-autopsy.md secao 6.3.")


if __name__ == "__main__":
    main()
