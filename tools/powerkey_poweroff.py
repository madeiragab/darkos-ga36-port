#!/usr/bin/env python3
r"""
Faz o toque no botao de power DESLIGAR o console (em vez de suspender),
gravando tudo antes.

Como funciona o botao de fabrica:

  udt_pwr.service  ->  /usr/bin/udt_pwr_events.sh
      le /sys/devices/platform/micro_gamepad/power_key em loop e, no toque:
          backlight off; amixer mute; sync; systemctl suspend

Esse script esta no squashfs somente leitura e nao pode ser editado, e nao
existe /etc/systemd/system para sobrescrever a unit.

O caminho aberto e outro. /etc/profile.d/99-emuelec.conf termina com:

    # reads other config files from /storage/.config/profile.d
      for config in /storage/.config/profile.d/*; do
        if [ -f "${config}" ] ; then . ${config} ; fi
      done

Ou seja, tudo em /storage/.config/profile.d — que fica no ext4 gravavel —
e carregado dentro do MESMO shell do udt_pwr_events.sh, que faz
`. /etc/profile` no inicio. Uma funcao definida ali tem precedencia sobre o
binario de mesmo nome.

Esta ferramenta acrescenta ao arquivo ja existente
`99-emuelec_functions.conf` (um stub vazio que o proprio EmuELEC oferece
para isso) uma funcao `systemctl` que troca **apenas** o verbo `suspend`
por `poweroff`. Qualquer outro verbo passa direto via `command`.

Nada de inode novo, nada de alocacao: o conteudo cresce dentro do bloco ja
alocado e o `i_size` e ajustado.

Uso (imagem):
    python powerkey_poweroff.py imagem.img 0x37400000
    python powerkey_poweroff.py imagem.img 0x37400000 --apply

Uso (cartao, PowerShell como Administrador):
    python powerkey_poweroff.py \\.\PhysicalDrive1 0x37400000 --apply

Reverter:
    python powerkey_poweroff.py ... --revert --apply
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ext4_reader import Ext4, ALIGN

CFG = "/.config/profile.d/99-emuelec_functions.conf"
MARK = "# >>> ga36-port: botao de power desliga em vez de suspender >>>"
END = "# <<< ga36-port <<<"

BLOCK = f"""
{MARK}
# udt_pwr_events.sh (servico udt_pwr.service) roda dentro de um shell que
# carregou este arquivo via /etc/profile. No toque do botao ele executa
# backlight off, mute, sync e entao `systemctl suspend`.
#
# A funcao abaixo intercepta somente o verbo `suspend`. O `sync` do script
# original ja rodou antes, e o `poweroff` do systemd ainda para os servicos
# de forma limpa: o RetroArch recebe SIGTERM e grava a SRAM, e as particoes
# sao desmontadas.
systemctl() {{
  if [ "$1" = "suspend" ]; then
    command systemctl poweroff
  else
    command systemctl "$@"
  fi
}}
{END}
"""


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    dev, off = sys.argv[1], int(sys.argv[2], 0)
    apply_it = "--apply" in sys.argv
    revert = "--revert" in sys.argv

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
    present = MARK in text
    print(f"{CFG}: {size} B, folga {alloc - size}, bloco ja presente: {present}")

    if revert:
        if not present:
            raise SystemExit("bloco nao esta presente — nada a reverter")
        i, j = text.index(MARK), text.index(END) + len(END)
        # remove tambem a linha em branco que precede o marcador
        start = text.rfind("\n", 0, i)
        data = (text[:start] + text[j:]).rstrip() + "\n"
        print("  removendo o bloco")
    else:
        if present:
            raise SystemExit("ja aplicado — nada a fazer")
        data = text.rstrip() + "\n" + BLOCK
        print("  acrescentando:\n")
        print(BLOCK)
    data = data.encode("latin-1")

    print(f"  tamanho {size} -> {len(data)} ({len(data)-size:+d})")
    if len(data) > alloc:
        raise SystemExit(f"nao cabe: {len(data)} > {alloc}")
    if not apply_it:
        print("--- SIMULACAO. rode de novo com --apply para gravar ---")
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
    print(f"\nverificacao: {len(back)} B relidos, identico = {back == data}")
    if not revert:
        print("\nA partir do proximo boot, um toque no botao desliga o console.")
        print("Segurar continua cortando na PMIC — isso e hardware.")
        print("Atencao: a opcao 'suspend' do menu do EmulationStation tambem")
        print("passa a desligar, porque ela chama o mesmo verbo.")


if __name__ == "__main__":
    main()
