#!/usr/bin/env python3
r"""
Faz o botao de power desligar o console de forma limpa.

O `SYSTEM` traz /etc/systemd/logind.conf com:

    [Login]
    HandlePowerKey=ignore

ou seja, o sistema recebe KEY_POWER e descarta. Nada trata o botao, e a
unica coisa que acontece e o corte por hardware da PMIC quando voce segura
— que leva o save junto.

/etc/systemd/logind.conf.d e um symlink para /storage/.config/logind.conf.d,
que fica no ext4 gravavel. Um drop-in ali sobrescreve o padrao sem tocar no
squashfs.

O diretorio so contem `README`. Como `README` e `z.conf` tem exatamente 6
bytes, a entrada de diretorio e renomeada no lugar, sem alterar `rec_len`,
`name_len` nem qualquer estrutura. O conteudo e substituido dentro dos
blocos ja alocados e o `i_size` do inode e ajustado.

Uso (imagem):
    python enable_powerkey.py imagem.img 0x37400000
    python enable_powerkey.py imagem.img 0x37400000 --apply

Uso (cartao, PowerShell como Administrador):
    python enable_powerkey.py \\.\PhysicalDrive1 0x37400000 --apply

Reverter:
    python enable_powerkey.py ... --revert --apply
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ext4_reader import Ext4, ALIGN

DIRPATH = "/.config/logind.conf.d"
OLD, NEW = b"README", b"z.conf"

DROPIN = b"""# Drop-in gerado por tools/enable_powerkey.py
# O padrao do SYSTEM e HandlePowerKey=ignore, o que faz o botao nao ter
# efeito nenhum em software. Com poweroff, um toque curto desliga limpo:
# o systemd para os servicos, o RetroArch recebe SIGTERM e grava a SRAM,
# e as particoes sao desmontadas antes de o aparelho apagar.
[Login]
HandlePowerKey=poweroff
HandlePowerKeyLongPress=poweroff
"""


def find_entry(raw, name):
    """Devolve (offset_do_nome, inode, name_len) da entrada `name`."""
    p = 0
    while p < len(raw) - 8:
        child, rec_len, name_len, ftype = struct.unpack("<IHBB", raw[p:p + 8])
        if rec_len < 8:
            break
        if raw[p + 8:p + 8 + name_len] == name:
            return p + 8, child, name_len
        p += rec_len
    return None


def write_inode_data(dev, fs, off, ino, data):
    ind = fs.inode(ino)
    size = struct.unpack("<I", ind[4:8])[0]
    exts = fs.extents(ind[0x28:0x28 + 60])
    alloc = sum(ln for _l, _p, ln in exts) * fs.bs
    if len(data) > alloc:
        raise SystemExit(f"conteudo nao cabe: {len(data)} > {alloc}")
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
    dino = fs.resolve(DIRPATH)
    if not dino:
        raise SystemExit(f"{DIRPATH} nao encontrado")
    dind = fs.inode(dino)
    draw = bytearray(fs.read_inode_data(dino))
    hit = find_entry(draw, src)
    if not hit:
        other = find_entry(draw, dst)
        if other:
            raise SystemExit(f"ja esta como {dst.decode()} — nada a fazer")
        raise SystemExit(f"entrada {src.decode()} nao encontrada em {DIRPATH}")
    npos, fino, nlen = hit
    if nlen != len(dst):
        raise SystemExit(f"tamanho do nome difere ({nlen} vs {len(dst)}); abortado")

    print(f"{DIRPATH}")
    print(f"  entrada  : {src.decode()} (inode {fino}) -> {dst.decode()}")
    body = DROPIN if not revert else b"# placeholder\n"
    fsize = struct.unpack("<I", fs.inode(fino)[4:8])[0]
    print(f"  conteudo : {fsize} B -> {len(body)} B")
    print(f"\n{body.decode()}")

    if not apply_it:
        print("--- SIMULACAO. rode de novo com --apply para gravar ---")
        return

    # 1. conteudo do arquivo
    write_inode_data(dev, fs, off, fino, body)
    # 2. nome na entrada de diretorio (mesmo numero de bytes)
    draw[npos:npos + nlen] = dst
    write_inode_data(dev, fs, off, dino, bytes(draw))

    fs2 = Ext4(dev, off)
    check = fs2.cat(f"{DIRPATH}/{dst.decode()}")
    print(f"verificacao: {DIRPATH}/{dst.decode()} = "
          f"{len(check) if check is not None else 'AUSENTE'} bytes, "
          f"identico = {check == body}")
    if not revert:
        print("\nA partir do proximo boot, um toque curto no botao de power")
        print("desliga o console de forma limpa. Segurar continua cortando na")
        print("PMIC — isso e hardware e nao tem correcao por software.")


if __name__ == "__main__":
    main()
