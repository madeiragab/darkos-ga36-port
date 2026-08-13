#!/usr/bin/env python3
"""
Extrai o environment do U-Boot de uma imagem crua.

Uso:
    python uboot_env.py IMAGEM [INICIO_MB] [FIM_MB]

Padrao: procura entre 60 MB e 90 MB, onde fica o environment na imagem do
GA36-MB (particao mmcblk0p5, 68 MB). Ver docs/image-autopsy.md.

Extracts the U-Boot environment from a raw image.
"""
import re
import sys

KEYS = ("disk", "mmc_root", "nand_root", "init", "console", "loglevel",
        "partitions", "bootcmd", "bootargs", "boot_normal", "setargs_mmc",
        "setargs_nand", "bootdelay", "boot_partition", "storage", "recovery")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]
    start = int(sys.argv[2]) * 1024 * 1024 if len(sys.argv) > 2 else 60 * 1024 * 1024
    end = int(sys.argv[3]) * 1024 * 1024 if len(sys.argv) > 3 else 90 * 1024 * 1024

    with open(path, "rb") as f:
        f.seek(start)
        data = f.read(end - start)

    print(f"=== variaveis de ambiente ({start/1024/1024:.0f}-{end/1024/1024:.0f} MB)")
    seen = {}
    for m in re.finditer(rb"([a-zA-Z_][a-zA-Z0-9_]{1,24})=([^\x00\n]{1,300})", data):
        k = m.group(1).decode("ascii", "replace")
        v = m.group(2).decode("ascii", "replace")
        if k not in KEYS or k in seen:
            continue
        seen[k] = v
        print(f"  @0x{start + m.start():08x}  {k}={v}")

    print("\n=== referencias a dispositivo de bloco")
    hits = set()
    for m in re.finditer(rb"/dev/(?:mmcblk\d+p?\d*|nand[a-z]?)", data):
        s = m.group().decode("ascii", "replace")
        if s in hits:
            continue
        hits.add(s)
        print(f"  @0x{start + m.start():08x}  {s}")

    if not seen:
        print("\nnada encontrado nessa faixa; tente outros limites, ex.:")
        print(f"  python {sys.argv[0]} IMAGEM 0 140")


if __name__ == "__main__":
    main()
