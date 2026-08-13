#!/usr/bin/env python3
r"""
Corrige a particao 1 (ROMs) do cartao: reescreve a entrada da MBR para
ocupar o cartao inteiro e cria um FAT32 valido nela.

Necessario porque a imagem de recovery distribuida vem truncada — declara
5,42 MB na MBR contra 48 779 MB no BPB — e porque o Windows nao formata
FAT32 acima de 32 GB com as ferramentas nativas. Ver docs/storage.md.

Tambem corrige o erro de um setor: a MBR aponta LBA 4956161 enquanto o
boot sector real esta em 4956160, que e o valor alinhado a 2048.

Rode num PowerShell ABERTO COMO ADMINISTRADOR:
    python fix_rom_partition.py --apply
Sem --apply, so simula.
"""
import ctypes
import json
import os
import random
import struct
import subprocess
import sys
import time
from ctypes import wintypes

SECTOR       = 512
EXPECT_START = 4956161      # valor errado atual (off-by-one do fabricante)
NEW_START    = 4956160      # alinhado a 2048
SEC_PER_CLUS = 64           # 32 KB
RESERVED     = 32
NUM_FATS     = 2
LABEL        = b"EEROMS     "

GENERIC_READ  = 0x80000000
GENERIC_WRITE = 0x40000000
SHARE_RW      = 0x00000003
OPEN_EXISTING = 3
FSCTL_LOCK_VOLUME            = 0x00090018
FSCTL_DISMOUNT_VOLUME        = 0x00090020
FSCTL_ALLOW_EXTENDED_DASD_IO = 0x00090083
IOCTL_DISK_UPDATE_PROPERTIES = 0x00070140
INVALID = ctypes.c_void_p(-1).value

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
k32.CreateFileW.restype = wintypes.HANDLE
k32.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
k32.DeviceIoControl.restype = wintypes.BOOL
k32.CloseHandle.argtypes = [wintypes.HANDLE]


def ps(cmd):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"powershell falhou: {r.stderr.strip()}")
    return r.stdout.strip()


def devio(h, code):
    br = wintypes.DWORD()
    return bool(k32.DeviceIoControl(h, code, None, 0, None, 0, ctypes.byref(br), None))


def lock_volumes(letters):
    """Trava e desmonta cada volume. Handles devem ficar abertos durante a escrita."""
    handles = []
    for L in letters:
        h = k32.CreateFileW(f"\\\\.\\{L}:", GENERIC_READ | GENERIC_WRITE,
                            SHARE_RW, None, OPEN_EXISTING, 0, None)
        if h == INVALID:
            print(f"  aviso: nao consegui abrir {L}: (erro {ctypes.get_last_error()})")
            continue
        locked = devio(h, FSCTL_LOCK_VOLUME)
        dismounted = devio(h, FSCTL_DISMOUNT_VOLUME)
        print(f"  {L}: lock={'ok' if locked else 'falhou'} "
              f"dismount={'ok' if dismounted else 'falhou'}")
        handles.append(h)
    return handles


def find_disk():
    out = ps("Get-Disk | Where-Object { $_.BusType -eq 'USB' -and -not $_.IsSystem "
             "-and -not $_.IsBoot -and $_.Size -gt 100GB -and $_.Size -lt 130GB } | "
             "Select-Object Number,Size,FriendlyName | ConvertTo-Json -Compress")
    if not out:
        raise SystemExit("nenhum cartao USB de ~116 GB encontrado. Esta plugado?")
    d = json.loads(out)
    if isinstance(d, list):
        raise SystemExit(f"achei {len(d)} discos candidatos. Desplugue os outros.")
    return d["Number"], int(d["Size"]), d["FriendlyName"]


def disk_letters(num):
    out = ps(f"Get-Partition -DiskNumber {num} | Where-Object DriveLetter | "
             "Select-Object -ExpandProperty DriveLetter")
    return [x.strip() for x in out.splitlines() if x.strip()]


