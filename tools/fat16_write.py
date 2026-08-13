#!/usr/bin/env python3
r"""
Grava (ou remove) um arquivo na raiz de uma particao FAT16, direto na
imagem ou no dispositivo. Usado para instalar os hooks de boot em /flash,
que o Windows nao monta.

Uso (imagem):
    python fat16_write.py imagem.img 0x7400000 --list
    python fat16_write.py imagem.img 0x7400000 --put local.sh post-flash.sh
    python fat16_write.py imagem.img 0x7400000 --put local.sh post-flash.sh --apply
    python fat16_write.py imagem.img 0x7400000 --delete post-flash.sh --apply

Uso (cartao, PowerShell como Administrador):
    python fat16_write.py \\.\PhysicalDrive1 0x7400000 --list

Sem --apply, so simula. Escreve nomes longos (LFN), entao o Linux ve
`post-flash.sh` e nao `POSTFL~1.SH`.
"""
import os
import struct
import sys

ALIGN = 512


class Fat16:
    def __init__(self, path, off, write=False):
        self.raw = path.startswith("\\\\.\\") or path.startswith("/dev/")
        self.f = open(path, "r+b" if write else "rb", buffering=0 if self.raw else -1)
        self.off = off
        b = self.pread(off, 512)
        if b[510:512] != b"\x55\xAA":
            raise SystemExit("sem assinatura 0x55AA")
        self.bps, self.spc = struct.unpack("<HB", b[11:14])
        self.rsvd, self.nfats, self.rootent = struct.unpack("<HBH", b[14:19])
        tot16, _media, self.spf = struct.unpack("<HBH", b[19:24])
        tot32, = struct.unpack("<I", b[32:36])
        self.total = tot16 or tot32
        if b[0x36:0x39] != b"FAT":
            raise SystemExit(f"nao parece FAT16: {b[0x36:0x3b]!r}")
        self.fat0 = off + self.rsvd * self.bps
        self.root = self.fat0 + self.nfats * self.spf * self.bps
        self.rootsz = self.rootent * 32
        self.data = self.root + self.rootsz
        self.csize = self.bps * self.spc
        self.nclus = (self.total - (self.rsvd + self.nfats * self.spf +
                                    self.rootsz // self.bps)) // self.spc + 2

    def pread(self, o, n):
        if not self.raw:
            self.f.seek(o); return self.f.read(n)
        s = o - (o % ALIGN)
        e = ((o + n + ALIGN - 1) // ALIGN) * ALIGN
        self.f.seek(s)
        buf = self.f.read(e - s)
        return buf[o - s:o - s + n]

    def pwrite(self, o, data):
        if not self.raw:
            self.f.seek(o); self.f.write(data); return
        s = o - (o % ALIGN)
        e = ((o + len(data) + ALIGN - 1) // ALIGN) * ALIGN
        self.f.seek(s)
        buf = bytearray(self.f.read(e - s))
        buf[o - s:o - s + len(data)] = data
        self.f.seek(s)
        self.f.write(bytes(buf))

    def read_fat(self):
        return bytearray(self.pread(self.fat0, self.spf * self.bps))

    def write_fat(self, fat):
        for i in range(self.nfats):
            self.pwrite(self.fat0 + i * self.spf * self.bps, bytes(fat))

    def sync(self):
        self.f.flush()
        os.fsync(self.f.fileno())

    def cluster_off(self, c):
        return self.data + (c - 2) * self.csize

    def read_root(self):
        return bytearray(self.pread(self.root, self.rootsz))


def lfn_checksum(short11):
    s = 0
    for ch in short11:
        s = (((s & 1) << 7) + (s >> 1) + ch) & 0xFF
    return s


def build_entries(longname, short11, first_clus, size):
    """Retorna as entradas LFN (ordem de disco) + a entrada 8.3."""
    chars = longname.encode("utf-16-le")
    per = 26                       # 13 chars UCS-2
    parts = [chars[i:i + per] for i in range(0, len(chars), per)] or [b""]
    if len(parts[-1]) < per:       # terminador 0x0000 + padding 0xFFFF
        pad = per - len(parts[-1])
        parts[-1] += b"\x00\x00" + b"\xFF" * (pad - 2) if pad >= 2 else b""
    csum = lfn_checksum(short11)
    out = b""
    for idx in range(len(parts), 0, -1):        # ordem descendente no disco
        p = parts[idx - 1].ljust(per, b"\xFF")
        seq = idx | (0x40 if idx == len(parts) else 0)
        e = bytearray(32)
        e[0] = seq
        e[1:11] = p[0:10]
        e[11] = 0x0F                            # atributo LFN
        e[12] = 0
        e[13] = csum
        e[14:26] = p[10:22]
        e[26:28] = b"\x00\x00"
        e[28:32] = p[22:26]
        out += bytes(e)
    s = bytearray(32)
    s[0:11] = short11
    s[11] = 0x20                                # arquivo comum
    struct.pack_into("<HH", s, 22, 0, 0x5921)   # hora/data fixas
    struct.pack_into("<H", s, 26, first_clus)
    struct.pack_into("<I", s, 28, size)
    return out + bytes(s)


def find_entry(root, longname):
    """Devolve (indice_inicial, n_entradas, cluster, tamanho) ou None."""
    name = []
    start = None
    for i in range(0, len(root), 32):
        e = root[i:i + 32]
        if e[0] == 0x00:
            break
        if e[0] == 0xE5:
            name, start = [], None
            continue
        if (e[11] & 0x0F) == 0x0F:
            if start is None:
                start = i
            chunk = (e[1:11] + e[14:26] + e[28:32])
            name.insert(0, chunk.decode("utf-16-le", "ignore"))
            continue
        full = "".join(name).split("\x00")[0].rstrip("\uffff")
        if full == longname:
            c, = struct.unpack("<H", e[26:28])
            sz, = struct.unpack("<I", e[28:32])
            s = start if start is not None else i
            return s, (i - s) // 32 + 1, c, sz
        name, start = [], None
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
                raise SystemExit("\n*** Precisa de ADMINISTRADOR. ***\n")
        except AttributeError:
            pass

    fs = Fat16(dev, off, write=apply_it)
    print(f"FAT16 @0x{off:x}  cluster={fs.csize} B  raiz={fs.rootent} entradas  "
          f"clusters={fs.nclus}")
    root = fs.read_root()
    fat = fs.read_fat()
    free = [c for c in range(2, fs.nclus) if struct.unpack_from("<H", fat, c * 2)[0] == 0]
    print(f"clusters livres: {len(free)} ({len(free) * fs.csize / 1024 / 1024:.1f} MB)")

    if "--list" in sys.argv:
        print("\nconteudo da raiz:")
        names, cur = [], []
        for i in range(0, len(root), 32):
            e = root[i:i + 32]
            if e[0] == 0x00:
                break
            if e[0] == 0xE5:
                cur = []; continue
            if (e[11] & 0x0F) == 0x0F:
                cur.insert(0, (e[1:11] + e[14:26] + e[28:32]).decode("utf-16-le", "ignore"))
                continue
            long = "".join(cur).split("\x00")[0].rstrip("\uffff")
            short = e[0:8].decode("ascii", "replace").strip()
            ext = e[8:11].decode("ascii", "replace").strip()
            sz, = struct.unpack("<I", e[28:32])
            names.append((long or f"{short}{'.' + ext if ext else ''}", sz, e[11]))
            cur = []
        for n, sz, attr in names:
            kind = "DIR " if attr & 0x10 else ("VOL " if attr & 0x08 else "    ")
            print(f"  {kind}{n:<24} {sz}")
        return

    if "--delete" in sys.argv:
        name = sys.argv[sys.argv.index("--delete") + 1]
        hit = find_entry(root, name)
        if not hit:
            raise SystemExit(f"{name} nao existe na raiz")
        idx, n, c, sz = hit
        print(f"\nremover {name}: {n} entradas @indice {idx // 32}, cluster {c}, {sz} B")
        if not apply_it:
            print("--- SIMULACAO ---"); return
        for k in range(n):
            root[idx + k * 32] = 0xE5
        while 2 <= c < 0xFFF8:
            nxt, = struct.unpack_from("<H", fat, c * 2)
            struct.pack_into("<H", fat, c * 2, 0)
            c = nxt
        fs.write_fat(fat)
        fs.pwrite(fs.root, bytes(root))
        fs.sync()
        print("removido.")
        return

    if "--put" not in sys.argv:
        print(__doc__); raise SystemExit(2)
    i = sys.argv.index("--put")
    src, name = sys.argv[i + 1], sys.argv[i + 2]
    data = open(src, "rb").read()
    if b"\r\n" in data:
        raise SystemExit("o arquivo tem CRLF; um script sh com \\r quebra no Linux")
    nclus_needed = max(1, (len(data) + fs.csize - 1) // fs.csize)
    print(f"\ngravar {name}: {len(data)} B, {nclus_needed} cluster(s)")

    existing = find_entry(root, name)
    if existing:
        idx, n, c, sz = existing
        print(f"  ja existe ({sz} B) — sera substituido")
    if len(free) < nclus_needed:
        raise SystemExit("clusters livres insuficientes")

    short11 = (name.split(".")[0][:6].upper().ljust(6, "_") + "~1").encode("ascii")
    short11 += name.split(".")[-1][:3].upper().ljust(3).encode("ascii")
    ents = build_entries(name, short11, free[0], len(data))
    need = len(ents) // 32
    print(f"  8.3='{short11.decode()}'  {need} entrada(s) de diretorio")

    if not apply_it:
        print("\n--- SIMULACAO. rode de novo com --apply para gravar ---")
        return

    if existing:
        idx, n, c, _sz = existing
        for k in range(n):
            root[idx + k * 32] = 0xE5
        while 2 <= c < 0xFFF8:
            nxt, = struct.unpack_from("<H", fat, c * 2)
            struct.pack_into("<H", fat, c * 2, 0)
            c = nxt

    slot = None
    run = 0
    for j in range(0, len(root), 32):
        if root[j] in (0x00, 0xE5):
            run += 1
            if run == need:
                slot = j - (need - 1) * 32
                break
        else:
            run = 0
    if slot is None:
        raise SystemExit("sem espaco contiguo no diretorio raiz")

    chain = free[:nclus_needed]
    for k, c in enumerate(chain):
        nxt = chain[k + 1] if k + 1 < len(chain) else 0xFFFF
        struct.pack_into("<H", fat, c * 2, nxt)
        blob = data[k * fs.csize:(k + 1) * fs.csize]
        fs.pwrite(fs.cluster_off(c), blob + b"\x00" * (fs.csize - len(blob)))
    fs.write_fat(fat)
    root[slot:slot + len(ents)] = ents
    fs.pwrite(fs.root, bytes(root))
    fs.sync()
    print(f"  gravado nos clusters {chain}")

    fs2 = Fat16(dev, off)
    hit = find_entry(fs2.read_root(), name)
    if not hit:
        raise SystemExit("VERIFICACAO FALHOU: entrada nao relida")
    _i, _n, c, sz = hit
    back = b""
    while 2 <= c < 0xFFF8 and len(back) < sz:
        back += fs2.pread(fs2.cluster_off(c), fs2.csize)
        c, = struct.unpack_from("<H", fs2.read_fat(), c * 2)
    ok = back[:sz] == data
    print(f"\nverificacao: {sz} B relidos, identico = {ok}")


if __name__ == "__main__":
    main()
