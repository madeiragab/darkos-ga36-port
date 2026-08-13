#!/usr/bin/env python3
r"""
Leitor de squashfs 4.x comprimido com LZO, gzip, xz ou zstd — em Python
puro, sem `unsquashfs` e sem `python-lzo`.

Existe porque o SYSTEM desta placa e squashfs **lzo**, o `python-lzo` nao
compila sem toolchain no Windows, e e dentro dele que estao o handler do
botao de power, os scripts do EmuELEC e o driver do painel jd9366.

O descompressor LZO1X abaixo e uma transcricao direta do algoritmo de
referencia (minilzo / lzo1x_decompress do kernel Linux).

Uso:
    python squashfs_lzo.py IMAGEM OFFSET --ls /
    python squashfs_lzo.py IMAGEM OFFSET --find powerbutton
    python squashfs_lzo.py IMAGEM OFFSET --cat /usr/bin/foo
    python squashfs_lzo.py IMAGEM OFFSET --extract /usr/config DESTINO

Nesta placa: offset 0x7434200 (o arquivo SYSTEM dentro da FAT16 /flash).
Descubra o offset exato com:  python boot_header.py IMAGEM
"""
import os
import struct
import sys

# --------------------------------------------------------------- LZO1X


def lzo1x_decompress(src):
    """LZO1X. Transcricao do lzo1x_decompress de referencia."""
    out = bytearray()
    ip = 0

    def mcopy(dist, n):
        """Copia n bytes de `dist` atras. Sobreposto exige byte a byte:
        com dist < n o trecho a copiar inclui bytes que ainda serao
        escritos, e uma fatia devolveria menos bytes do que o pedido."""
        p = len(out) - dist
        if p < 0:
            raise ValueError("lzo: distancia invalida")
        if dist >= n:
            out.extend(out[p:p + n])
        else:
            for i in range(n):
                out.append(out[p + i])

    L_INIT, L_LOOP, L_FIRST, L_MATCH, L_COPY, L_DONE, L_NEXT = range(7)
    state, t, dist = L_INIT, 0, 0

    while True:
        if state == L_INIT:
            if src[ip] > 17:
                t = src[ip] - 17
                ip += 1
                if t < 4:
                    state = L_NEXT
                    continue
                out += src[ip:ip + t]
                ip += t
                state = L_FIRST
                continue
            state = L_LOOP

        elif state == L_LOOP:
            t = src[ip]
            ip += 1
            if t >= 16:
                state = L_MATCH
                continue
            if t == 0:
                while src[ip] == 0:
                    t += 255
                    ip += 1
                t += 15 + src[ip]
                ip += 1
            t += 3
            out += src[ip:ip + t]
            ip += t
            state = L_FIRST

        elif state == L_FIRST:
            t = src[ip]
            ip += 1
            if t >= 16:
                state = L_MATCH
                continue
            dist = 1 + 0x0800 + (t >> 2) + (src[ip] << 2)
            ip += 1
            mcopy(dist, 3)
            state = L_DONE

        elif state == L_MATCH:
            if t >= 64:
                dist = 1 + ((t >> 2) & 7) + (src[ip] << 3)
                ip += 1
                t = (t >> 5) - 1
                state = L_COPY
            elif t >= 32:
                t &= 31
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 31 + src[ip]
                    ip += 1
                dist = 1 + (src[ip] >> 2) + (src[ip + 1] << 6)
                ip += 2
                state = L_COPY
            elif t >= 16:
                dist = (t & 8) << 11
                t &= 7
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 7 + src[ip]
                    ip += 1
                dist += (src[ip] >> 2) + (src[ip + 1] << 6)
                ip += 2
                if dist == 0:
                    return bytes(out)          # fim do fluxo
                dist += 0x4000
                state = L_COPY
            else:
                dist = 1 + (t >> 2) + (src[ip] << 2)
                ip += 1
                mcopy(dist, 2)
                state = L_DONE

        elif state == L_COPY:
            mcopy(dist, t + 2)
            state = L_DONE

        elif state == L_DONE:
            t = src[ip - 2] & 3
            state = L_LOOP if t == 0 else L_NEXT

        elif state == L_NEXT:
            out += src[ip:ip + t]
            ip += t
            t = src[ip]
            ip += 1
            state = L_MATCH


