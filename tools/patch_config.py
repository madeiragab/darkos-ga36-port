#!/usr/bin/env python3
r"""
Aplica um conjunto curado de ajustes aos arquivos de configuracao dentro do
ext4, sem montar nada. Cobre retroarch.cfg, emuelec.conf e es_settings.cfg.

Escreve apenas dentro dos blocos ja alocados; se o conteudo crescer, usa a
folga do ultimo bloco e atualiza `i_size` no inode. Nunca aloca bloco.
Este ext4 nao tem metadata_csum, entao nao ha checksum a recalcular.

Uso (imagem):
    python patch_config.py imagem.img 0x37400000
    python patch_config.py imagem.img 0x37400000 --apply

Uso (cartao, PowerShell como Administrador):
    python patch_config.py \\.\PhysicalDrive1 0x37400000 --apply

Opcional: --only retroarch|emuelec|es

Sem --apply, so simula. Ver docs/emuelec-defects.md.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ext4_reader import Ext4, ALIGN

# ---------------------------------------------------------------- perfis
# formato "kv":  chave = "valor"      (retroarch.cfg)
# formato "eq":  chave=valor          (emuelec.conf)
# formato "xml": <tipo name="K" value="V" />   (es_settings.cfg)

PROFILES = {
    "retroarch": {
        "path": "/.config/retroarch/retroarch.cfg",
        "fmt": "kv",
        "changes": {
            # integridade de save
            "autosave_interval":                "10",
            "savefiles_in_content_dir":         "false",
            "savefile_directory":               "/storage/savefiles",
            "savestate_directory":              "/storage/savestates",
            "config_save_on_exit":              "true",
            "save_file_compression":            "false",   # SRAM crua = escrita mais rapida
            # tela: o painel e 4:3 640x480
            "rgui_aspect_ratio":                "0",       # era 6 (3:2), deixava o RGUI em letterbox
            "video_aspect_ratio":               "1.333333",
            # menu: custo de render na Mali-400
            "menu_driver":                      "rgui",
            "menu_shader_pipeline":             "0",
            "auto_shaders_enable":              "false",
            "menu_dynamic_wallpaper_enable":    "false",
            "menu_show_load_content_animation": "false",
            "savestate_thumbnail_enable":       "false",
            "menu_enable_widgets":              "false",
            "rgui_inline_thumbnails":           "false",
            "menu_show_sublabels":              "false",
            "menu_ticker_smooth":               "false",
            "menu_widget_scale_factor":         "1.000000",
            "menu_scroll_delay":                "150",      # repeticao mais rapida ao segurar
            # log: escrita constante no cartao sem utilidade
            "log_verbosity":                    "false",
            "libretro_log_level":               "3",
        },
    },
    "emuelec": {
        "path": "/.config/emuelec/configs/emuelec.conf",
        "fmt": "eq",
        "changes": {
            "system.timezone": "America/Sao_Paulo",
            "updates.enabled": "0",      # sem wifi; e este fork nao tem upstream
            "audio.bgmusic":   "0",      # decodificacao continua de musica no frontend
        },
    },
    "es": {
        "path": "/.config/emulationstation/es_settings.cfg",
        "fmt": "xml",
        "changes": {
            "GamelistViewStyle":   ("string", "basic"),      # detailed = imagem+metadado por item
            "ScreenSaverBehavior": ("string", "dim"),        # slideshow decodifica imagens
            "ScrapeVideos":        ("bool",   "false"),      # preview em video no gamelist
            "StopMusicOnScreenSaver": ("bool", "true"),
        },
    },
}


def apply_kv(text, key, val):
    pat = rf'(?m)^{re.escape(key)}[ \t]*=[ \t]*"[^"\n]*"[ \t]*$'
    return pat, f'{key} = "{val}"', text


def apply_eq(text, key, val):
    pat = rf'(?m)^{re.escape(key)}=.*$'
    return pat, f'{key}={val}', text


def apply_xml(text, key, spec):
    typ, val = spec
    pat = rf'(?m)^(\s*)<\w+ name="{re.escape(key)}" value="[^"]*" />[ \t]*$'
    m = re.search(pat, text)
    indent = m.group(1) if m else "\t"
    return pat, f'{indent}<{typ} name="{key}" value="{val}" />', text


HANDLERS = {"kv": apply_kv, "eq": apply_eq, "xml": apply_xml}


def patch_file(fs, dev, off, prof, apply_it):
    path, fmt, changes = prof["path"], prof["fmt"], prof["changes"]
    ino = fs.resolve(path)
    if not ino:
        print(f"  {path}: NAO ENCONTRADO"); return False
    ind = fs.inode(ino)
    size = struct.unpack("<I", ind[4:8])[0]
    if not (struct.unpack("<I", ind[0x20:0x24])[0] & 0x80000):
        print(f"  {path}: sem extents, pulado"); return False
    exts = fs.extents(ind[0x28:0x28 + 60])
    alloc = sum(ln for _l, _p, ln in exts) * fs.bs
    text = fs.read_inode_data(ino).decode("latin-1")
    print(f"\n{path}  ({size} B, folga {alloc - size})")

    n = 0
    for key, val in changes.items():
        pat, new, text = HANDLERS[fmt](text, key, val)
        m = re.search(pat, text)
        if not m:
            print(f"   [ausente] {key}")
            continue
        if m.group(0) == new:
            print(f"   [ok]      {key} — ja esta assim")
            continue
        print(f"   {m.group(0).strip()}\n     -> {new.strip()}")
        text = text[:m.start()] + new + text[m.end():]
        n += 1

    data = text.encode("latin-1")
    if len(data) > alloc:
        print(f"   NAO CABE: {len(data)} > {alloc} alocados — nada gravado")
        return False
    if not n:
        return False
    print(f"   tamanho {size} -> {len(data)} ({len(data)-size:+d})")
    if not apply_it:
        return True

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
    back = Ext4(dev, off).cat(path)
    print(f"   verificado: {len(back)} B relidos, identico = {back == data}")
    return True


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    dev, off = sys.argv[1], int(sys.argv[2], 0)
    apply_it = "--apply" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    if dev.startswith("\\\\.\\"):
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise SystemExit("\n*** Precisa de ADMINISTRADOR. ***\n")
        except AttributeError:
            pass

    for name, prof in PROFILES.items():
        if only and name != only:
            continue
        patch_file(Ext4(dev, off), dev, off, prof, apply_it)

    if not apply_it:
        print("\n--- SIMULACAO. rode de novo com --apply para gravar ---")


if __name__ == "__main__":
    main()
