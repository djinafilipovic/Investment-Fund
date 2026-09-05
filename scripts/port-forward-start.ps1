# ---------------------------------------------------------------------------
# Pokrece kubectl port-forward za sva cetiri NodePort servisa u pozadinskim
# poslovima (PowerShell background jobs), tako da localhost:30001-30004
# rade cak i ako Docker Desktop Kubernetes ne prosledjuje NodePort automatski.
#
#   .\scripts\port-forward-start.ps1
#   .\scripts\port-forward-stop.ps1     # zaustavljanje
#
# Napomena: poslovi rade dok je ovaj PowerShell prozor otvoren.
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$Services = @(
    @{ Name = "authentication"; Local = 30001; Remote = 5000 },
    @{ Name = "employee";       Local = 30002; Remote = 5000 },
    @{ Name = "director";       Local = 30003; Remote = 5000 },
    @{ Name = "ganache";        Local = 30004; Remote = 8545 }
)

# ukloni eventualne prethodne poslove sa istim imenima
Get-Job -Name "portforward-*" -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job

foreach ($svc in $Services) {
    Start-Job -Name "portforward-$($svc.Name)" -ScriptBlock {
        param($Name, $Local, $Remote)
        kubectl port-forward "svc/$Name" "${Local}:${Remote}"
    } -ArgumentList $svc.Name, $svc.Local, $svc.Remote | Out-Null
    Write-Host "==> $($svc.Name): localhost:$($svc.Local) -> $($svc.Remote)"
}

Start-Sleep -Seconds 2

$failed = Get-Job -Name "portforward-*" | Where-Object { $_.State -eq "Failed" }
if ($failed) {
    Write-Host ""
    Write-Host "GRESKA - neki poslovi nisu uspeli:" -ForegroundColor Red
    $failed | ForEach-Object {
        Write-Host "  $($_.Name):"
        Receive-Job -Job $_ -ErrorAction SilentlyContinue
    }
    exit 1
}

Write-Host ""
Write-Host "Svi tuneli su aktivni. Za zaustavljanje: .\scripts\port-forward-stop.ps1"
