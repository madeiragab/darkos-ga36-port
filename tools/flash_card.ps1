# Grava a recovery img patchada no cartao do console GA36.
# Precisa rodar como Administrador.

$ErrorActionPreference = "Stop"
$IMG = "C:\Users\gabri\OneDrive\Desktop\r36s-a33-recovery.img"

function Fail($m) { Write-Host "`nABORTADO: $m" -ForegroundColor Red; Read-Host "Enter para sair"; exit 1 }

# --- elevacao
$p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Fail "nao esta como Administrador. Feche e abra o PowerShell com 'Executar como administrador'."
}
if (-not (Test-Path $IMG)) { Fail "imagem nao encontrada: $IMG" }
$imgSize = (Get-Item $IMG).Length
Write-Host "imagem : $IMG"
Write-Host "tamanho: $([math]::Round($imgSize/1MB,1)) MB"

# --- identificar o cartao por caracteristicas, NUNCA por numero fixo
$cands = Get-Disk | Where-Object {
    $_.BusType -eq 'USB' -and -not $_.IsSystem -and -not $_.IsBoot -and
    $_.Size -gt 100GB -and $_.Size -lt 130GB
}
if ($cands.Count -eq 0) { Fail "nenhum cartao USB de ~116 GB encontrado. O cartao esta plugado?" }
if ($cands.Count -gt 1) { Fail "achei $($cands.Count) discos USB que batem. Desplugue os outros e rode de novo." }

$disk = $cands[0]
if ($disk.Size -lt $imgSize) { Fail "cartao menor que a imagem." }

Write-Host "`n--- DISCO ALVO ---" -ForegroundColor Yellow
Write-Host "  Numero : $($disk.Number)"
Write-Host "  Nome   : $($disk.FriendlyName)"
Write-Host "  Tamanho: $([math]::Round($disk.Size/1GB,2)) GB"
Write-Host "  Bus    : $($disk.BusType)   Sistema: $($disk.IsSystem)   Boot: $($disk.IsBoot)"
Get-Partition -DiskNumber $disk.Number -ErrorAction SilentlyContinue |
    Select-Object PartitionNumber, DriveLetter, @{n='MB';e={[math]::Round($_.Size/1MB,1)}} |
    Format-Table -AutoSize | Out-String | Write-Host

Write-Host "TODO o conteudo deste disco sera destruido." -ForegroundColor Red
if ((Read-Host "Digite GRAVAR para confirmar") -ne "GRAVAR") { Fail "cancelado pelo usuario." }

# --- offline para liberar escrita crua
Write-Host "`ncolocando disco offline..."
Set-Disk -Number $disk.Number -IsReadOnly $false
Set-Disk -Number $disk.Number -IsOffline $true
Start-Sleep -Seconds 2

$path = "\\.\PhysicalDrive$($disk.Number)"
$CH = 4MB
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
    $in  = [IO.File]::OpenRead($IMG)
    $out = New-Object IO.FileStream($path, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite)
    $buf = New-Object byte[] $CH
    $done = 0
    while ($true) {
        $n = $in.Read($buf, 0, $CH)
        if ($n -le 0) { break }
        # setores de 512 B: completa o ultimo bloco
        if ($n % 512 -ne 0) { $n = [math]::Ceiling($n / 512) * 512 }
        $out.Write($buf, 0, $n)
        $done += $n
        $pct = [math]::Round(100 * $done / $imgSize, 1)
        Write-Progress -Activity "Gravando" -Status "$([math]::Round($done/1MB,1)) / $([math]::Round($imgSize/1MB,1)) MB" -PercentComplete ([math]::Min($pct,100))
    }
    $out.Flush()
} finally {
    if ($out) { $out.Close() }
    if ($in)  { $in.Close() }
}
Write-Progress -Activity "Gravando" -Completed
Write-Host "gravado em $([math]::Round($sw.Elapsed.TotalSeconds,1))s"

# --- verificacao: le de volta e compara hash
Write-Host "`nverificando (lendo de volta)..."
$sha = [Security.Cryptography.SHA256]::Create()
$in  = [IO.File]::OpenRead($IMG)
$chk = New-Object IO.FileStream($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
$b1 = New-Object byte[] $CH; $b2 = New-Object byte[] $CH
$ok = $true; $read = 0
while ($read -lt $imgSize) {
    $want = [math]::Min($CH, $imgSize - $read)
    $want = [int]([math]::Ceiling($want / 512) * 512)
    $n1 = $in.Read($b1, 0, $want); $null = $chk.Read($b2, 0, $want)
    if ($n1 -le 0) { break }
    for ($i = 0; $i -lt $n1; $i++) { if ($b1[$i] -ne $b2[$i]) { $ok = $false; break } }
    if (-not $ok) { break }
    $read += $n1
    Write-Progress -Activity "Verificando" -PercentComplete ([math]::Min([math]::Round(100*$read/$imgSize,1),100))
}
$in.Close(); $chk.Close()
Write-Progress -Activity "Verificando" -Completed

if ($ok) {
    Write-Host "`nOK - imagem gravada e verificada byte a byte." -ForegroundColor Green
    Write-Host "O disco foi deixado OFFLINE de proposito." -ForegroundColor Yellow
    Write-Host "O Windows monta a particao Volumn com o tamanho errado (128 MB em vez de 32 MB)" -ForegroundColor Yellow
    Write-Host "e pode escrever por cima do boot.img. Offline ele nao toca em nada." -ForegroundColor Yellow
    Write-Host "`nRetire o cartao agora, ainda offline, e ponha no console." -ForegroundColor Cyan
} else {
    Write-Host "`nFALHA na verificacao - dados lidos diferem da imagem. Nao use este cartao." -ForegroundColor Red
    Set-Disk -Number $disk.Number -IsOffline $false
}
Read-Host "`nEnter para sair"
