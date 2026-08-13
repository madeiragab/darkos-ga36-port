# GA36-MB — hook de boot, instalar em /flash/post-flash.sh
#
# O /init faz `. /flash/post-flash.sh` logo depois de montar /flash
# (linha 666 do initramfs). Valores escritos em /proc/sys sobrevivem ao
# switch_root e valem para o boot inteiro.
#
# Objetivo: fazer o dado chegar ao cartao em ~2 s em vez de ate 30 s, para
# que um corte de energia pelo botao nao leve o save junto.
#
# ATENCAO: este arquivo e *sourced* pelo shell do initramfs. Um erro de
# SINTAXE aqui aborta o boot. Por isso ele contem apenas redirecionamentos
# de echo — sem condicionais, sem substituicao, sem loop. Nao complique.
# Terminadores de linha DEVEM ser LF; um \r torna o caminho invalido.

echo 200 > /proc/sys/vm/dirty_expire_centisecs
echo 100 > /proc/sys/vm/dirty_writeback_centisecs
echo 5 > /proc/sys/vm/dirty_ratio
echo 2 > /proc/sys/vm/dirty_background_ratio
echo deadline > /sys/block/mmcblk0/queue/scheduler
echo "post-flash.sh: writeback ajustado" > /dev/kmsg
