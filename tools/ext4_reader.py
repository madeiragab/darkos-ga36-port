#!/usr/bin/env python3
"""
Leitor ext4 somente leitura, direto de uma imagem crua ou dispositivo.

Nao monta nada, nao precisa de Linux, nao precisa de root (exceto para ler
um dispositivo fisico no Windows, que exige Administrador).

Uso:
    python ext4_reader.py IMAGEM OFFSET ls:/            # lista a raiz
    python ext4_reader.py IMAGEM OFFSET cat:/etc/fstab  # imprime um arquivo
    python ext4_reader.py IMAGEM OFFSET ls:/.config cat:/.config/EE_VERSION

OFFSET e o byte onde a particao comeca (aceita 0x...).
Na imagem do GA36-MB, /storage esta em 0x37400000.

Read-only ext4 walker for raw images. See docs/image-autopsy.md.
"""
import struct
import sys

FTYPE = {1: "-", 2: "d", 3: "c", 4: "b", 5: "p", 6: "s", 7: "l"}


ALIGN = 512          # dispositivos brutos exigem I/O alinhado ao setor


class Ext4:
    def __init__(self, path, part_off):
        # dispositivo bruto (\\.\PhysicalDriveN, /dev/sdX) precisa de I/O
        # sem buffer e alinhado; arquivo comum aceita qualquer coisa
        self.raw = path.startswith("\\\\.\\") or path.startswith("/dev/")
        self.f = open(path, "rb", buffering=0 if self.raw else -1)
        self.po = part_off
        sb = self.pread(part_off + 1024, 1024)
        magic, = struct.unpack("<H", sb[0x38:0x3A])
        if magic != 0xEF53:
            raise SystemExit(f"sem magic ext4 em 0x{part_off:x} (achei 0x{magic:04x})")
        self.inodes_count, self.blocks_count = struct.unpack("<II", sb[0:8])
        self.first_data_block, = struct.unpack("<I", sb[20:24])
        log_bs, = struct.unpack("<I", sb[24:28])
        self.bs = 1024 << log_bs
        self.blocks_per_group, = struct.unpack("<I", sb[32:36])
        self.inodes_per_group, = struct.unpack("<I", sb[40:44])
        self.inode_size, = struct.unpack("<H", sb[0x58:0x5A])
        self.feat_incompat, = struct.unpack("<I", sb[0x60:0x64])
        self.desc_size, = struct.unpack("<H", sb[0xFE:0x100])
        if not (self.feat_incompat & 0x80):          # sem 64BIT
            self.desc_size = 32
        self.desc_size = self.desc_size or 32
        self.label = sb[0x78:0x88].split(b"\0")[0].decode("ascii", "replace")
        self.gdt_block = self.first_data_block + 1

    def pread(self, off, n):
        if not self.raw:
            self.f.seek(off)
            return self.f.read(n)
        # arredonda o inicio para baixo e o fim para cima, depois fatia
        start = off - (off % ALIGN)
        end = ((off + n + ALIGN - 1) // ALIGN) * ALIGN
        self.f.seek(start)
        buf = self.f.read(end - start)
        rel = off - start
        return buf[rel:rel + n]

    def block(self, n, count=1):
        return self.pread(self.po + n * self.bs, self.bs * count)

    def inode_table(self, group):
        off = self.po + self.gdt_block * self.bs + group * self.desc_size
        d = self.pread(off, self.desc_size)
        lo, = struct.unpack("<I", d[8:12])
        hi = struct.unpack("<I", d[40:44])[0] if self.desc_size >= 64 else 0
        return (hi << 32) | lo

    def inode(self, ino):
        g, i = divmod(ino - 1, self.inodes_per_group)
        off = self.po + self.inode_table(g) * self.bs + i * self.inode_size
        return self.pread(off, self.inode_size)

    def extents(self, iblock_bytes):
        """Retorna [(bloco_logico, bloco_fisico, tamanho)]."""
        out = []

        def walk(buf):
            magic, entries, _mx, depth, _gen = struct.unpack("<HHHHI", buf[:12])
            if magic != 0xF30A:
                return
            for k in range(entries):
                e = buf[12 + k * 12: 24 + k * 12]
                if depth == 0:
                    blk, ln, hi, lo = struct.unpack("<IHHI", e)
                    if ln > 32768:                    # extent nao inicializado
                        ln -= 32768
                    out.append((blk, (hi << 32) | lo, ln))
                else:
                    _blk, lo, hi, _u = struct.unpack("<IIHH", e)
                    walk(self.block((hi << 32) | lo))

        walk(iblock_bytes)
        return out

    def read_inode_data(self, ino):
        ind = self.inode(ino)
        size_lo, = struct.unpack("<I", ind[4:8])
        size_hi, = struct.unpack("<I", ind[0x6C:0x70])
        size = (size_hi << 32) | size_lo
        flags, = struct.unpack("<I", ind[0x20:0x24])
        iblock = ind[0x28:0x28 + 60]
        if flags & 0x10000000:                        # INLINE_DATA
            return ind[0x28:0x28 + min(size, 60)]
        data = bytearray(size)
        if flags & 0x80000:                           # EXTENTS
            for lblk, pblk, ln in self.extents(iblock):
                chunk = self.block(pblk, ln)
                s = lblk * self.bs
                data[s:s + len(chunk)] = chunk[:max(0, size - s)]
        else:                                         # mapa de blocos classico
            ptrs = struct.unpack("<15I", iblock)
            blocks = list(ptrs[:12])
            ppb = self.bs // 4
            if ptrs[12]:
                blocks += [b for b in struct.unpack(f"<{ppb}I", self.block(ptrs[12])) if b]
            if ptrs[13]:
                for b1 in struct.unpack(f"<{ppb}I", self.block(ptrs[13])):
                    if b1:
                        blocks += [b for b in struct.unpack(f"<{ppb}I", self.block(b1)) if b]
            for i, b in enumerate(blocks):
                if not b or i * self.bs >= size:
                    continue
                data[i * self.bs:(i + 1) * self.bs] = self.block(b)[:max(0, size - i * self.bs)]
        return bytes(data[:size])

    def mode(self, ino):
        return struct.unpack("<H", self.inode(ino)[0:2])[0]

    def listdir(self, ino):
        raw = self.read_inode_data(ino)
        out, p = [], 0
        while p < len(raw) - 8:
            child, rec_len, name_len, ftype = struct.unpack("<IHBB", raw[p:p + 8])
            if rec_len < 8:
                break
            name = raw[p + 8:p + 8 + name_len].decode("utf-8", "replace")
            if child and name not in (".", ".."):
                out.append((name, child, ftype))
            p += rec_len
        return out

    def resolve(self, path):
        ino = 2
        for part in [p for p in path.strip("/").split("/") if p]:
            hit = [c for n, c, _t in self.listdir(ino) if n == part]
            if not hit:
                return None
            ino = hit[0]
        return ino

    def cat(self, path):
        ino = self.resolve(path)
        return self.read_inode_data(ino) if ino else None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    img = sys.argv[1]
    off = int(sys.argv[2], 0)
    fs = Ext4(img, off)
    print(f"ext4 @0x{off:x}  bs={fs.bs}  blocos={fs.blocks_count} "
          f"({fs.blocks_count * fs.bs / 1024 / 1024:.0f} MB)  inodes={fs.inodes_count} "
          f"isize={fs.inode_size} desc={fs.desc_size} label={fs.label!r}")

    for cmd in sys.argv[3:]:
        op, _, path = cmd.partition(":")
        print(f"\n===== {op} {path}")
        try:
            if op == "ls":
                ino = fs.resolve(path)
                if not ino:
                    print("  (nao encontrado)")
                    continue
                for name, child, t in sorted(fs.listdir(ino)):
                    m = fs.mode(child)
                    sz = struct.unpack("<I", fs.inode(child)[4:8])[0]
                    tag = FTYPE.get(t, "?")
                    link = ""
                    if tag == "l":
                        link = " -> " + fs.read_inode_data(child).decode("utf-8", "replace")
                    print(f"  {tag} {oct(m & 0o7777):>6} {sz:>10}  {name}{link}")
            elif op == "cat":
                d = fs.cat(path)
                print(d.decode("utf-8", "replace") if d is not None else "  (nao encontrado)")
            else:
                print(f"  operacao desconhecida: {op}")
        except Exception as e:
            print(f"  ERRO: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
