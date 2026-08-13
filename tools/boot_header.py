#!/usr/bin/env python3
"""
Parseia o header de um boot.img Android (formato usado pelo U-Boot da
Allwinner) e varre a imagem procurando superblocos ext4 e squashfs.

Uso:
    python boot_header.py IMAGEM              # varre e mostra tudo
    python boot_header.py IMAGEM 0x5400000    # parseia um header especifico

Na imagem do GA36-MB o boot.img fica em 0x5400000 (84 MB).
Ver docs/image-autopsy.md.

Android boot.img header + filesystem superblock scan.
"""
import datetime
import struct
import sys

SEC = 512


def txt(b):
    return b.split(b"\x00")[0].decode("ascii", "replace")


def parse_boot(f, off):
    f.seek(off)
    h = f.read(1648)
    if h[:8] != b"ANDROID!":
        return False
    ks, ka, rs, ra, ss, sa, tags, psz = struct.unpack("<8I", h[8:40])
    # um header valido tem page_size potencia de 2 entre 512 e 16384
    if psz not in (512, 1024, 2048, 4096, 8192, 16384):
        print(f"  @0x{off:08x}: assinatura ANDROID! mas page_size={psz} "
              f"invalido -> falso positivo (string dentro do U-Boot)")
        return False
    print(f"=== boot.img @0x{off:08x} ({off/1024/1024:.2f} MB)")
    print(f"  page_size : {psz}")
    print(f"  kernel    : {ks} B ({ks/1024/1024:.2f} MB) @load 0x{ka:08x}")
    print(f"  ramdisk   : {rs} B ({rs/1024/1024:.2f} MB) @load 0x{ra:08x}")
    print(f"  second    : {ss} B @load 0x{sa:08x}")
    print(f"  tags addr : 0x{tags:08x}")
    print(f"  name      : {txt(h[48:64])!r}")
    print(f"  cmdline   : {txt(h[64:576])!r}")
    n = lambda x: ((x + psz - 1) // psz) * psz
    rd = off + psz + n(ks)
    f.seek(rd)
    magic = f.read(4)
    kind = ("gzip" if magic[:2] == b"\x1f\x8b" else
            "lz4" if magic[:4] == b"\x04\x22\x4d\x18" else
            "xz" if magic[:2] == b"\xfd7" else "?")
    print(f"  ramdisk em: 0x{rd:08x}  magic={magic.hex()} ({kind})")
    print(f"  extrair   : dd if=IMG bs=1 skip={rd} count={rs} | gunzip | cpio -idv")
    return True


def scan(f, size):
    print("\n=== varredura de superblocos (granularidade 1 MB)")
    for base in range(0, size, 1024 * 1024):
        f.seek(base + 0x438)
        if f.read(2) == b"\x53\xef":
            f.seek(base + 0x400)
            sb = f.read(1024)
            _inodes, blocks = struct.unpack("<II", sb[0:8])
            log_bs, = struct.unpack("<I", sb[24:28])
            bs = 1024 << log_bs
            print(f"  ext4     @0x{base:09x} ({base/1024/1024:8.1f} MB)  "
                  f"{blocks*bs/1024/1024:.0f} MB  bs={bs}")
        f.seek(base)
        if f.read(4) == b"hsqs":
            f.seek(base)
            sb = f.read(96)
            _ino, mkfs, bsize, _fr = struct.unpack("<IIII", sb[4:20])
            comp, blog, _fl, _ni, smaj, _smin = struct.unpack("<HHHHHH", sb[20:32])
            _root, used = struct.unpack("<QQ", sb[32:48])
            if smaj == 4 and bsize == (1 << blog):
                ts = datetime.datetime.fromtimestamp(mkfs).strftime("%Y-%m-%d %H:%M")
                comps = {1: "gzip", 2: "lzma", 3: "lzo", 4: "xz", 5: "lz4", 6: "zstd"}
                print(f"  squashfs @0x{base:09x} ({base/1024/1024:8.1f} MB)  "
                      f"{used/1024/1024:.2f} MB  bs={bsize}  "
                      f"comp={comps.get(comp, comp)}  build={ts}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]
    import os
    size = os.path.getsize(path) if os.path.isfile(path) else 0
    with open(path, "rb") as f:
        if len(sys.argv) > 2:
            parse_boot(f, int(sys.argv[2], 0))
        else:
            f.seek(0)
            data = f.read(min(size or 256 * 1024 * 1024, 256 * 1024 * 1024))
            i = 0
            while True:
                i = data.find(b"ANDROID!", i)
                if i < 0:
                    break
                parse_boot(f, i)
                i += 8
            if size:
                scan(f, size)


if __name__ == "__main__":
    main()
