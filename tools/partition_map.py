#!/usr/bin/env python3
"""
Mapeia a tabela de particoes de uma imagem crua ou dispositivo:
MBR primaria, cadeia de particoes estendidas e deteccao de filesystem.

Uso:
    python partition_map.py IMAGEM

Tambem procura as assinaturas do bootloader Allwinner (eGON.BT0) e a
string de versao do U-Boot na area raw.

Maps MBR + extended chain. See docs/image-autopsy.md.
"""
import re
import struct
import sys

SEC = 512

TYPES = {
    0x00: "vazia", 0x05: "estendida CHS", 0x06: "FAT16", 0x0b: "FAT32",
    0x0c: "FAT32 LBA", 0x0e: "FAT16 LBA", 0x0f: "estendida LBA",
    0x82: "swap", 0x83: "Linux", 0x85: "estendida Linux", 0xee: "GPT",
}


def probe_fs(f, lba):
    f.seek(lba * SEC)
    b = f.read(SEC)
    if len(b) < SEC:
        return "?"
    f.seek(lba * SEC + 0x438)
    if f.read(2) == b"\x53\xef":
        return "ext2/3/4"
    if b[0x52:0x57] == b"FAT32":
        return "FAT32"
    if b[0x36:0x39] == b"FAT":
        return b[0x36:0x3b].decode("ascii", "replace").strip()
    f.seek(lba * SEC)
    if f.read(4) in (b"hsqs", b"sqsh"):
        return "squashfs"
    return "?"


def entries(f, lba):
    f.seek(lba * SEC)
    s = f.read(SEC)
    if len(s) < SEC or s[510:512] != b"\x55\xAA":
        return None
    out = []
    for i in range(4):
        e = s[446 + i * 16: 462 + i * 16]
        start, cnt = struct.unpack("<II", e[8:16])
        out.append((i + 1, e[4], start, cnt, e[0]))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]
    f = open(path, "rb")

    print("=== MBR primaria (LBA 0)")
    prim = entries(f, 0)
    if prim is None:
        raise SystemExit("sem assinatura 0x55AA na MBR")
    ext_lba = None
    for n, t, start, cnt, boot in prim:
        if t == 0 and cnt == 0:
            continue
        fs = probe_fs(f, start) if cnt else "?"
        print(f"  p{n}: tipo=0x{t:02x} ({TYPES.get(t,'?'):<16}) inicio={start:<10} "
              f"setores={cnt:<11} ({cnt*SEC/1024/1024:9.2f} MB)  boot=0x{boot:02x}  fs={fs}")
        if t in (0x05, 0x0f, 0x85):
            ext_lba = start

    if ext_lba is not None:
        print(f"\n=== cadeia estendida a partir de LBA {ext_lba}")
        cur, idx, seen = ext_lba, 5, set()
        while cur and cur not in seen:
            seen.add(cur)
            ents = entries(f, cur)
            if ents is None:
                print(f"  EBR @LBA {cur}: sem assinatura 0x55AA -> fim da cadeia")
                break
            _, t1, s1, c1, _ = ents[0]
            if c1:
                a = cur + s1
                print(f"  p{idx}: tipo=0x{t1:02x} ({TYPES.get(t1,'?'):<16}) "
                      f"inicio_abs={a:<10} ({a*SEC/1024/1024:9.2f} MB) "
                      f"setores={c1:<9} ({c1*SEC/1024/1024:8.2f} MB)  fs={probe_fs(f, a)}")
                idx += 1
            _, _t2, s2, c2, _ = ents[1]
            cur = ext_lba + s2 if c2 else None

    print("\n=== area raw / bootloader")
    f.seek(0)
    gap = f.read(min(64 * 1024 * 1024, 1 << 31))
    for sig in (b"eGON.BT0", b"eGON.BT1", b"TOC0"):
        i = gap.find(sig)
        print(f"  {sig.decode():<10}: {'@0x%08x (setor %d)' % (i, i // SEC) if i >= 0 else 'nao encontrado'}")
    for m in re.finditer(rb"U-Boot [0-9][^\x00\n]{0,90}", gap):
        print(f"  U-Boot    : @0x{m.start():08x}  {m.group().decode('ascii','replace')}")
        break
    f.close()


if __name__ == "__main__":
    main()