def fat32_geometry(total_sectors):
    """Formula do fatgen103 da Microsoft."""
    t1 = total_sectors - RESERVED
    t2 = (256 * SEC_PER_CLUS + NUM_FATS) // 2
    fat_sz = (t1 + t2 - 1) // t2
    data_start = RESERVED + NUM_FATS * fat_sz
    clusters = (total_sectors - data_start) // SEC_PER_CLUS
    need = ((clusters + 2) * 4 + SECTOR - 1) // SECTOR
    assert need <= fat_sz, (need, fat_sz)
    assert 65525 < clusters < 0x0FFFFFF5, clusters
    return fat_sz, data_start, clusters


def build_boot_sector(total_sectors, fat_sz, vol_id):
    b = bytearray(SECTOR)
    b[0:3] = b"\xEB\x58\x90"
    b[3:11] = b"MSWIN4.1"
    struct.pack_into("<HBHBHHBHHHII", b, 11,
                     SECTOR, SEC_PER_CLUS, RESERVED, NUM_FATS, 0, 0,
                     0xF8, 0, 63, 255, 0, total_sectors)
    struct.pack_into("<IHHIHH", b, 36, fat_sz, 0, 0, 2, 1, 6)
    b[64] = 0x80
    b[66] = 0x29
    struct.pack_into("<I", b, 67, vol_id)
    b[71:82] = LABEL
    b[82:90] = b"FAT32   "
    b[510:512] = b"\x55\xAA"
    return bytes(b)


def build_fsinfo(free_clusters):
    b = bytearray(SECTOR)
    b[0:4] = b"RRaA"
    b[484:488] = b"rrAa"
    struct.pack_into("<II", b, 488, free_clusters, 3)
    b[508:512] = b"\x00\x00\x55\xAA"
    return bytes(b)


def write_fat32(f, base, new_size, fat_sz, data_start, clusters, vol_id):
    f.seek(base)
    f.write(build_boot_sector(new_size, fat_sz, vol_id))
    f.write(build_fsinfo(clusters - 1))
    f.write(b"\x00" * (SECTOR * 4))
    f.seek(base + 6 * SECTOR)
    f.write(build_boot_sector(new_size, fat_sz, vol_id))
    f.write(build_fsinfo(clusters - 1))

    fat0 = bytearray(SECTOR)
    struct.pack_into("<III", fat0, 0, 0x0FFFFFF8, 0xFFFFFFFF, 0x0FFFFFFF)
    zeros = b"\x00" * (SECTOR * 256)
    for i in range(NUM_FATS):
        f.seek(base + (RESERVED + i * fat_sz) * SECTOR)
        f.write(bytes(fat0))
        left = fat_sz - 1
        while left:
            n = min(left, 256)
            f.write(zeros[:n * SECTOR])
            left -= n
        print(f"  FAT{i+1} gravada ({fat_sz} setores)")

    root = bytearray(SECTOR * SEC_PER_CLUS)
    root[0:11] = LABEL
    root[11] = 0x08
    f.seek(base + data_start * SECTOR)
    f.write(bytes(root))


