#!/usr/bin/env python3
"""
Localiza e parseia o script.bin (formato legacy Allwinner) dentro de uma
imagem crua, sem precisar das sunxi-tools.

Uso:
    python scriptbin_parse.py IMAGEM                  # lista as secoes
    python scriptbin_parse.py IMAGEM uart_para lcd0_para power_sply
    python scriptbin_parse.py IMAGEM --all            # despeja tudo

Na imagem do GA36-MB o script.bin fica em 0x01366000 (area raw, junto ao
U-Boot) e tem 78 secoes. Ver docs/device-tree.md.

Parses legacy Allwinner script.bin. See docs/device-tree.en.md.
"""
import re
import struct
import sys

SEARCH_LIMIT = 140 * 1024 * 1024      # boot0 + U-Boot + Volumn + boot.img

PORTS = {1: "PA", 2: "PB", 3: "PC", 4: "PD", 5: "PE", 6: "PF", 7: "PG",
         8: "PH", 9: "PI", 10: "PJ", 11: "PK", 12: "PL", 13: "PM", 14: "PN"}

# tipos de valor do script.bin
T_WORD, T_STRING, T_MULTI, T_GPIO = 1, 2, 3, 4


def try_parse(data, base):
    """script.bin: u32 main_key_count, u32 version[3], depois a tabela."""
    try:
        count, = struct.unpack_from("<I", data, base)
    except struct.error:
        return None
    if not (5 <= count <= 300):
        return None
    keys = []
    for i in range(count):
        off = base + 16 + i * 40
        if off + 40 > len(data):
            return None
        name = data[off:off + 32].split(b"\x00")[0]
        if not name or not re.fullmatch(rb"[A-Za-z0-9_\-]{2,31}", name):
            return None
        nsub, koff = struct.unpack_from("<II", data, off + 32)
        if nsub > 500 or koff * 4 > len(data):
            return None
        keys.append((name.decode(), nsub, koff))
    return keys


def read_subkeys(data, base, nsub, koff):
    out = []
    for j in range(nsub):
        off = base + koff * 4 + j * 40
        if off + 40 > len(data):
            break
        name = data[off:off + 32].split(b"\x00")[0].decode("ascii", "replace")
        voff, pattern = struct.unpack_from("<II", data, off + 32)
        vtype = (pattern >> 16) & 0xFFFF
        vlen = pattern & 0xFFFF
        vpos = base + voff * 4
        val = None
        if vtype == T_WORD and vpos + 4 <= len(data):
            val = struct.unpack_from("<i", data, vpos)[0]
        elif vtype == T_STRING and vpos + vlen * 4 <= len(data):
            val = data[vpos:vpos + vlen * 4].split(b"\x00")[0].decode("ascii", "replace")
        elif vtype == T_GPIO and vpos + 24 <= len(data):
            port, pin, mul, pull, drv, dat = struct.unpack_from("<iiiiii", data, vpos)
            pname = "PL" if port == 0x100 else PORTS.get(port, f"P?{port}")
            val = f"{pname}{pin}  mux={mul} pull={pull} drv={drv} data={dat}"
        out.append((name, vtype, val))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]
    wanted = [a for a in sys.argv[2:] if not a.startswith("--")]
    dump_all = "--all" in sys.argv

    with open(path, "rb") as f:
        data = f.read(SEARCH_LIMIT)

    found = None
    for base in range(0, len(data) - 4096, 4):
        k = try_parse(data, base)
        if k and len(k) >= 20 and any(n.startswith(("uart", "lcd")) for n, _, _ in k):
            found = (base, k)
            break

    if not found:
        raise SystemExit(f"script.bin nao localizado nos primeiros "
                         f"{SEARCH_LIMIT // 1024 // 1024} MB")

    base, keys = found
    print(f"script.bin @0x{base:08x} ({base/1024/1024:.2f} MB) - {len(keys)} secoes\n")
    if not wanted and not dump_all:
        for i in range(0, len(keys), 6):
            print("  " + "  ".join(f"{n:<20}" for n, _, _ in keys[i:i + 6]))
        print("\nPasse nomes de secao como argumento, ou --all para despejar tudo.")
        return

    for name, nsub, koff in keys:
        if not dump_all and name not in wanted:
            continue
        print(f"=== [{name}]")
        for sk, vt, val in read_subkeys(data, base, nsub, koff):
            if val is None:
                print(f"   {sk:<26} (tipo {vt}, nao decodificado)")
            else:
                print(f"   {sk:<26} = {val}")
        print()


if __name__ == "__main__":
    main()