def decompress(data, comp, want):
    if comp == 1:
        import zlib
        return zlib.decompress(data)
    if comp == 3:
        return lzo1x_decompress(data)
    if comp == 4:
        import lzma
        return lzma.decompress(data, format=lzma.FORMAT_AUTO)
    if comp == 6:
        import zstandard
        return zstandard.ZstdDecompressor().decompress(data, max_output_size=want)
    raise SystemExit(f"compressao {comp} nao suportada")


# ------------------------------------------------------------ squashfs

COMPNAME = {1: "gzip", 2: "lzma", 3: "lzo", 4: "xz", 5: "lz4", 6: "zstd"}
ALIGN = 512


class SquashFS:
    def __init__(self, path, off):
        self.raw = path.startswith("\\\\.\\") or path.startswith("/dev/")
        self.f = open(path, "rb", buffering=0 if self.raw else -1)
        self.off = off
        sb = self.pread(off, 96)
        if sb[:4] != b"hsqs":
            raise SystemExit(f"sem magic squashfs em 0x{off:x}")
        (self.inodes, self.mkfs, self.block_size, self.fragments) = struct.unpack_from("<IIII", sb, 4)
        (self.comp, self.block_log, self.flags, self.no_ids,
         self.major, self.minor) = struct.unpack_from("<HHHHHH", sb, 20)
        (self.root_ref, self.bytes_used, self.id_start, self.xattr_start,
         self.inode_start, self.dir_start, self.frag_start,
         self.lookup_start) = struct.unpack_from("<QQQQQQQQ", sb, 32)
        if self.major != 4:
            raise SystemExit(f"squashfs versao {self.major}, so suporto 4")
        self._meta = {}
        self.errors = []

    def pread(self, o, n):
        if not self.raw:
            self.f.seek(o)
            return self.f.read(n)
        s = o - (o % ALIGN)
        e = ((o + n + ALIGN - 1) // ALIGN) * ALIGN
        self.f.seek(s)
        buf = self.f.read(e - s)
        return buf[o - s:o - s + n]

    def meta_block(self, pos):
        """Le um bloco de metadados; devolve (dados, proxima_posicao)."""
        if pos in self._meta:
            return self._meta[pos]
        if not (0 <= pos < self.bytes_used):
            raise ValueError(f"bloco de metadados fora da imagem: 0x{pos:x}")
        raw2 = self.pread(self.off + pos, 2)
        if len(raw2) < 2:
            raise ValueError(f"leitura curta em 0x{pos:x}")
        hdr, = struct.unpack("<H", raw2)
        size = hdr & 0x7FFF
        comp = not (hdr & 0x8000)
        raw = self.pread(self.off + pos + 2, size)
        data = decompress(raw, self.comp, 8192) if comp else raw
        self._meta[pos] = (data, pos + 2 + size)
        return self._meta[pos]

    def meta_read(self, start, offset, count):
        """Le `count` bytes a partir de (bloco start, deslocamento offset).

        O deslocamento pode ultrapassar o bloco: inodes e diretorios
        atravessam blocos de metadados livremente. Normaliza antes de ler.
        """
        pos = start
        guard = 0
        while True:
            data, nxt = self.meta_block(pos)
            if offset < len(data) or not data:
                break
            offset -= len(data)
            pos = nxt
            guard += 1
            if guard > 4096:
                raise SystemExit("meta_read: cadeia de blocos sem fim")
        out = b""
        while len(out) < count:
            data, nxt = self.meta_block(pos)
            if not data:
                break
            out += data[offset:]
            offset = 0
            pos = nxt
        return out[:count], start, pos

    # ---- inodes
    def read_inode(self, ref):
        blk = (ref >> 16) & 0xFFFFFFFF
        off = ref & 0xFFFF
        base = self.inode_start + blk
        hdr, _p, _n = self.meta_read(base, off, 16)
        itype, mode, uid, gid, mtime, ino = struct.unpack("<HHHHII", hdr)
        node = {"type": itype, "mode": mode, "ino": ino, "mtime": mtime}
        if itype == 1:                                   # dir
            b, _p, _n = self.meta_read(base, off + 16, 16)
            sblk, nlink, fsize, soff, parent = struct.unpack("<IIHHI", b)
            node.update(start=sblk, size=fsize, offset=soff)
        elif itype == 8:                                 # ldir
            b, _p, _n = self.meta_read(base, off + 16, 24)
            (nlink, fsize, sblk, parent,
             icount, soff, xattr) = struct.unpack("<IIIIHHI", b)
            node.update(start=sblk, size=fsize, offset=soff)
        elif itype == 2:                                 # reg
            b, _p, _n = self.meta_read(base, off + 16, 16)
            sblk, frag, foff, fsize = struct.unpack("<IIII", b)
            nblk = (fsize // self.block_size) if frag != 0xFFFFFFFF else \
                   ((fsize + self.block_size - 1) // self.block_size)
            bs, _p, _n = self.meta_read(base, off + 32, nblk * 4)
            node.update(start=sblk, frag=frag, foff=foff, size=fsize,
                        blocks=list(struct.unpack(f"<{nblk}I", bs)))
        elif itype == 9:                                 # lreg
            b, _p, _n = self.meta_read(base, off + 16, 40)
            sblk, fsize, sparse, nlink, frag, foff, xattr = struct.unpack("<QQQIIII", b)
            nblk = (fsize // self.block_size) if frag != 0xFFFFFFFF else \
                   ((fsize + self.block_size - 1) // self.block_size)
            bs, _p, _n = self.meta_read(base, off + 56, nblk * 4)
            node.update(start=sblk, frag=frag, foff=foff, size=fsize,
                        blocks=list(struct.unpack(f"<{nblk}I", bs)))
        elif itype in (3, 10):                           # symlink
            b, _p, _n = self.meta_read(base, off + 16, 8)
            nlink, tsize = struct.unpack("<II", b)
            tgt, _p, _n = self.meta_read(base, off + 24, tsize)
            node.update(target=tgt.decode("utf-8", "replace"))
        return node

    def listdir(self, node):
        if node["type"] not in (1, 8) or node["size"] <= 3:
            return []
        raw, _p, _n = self.meta_read(self.dir_start + node["start"],
                                     node["offset"], node["size"] - 3)
        out, p = [], 0
        while p + 12 <= len(raw):
            count, sblk, ino_base = struct.unpack_from("<III", raw, p)
            p += 12
            for _ in range(count + 1):
                if p + 8 > len(raw):
                    break
                eoff, ioff, etype, nsize = struct.unpack_from("<HhHH", raw, p)
                p += 8
                name = raw[p:p + nsize + 1].decode("utf-8", "replace")
                p += nsize + 1
                out.append((name, (sblk << 16) | eoff, etype))
        return out

    def resolve(self, path):
        node = self.read_inode(self.root_ref)
        for part in [x for x in path.strip("/").split("/") if x]:
            hit = [r for n, r, _t in self.listdir(node) if n == part]
            if not hit:
                return None
            node = self.read_inode(hit[0])
        return node

    def frag_entry(self, idx):
        nblocks = (self.fragments * 16 + 8191) // 8192
        tbl = self.pread(self.off + self.frag_start, nblocks * 8)
        starts = struct.unpack(f"<{nblocks}Q", tbl)
        per = 8192 // 16
        blk, within = divmod(idx, per)
        data, _n = self.meta_block(starts[blk])
        return struct.unpack_from("<QII", data, within * 16)

    def cat(self, node):
        if node["type"] not in (2, 9):
            return None
        out = b""
        pos = self.off + node["start"]
        for bs in node["blocks"]:
            size = bs & 0xFFFFFF
            if size == 0:
                out += b"\x00" * self.block_size
                continue
            raw = self.pread(pos, size)
            out += raw if (bs & 0x1000000) else decompress(raw, self.comp, self.block_size)
            pos += size
        if node["frag"] != 0xFFFFFFFF:
            fstart, fsize, _u = self.frag_entry(node["frag"])
            raw = self.pread(self.off + fstart, fsize & 0xFFFFFF)
            fdata = raw if (fsize & 0x1000000) else decompress(raw, self.comp, self.block_size)
            out += fdata[node["foff"]:node["foff"] + (node["size"] - len(out))]
        return out[:node["size"]]

    def walk(self, path="/", node=None, depth=0, maxdepth=99):
        if node is None:
            node = self.resolve(path)
        if node is None or depth > maxdepth:
            return
        try:
            entries = sorted(self.listdir(node))
        except Exception as e:
            self.errors.append((path, f"listdir: {e}"))
            return
        for name, ref, etype in entries:
            full = (path.rstrip("/") + "/" + name)
            try:
                child = self.read_inode(ref)
            except Exception as e:
                self.errors.append((full, f"read_inode: {e}"))
                continue
            yield full, child
            if child["type"] in (1, 8):
                yield from self.walk(full, child, depth + 1, maxdepth)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    img, off = sys.argv[1], int(sys.argv[2], 0)
    fs = SquashFS(img, off)
    import datetime
    print(f"squashfs {fs.major}.{fs.minor}  comp={COMPNAME.get(fs.comp, fs.comp)}  "
          f"bloco={fs.block_size}  inodes={fs.inodes}  frags={fs.fragments}")
    print(f"build={datetime.datetime.fromtimestamp(fs.mkfs)}  "
          f"bytes_used={fs.bytes_used/1024/1024:.2f} MB\n")

    if "--ls" in sys.argv:
        p = sys.argv[sys.argv.index("--ls") + 1]
        node = fs.resolve(p)
        if not node:
            raise SystemExit(f"{p} nao encontrado")
        for name, ref, etype in sorted(fs.listdir(node)):
            c = fs.read_inode(ref)
            kind = {1: "d", 8: "d", 2: "-", 9: "-", 3: "l", 10: "l"}.get(c["type"], "?")
            extra = " -> " + c["target"] if "target" in c else ""
            print(f"  {kind} {oct(c['mode'] & 0o7777):>6} {c.get('size', 0):>10}  {name}{extra}")

    elif "--find" in sys.argv:
        pat = sys.argv[sys.argv.index("--find") + 1].lower()
        n = 0
        for full, node in fs.walk("/"):
            if pat in full.lower():
                kind = {1: "d", 8: "d", 2: "-", 9: "-", 3: "l", 10: "l"}.get(node["type"], "?")
                print(f"  {kind} {node.get('size', 0):>9}  {full}")
                n += 1
                if n > 300:
                    print("  ..."); break

    elif "--cat" in sys.argv:
        p = sys.argv[sys.argv.index("--cat") + 1]
        node = fs.resolve(p)
        if not node:
            raise SystemExit(f"{p} nao encontrado")
        sys.stdout.write(fs.cat(node).decode("utf-8", "replace"))

    elif "--extract" in sys.argv:
        i = sys.argv.index("--extract")
        src, dst = sys.argv[i + 1], sys.argv[i + 2]
        root = fs.resolve(src)
        if root is None:
            raise SystemExit(f"{src} nao encontrado")
        n = 0
        for full, node in fs.walk(src, root):
            rel = full[len(src.rstrip("/")):].lstrip("/")
            target = os.path.join(dst, rel.replace("/", os.sep))
            if node["type"] in (1, 8):
                os.makedirs(target, exist_ok=True)
            elif node["type"] in (2, 9):
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as fh:
                    fh.write(fs.cat(node))
                n += 1
        print(f"  {n} arquivos extraidos para {dst}")


if __name__ == "__main__":
    main()
