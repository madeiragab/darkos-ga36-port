#!/usr/bin/env python3
r"""
Tira as 205 ROMs de NES pre-carregadas de dentro do menu.

O `SYSTEM` embute 205 arquivos em /usr/roms/nes/, e /usr/bin/mount_romfs.sh
termina com esta linha, com a condicao comentada pelo vendor:

    #if [ -z "${ROMS_PART_TOKEN}" ]; then
        rsync -a --ignore-existing --progress /usr/roms/nes/ /storage/roms/nes/
    #else
      #  echo "mmcblk0"
    #fi

Ou seja: **a cada boot** ele recopia tudo para /storage/roms/nes/. Apagar
os arquivos do cartao nao adianta, eles voltam no boot seguinte. E o
squashfs e somente leitura, entao remover a origem exigiria repack.

A saida: fazer o EmulationStation procurar ROMs de NES em OUTRA pasta. O
rsync continua despejando em /storage/roms/nes/, que ninguem mais le.

Uso (imagem):
    python unbundle_nes.py imagem.img 0x37400000
    python unbundle_nes.py imagem.img 0x37400000 --apply

Uso (cartao, PowerShell como Administrador):
    python unbundle_nes.py \\.\PhysicalDrive1 0x37400000 --apply

Reverter:
    python unbundle_nes.py ... --revert --apply
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ext4_reader import Ext4, ALIGN

CFG = "/.config/emulationstation/es_systems.cfg"
OLD = "<path>/storage/roms/nes</path>"
NEW = "<path>/storage/roms/nes-user</path>"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    dev, off = sys.argv[1], int(sys.argv[2], 0)
    apply_it = "--apply" in sys.argv
    revert = "--revert" in sys.argv
    src, dst = (NEW, OLD) if revert else (OLD, NEW)

    if dev.startswith("\\\\.\\"):
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise SystemExit("\n*** Precisa de ADMINISTRADOR. ***\n")
        except AttributeError:
            pass

    fs = Ext4(dev, off)
    ino = fs.resolve(CFG)
    if not ino:
        raise SystemExit(f"{CFG} nao encontrado")
    ind = fs.inode(ino)
    size = struct.unpack("<I", ind[4:8])[0]
    exts = fs.extents(ind[0x28:0x28 + 60])
    alloc = sum(ln for _l, _p, ln in exts) * fs.bs
    text = fs.read_inode_data(ino).decode("latin-1")

    n = text.count(src)
    print(f"{CFG}: {size} B, folga {alloc - size}")
    print(f"  {src}\n    -> {dst}")
    print(f"  ocorrencias: {n}")
    if n == 0:
        if text.count(dst):
            raise SystemExit("ja esta aplicado — nada a fazer")
        raise SystemExit("padrao nao encontrado; abortado")
    if n != 1:
        raise SystemExit(f"esperava 1 ocorrencia, achei {n}; abortado por seguranca")

    data = text.replace(src, dst).encode("latin-1")
    print(f"  tamanho {size} -> {len(data)} ({len(data)-size:+d})")
    if len(data) > alloc:
        raise SystemExit(f"nao cabe: {len(data)} > {alloc}")
    if not apply_it:
        print("\n--- SIMULACAO. rode de novo com --apply para gravar ---")
        return

    raw = dev.startswith("\\\\.\\") or dev.startswith("/dev/")
    ino_off = fs.inode_offset(ino)
    with open(dev, "r+b", buffering=0 if raw else -1) as f:
        for lblk, pblk, ln in exts:
            chunk = data[lblk * fs.bs:(lblk + ln) * fs.bs]
            chunk += b"\x00" * ((fs.bs * ln) - len(chunk))
            f.seek(off + pblk * fs.bs)
            f.write(chunk)
        if len(data) != size:
            start = ino_off - (ino_off % ALIGN)
            need = ((fs.inode_size + (ino_off - start) + ALIGN - 1) // ALIGN) * ALIGN
            f.seek(start)
            sect = bytearray(f.read(need))
            struct.pack_into("<I", sect, ino_off - start + 4, len(data))
            f.seek(start)
            f.write(bytes(sect))
        f.flush()
        os.fsync(f.fileno())

    back = Ext4(dev, off).cat(CFG)
    print(f"\nverificacao: {len(back)} B relidos, identico = {back == data}, "
          f"contem destino = {dst in back.decode('latin-1')}")
    if not revert:
        print("\nAgora crie a pasta `nes-user` na particao de ROMs e ponha os")
        print("seus jogos de NES la. A pasta `nes` continua recebendo as 205")
        print("do fabricante a cada boot, mas ninguem mais olha para ela.")


if __name__ == "__main__":
    main()
