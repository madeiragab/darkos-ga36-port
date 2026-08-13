#!/usr/bin/env python3
r"""
Altera chaves do retroarch.cfg dentro do ext4, sem montar nada.

Escreve apenas dentro dos blocos que o arquivo ja ocupa. Se o conteudo
novo for maior, usa a folga do ultimo bloco e atualiza `i_size` no inode
(4 bytes). Nunca aloca bloco, nunca mexe em bitmap. Este ext4 nao tem
metadata_csum, entao nao ha checksum a recalcular.

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

# chave -> valor novo
CHANGES = {
    # --- integridade de save ---
    "autosave_interval":                "10",                    # grava SRAM a cada 10 s
    "savefiles_in_content_dir":         "false",                 # tira do FAT32
    "savefile_directory":               "/storage/savefiles",    # ext4, com journal
    "savestate_directory":              "/storage/savestates",   # corrige o hardcode em gb/gba
    "config_save_on_exit":              "true",                  # mantem o que ajustamos
    # --- desempenho na Mali-400 ---
    "menu_driver":                      "rgui",                  # XMB e caro demais
    "menu_shader_pipeline":             "0",
    "auto_shaders_enable":              "false",
    "menu_dynamic_wallpaper_enable":    "false",
    "menu_show_load_content_animation": "false",
    "savestate_thumbnail_enable":       "false",
    "menu_enable_widgets":              "false",
    "rgui_inline_thumbnails":           "false",
}


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
        raise SystemExit("arquivo sem extents; nao suportado")
    exts = fs.extents(ind[0x28:0x28 + 60])
    alloc = sum(ln for _l, _p, ln in exts) * fs.bs
    text = fs.read_inode_data(ino).decode("latin-1")
    print(f"{CFG}")
    print(f"  inode={ino}  size={size}  alocado={alloc}  folga={alloc - size} bytes")

    changed, skipped = [], []
    for key, val in CHANGES.items():
        pat = rf'(?m)^{re.escape(key)}[ \t]*=[ \t]*"[^"\n]*"[ \t]*$'
        m = re.search(pat, text)
        new = f'{key} = "{val}"'
        if not m:
            skipped.append((key, "chave nao encontrada"))
            continue
        if m.group(0) == new:
            skipped.append((key, "ja esta no valor desejado"))
            continue
        changed.append((m.group(0), new))
        text = text[:m.start()] + new + text[m.end():]

    print()
    for old, new in changed:
        print(f"  {old}\n    -> {new}")
    for key, why in skipped:
        print(f"  [pulado] {key}: {why}")

    data = text.encode("latin-1")
    delta = len(data) - size
    print(f"\n  tamanho: {size} -> {len(data)} ({delta:+d} bytes)")
    if len(data) > alloc:
        raise SystemExit(f"nao cabe: precisaria de {len(data)} contra {alloc} alocados")
    if not changed:
        print("\nnada a fazer.")
        return
    if not apply_it:
        print("\n--- SIMULACAO. rode de novo com --apply para gravar ---")
        return

    bak = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retroarch.cfg.bak")
    if not os.path.exists(bak):
        with open(bak, "wb") as f:
            f.write(fs.read_inode_data(ino))
        print(f"\nbackup: {bak}")

    raw = dev.startswith("\\\\.\\") or dev.startswith("/dev/")
    ino_off = fs.inode_offset(ino)
    with open(dev, "r+b", buffering=0 if raw else -1) as f:
        # 1. dados, extent por extent
        for lblk, pblk, ln in exts:
            chunk = data[lblk * fs.bs:(lblk + ln) * fs.bs]
            chunk += b"\x00" * ((fs.bs * ln) - len(chunk))
            f.seek(off + pblk * fs.bs)
            f.write(chunk)
        # 2. i_size no inode (leitura alinhada, altera 4 bytes, regrava)
        if delta:
            start = ino_off - (ino_off % ALIGN)
            f.seek(start)
            sect = bytearray(f.read(((fs.inode_size + (ino_off - start) + ALIGN - 1) // ALIGN) * ALIGN))
            rel = ino_off - start
            struct.pack_into("<I", sect, rel + 4, len(data))
            f.seek(start)
            f.write(bytes(sect))
        f.flush()
        os.fsync(f.fileno())

    fs2 = Ext4(dev, off)
    back = fs2.read_inode_data(fs2.resolve(CFG))
    ok = back == data
    print(f"\nverificacao: {len(back)} bytes relidos, identico = {ok}")
    for key, val in CHANGES.items():
        line = f'{key} = "{val}"'
        print(f"  {'OK  ' if line in back.decode('latin-1') else 'FALHA'} {line}")
    print("\nO RetroArch regrava este arquivo ao sair (config_save_on_exit=true),")
    print("entao os valores novos passam a ser os dele a partir do proximo boot.")


if __name__ == "__main__":
    main()