def main():
    try:
        admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        admin = 0
    if not admin:
        raise SystemExit(
            "\n*** Este script precisa de ADMINISTRADOR. ***\n"
            "Menu Iniciar -> 'powershell' -> botao direito ->\n"
            "'Executar como administrador'. Depois cole o comando de novo.\n")

    apply = "--apply" in sys.argv
    num, size, name = find_disk()
    total_disk_sectors = size // SECTOR
    new_size = total_disk_sectors - NEW_START
    fat_sz, data_start, clusters = fat32_geometry(new_size)

    print(f"disco  : {num}  {name}  {size/1024**3:.2f} GB  ({total_disk_sectors} setores)")
    print(f"p1 novo: inicio LBA {NEW_START}, {new_size} setores = {new_size*SECTOR/1024**3:.2f} GB")
    print(f"FAT32  : fat_size={fat_sz} setores, data_start={data_start}, clusters={clusters}")

    path = rf"\\.\PhysicalDrive{num}"
    with open(path, "rb", buffering=0) as f:
        mbr = f.read(SECTOR)
    if mbr[510:512] != b"\x55\xAA":
        raise SystemExit("MBR sem assinatura 0x55AA.")

    e = mbr[446:462]
    cur_start, cur_cnt = struct.unpack("<II", e[8:16])
    print(f"\np1 atual: tipo=0x{e[4]:02x} inicio={cur_start} setores={cur_cnt} "
          f"({cur_cnt*SECTOR/1024**2:.2f} MB)")
    zeroed = e == b"\x00" * 16
    if zeroed:
        print("  entrada 1 esta zerada — retomando execucao interrompida")
    elif cur_start != EXPECT_START:
        raise SystemExit(f"inicio inesperado ({cur_start}). Abortado.")
    elif cur_cnt > 100000:
        raise SystemExit(f"p1 ja parece corrigida ({cur_cnt} setores). Abortado.")

    new_entry = bytearray(16)
    new_entry[1:4] = b"\xFE\xFF\xFF"
    new_entry[4] = 0x0C
    new_entry[5:8] = b"\xFE\xFF\xFF"
    struct.pack_into("<II", new_entry, 8, NEW_START, new_size)
    new_mbr = bytearray(mbr)
    new_mbr[446:462] = new_entry

    if not apply:
        print("\n--- SIMULACAO. rode de novo com --apply para gravar ---")
        return

    letters = disk_letters(num)
    print(f"\ntravando e desmontando volumes: {letters}")
    handles = lock_volumes(letters)

    vol_id = random.getrandbits(32)
    base = NEW_START * SECTOR
    hdisk = None
    try:
        hdisk = k32.CreateFileW(path, GENERIC_READ | GENERIC_WRITE, SHARE_RW,
                                None, OPEN_EXISTING, 0, None)
        if hdisk != INVALID:
            devio(hdisk, FSCTL_ALLOW_EXTENDED_DASD_IO)

        # O Windows bloqueia escrita em setores que pertencem a uma particao
        # que ele conhece, mesmo sem letra atribuida — e sem letra nao da para
        # travar/desmontar o volume. Por isso a gravacao e em tres fases:
        # apaga a entrada da MBR, faz o Windows esquecer a particao, grava o
        # filesystem, e so entao escreve a entrada definitiva.
        with open(path, "r+b", buffering=0) as f:
            if not zeroed:
                blank = bytearray(mbr)
                blank[446:462] = b"\x00" * 16
                f.seek(0)
                f.write(bytes(blank))
                f.flush()
                os.fsync(f.fileno())
                if hdisk != INVALID:
                    devio(hdisk, IOCTL_DISK_UPDATE_PROPERTIES)
                time.sleep(2)
                print("  fase 1: entrada 1 da MBR apagada, particao liberada")

            write_fat32(f, base, new_size, fat_sz, data_start, clusters, vol_id)
            f.flush()
            os.fsync(f.fileno())
            print("  fase 2: FAT32 gravado")

            f.seek(0)
            f.write(bytes(new_mbr))
            f.flush()
            os.fsync(f.fileno())
            print("  fase 3: entrada 1 da MBR reescrita")

        if hdisk != INVALID:
            devio(hdisk, IOCTL_DISK_UPDATE_PROPERTIES)
    finally:
        if hdisk and hdisk != INVALID:
            k32.CloseHandle(hdisk)
        for h in handles:
            k32.CloseHandle(h)

    with open(path, "rb", buffering=0) as f:
        chk = f.read(SECTOR)
        s, c = struct.unpack("<II", chk[446+8:446+16])
        f.seek(base)
        bs = f.read(SECTOR)
    print(f"\nverificacao MBR : inicio={s} setores={c}  ok={s == NEW_START and c == new_size}")
    print(f"verificacao FAT : {bs[82:90]!r} label={bs[71:82]!r} sig={bs[510:512].hex()}")
    print("\nPronto. Retire e replugue o cartao para o Windows remontar.")
    print("Lembrete: NAO copie nada para o D: (Volumn).")


if __name__ == "__main__":
    main()
