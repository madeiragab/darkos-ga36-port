#!/usr/bin/env python3
r"""
Altera chaves do retroarch.cfg dentro do ext4, sem montar nada.

Escreve SOMENTE dentro dos blocos que o arquivo ja ocupa: cada linha
alterada mantem exatamente o mesmo numero de bytes, ajustando os espacos
em volta do '='. Nada de inode, bitmap ou realocacao e tocado.

Uso (imagem):
    python patch_retroarch.py imagem.img 0x37400000
    python patch_retroarch.py imagem.img 0x37400000 --apply

Uso (cartao, PowerShell como Administrador):
    python patch_retroarch.py \\.\PhysicalDrive1 0x37400000 --apply

Sem --apply, so simula. Ver docs/emuelec-defects.md.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ext4_reader import Ext4, ALIGN

CFG = "/.config/retroarch/retroarch.cfg"

# chave -> valor novo.  Ajuste aqui se quiser outro conjunto.
CHANGES = {
    "autosave_interval":                "10",     # grava SRAM a cada 10 s
    "menu_driver":                      "rgui",   # XMB e caro demais na Mali-400
    "menu_shader_pipeline":             "0",
    "auto_shaders_enable":              "false",
    "menu_dynamic_wallpaper_enable":    "false",
    "savestate_thumbnail_enable":       "false",
    "menu_show_load_content_animation": "false",
}


def fit(key, val, width):
    """Monta 'key = "val"' com exatamente `width` bytes, ou None."""
    for sep in (" = ", " =", "= ", "="):
        s = f'{key}{sep}"{val}"'
        if len(s) <= width:
            return s + " " * (width - len(s))
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    dev, off = sys.argv[1], int(sys.argv[2], 0)
    apply_it = "--apply" in sys.argv

    if dev.startswith("\\\\.\\"):
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise SystemExit("\n*** Precisa de ADMINISTRADOR para acessar o disco. ***\n")
        except AttributeError:
            pass

    fs = Ext4(dev, off)
    ino = fs.resolve(CFG)
    if not ino:
        raise SystemExit(f"{CFG} nao encontrado")

    ind = fs.inode(ino)
    size = struct.unpack("<I", ind[4:8])[0]
    flags = struct.unpack("<I", ind[0x20:0x24])[0]
    if not (flags & 0x80000):
        raise SystemExit("arquivo sem extents; nao suportado por esta ferramenta")
    exts = fs.extents(ind[0x28:0x28 + 60])
    data = bytearray(fs.read_inode_data(ino))
    print(f"{CFG}: inode={ino} {size} bytes, {len(exts)} extent(s)")

    changed, skipped = [], []
    for key, val in CHANGES.items():
        m = re.search(rf'(?m)^{re.escape(key)}\s*=\s*"[^"\n]*"[ \t]*$', data.decode("latin-1"))
        if not m:
            skipped.append((key, "chave nao encontrada"))
            continue
        old = m.group(0)
        new = fit(key, val, len(old))
        if new is None:
            skipped.append((key, f"nao cabe em {len(old)} bytes"))
            continue
        if old == new:
            skipped.append((key, "ja esta no valor desejado"))
            continue
        data[m.start():m.end()] = new.encode("latin-1")
        changed.append((old.strip(), new.strip()))

    print()
    for old, new in changed:
        print(f"  {old}\n    -> {new}")
    for key, why in skipped:
        print(f"  [pulado] {key}: {why}")

    if not changed:
        print("\nnada a fazer.")
        return
    if len(data) != size:
        raise SystemExit("tamanho mudou; abortado (isso nao deveria acontecer)")

    if not apply_it:
        print("\n--- SIMULACAO. rode de novo com --apply para gravar ---")
        return

    bak = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "retroarch.cfg.bak")
    if not os.path.exists(bak):
        with open(bak, "wb") as f:
            f.write(fs.read_inode_data(ino))
        print(f"\nbackup: {bak}")

    raw = dev.startswith("\\\\.\\") or dev.startswith("/dev/")
    with open(dev, "r+b", buffering=0 if raw else -1) as f:
        for lblk, pblk, ln in exts:
            chunk = bytes(data[lblk * fs.bs:(lblk + ln) * fs.bs])
            if len(chunk) % ALIGN:
                chunk += b"\x00" * (ALIGN - len(chunk) % ALIGN)
            f.seek(off + pblk * fs.bs)
            f.write(chunk)
        f.flush()
        os.fsync(f.fileno())

    fs2 = Ext4(dev, off)
    back = fs2.read_inode_data(fs2.resolve(CFG))
    ok = all(f'"{v}"' in back.decode("latin-1").split(f"\n{k}")[1].split("\n")[0]
             for k, v in CHANGES.items()
             if f"\n{k}" in back.decode("latin-1"))
    print(f"\nverificacao: {len(back)} bytes relidos, valores conferem = {ok}")
    print("\nO RetroArch regrava esse arquivo ao sair (config_save_on_exit=true),")
    print("entao os valores novos passam a ser os dele a partir do proximo boot.")


if __name__ == "__main__":
    main()
