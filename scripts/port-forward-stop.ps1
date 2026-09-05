# Zaustavlja port-forward poslove pokrenute skriptom port-forward-start.ps1.
#   .\scripts\port-forward-stop.ps1

$jobs = Get-Job -Name "portforward-*" -ErrorAction SilentlyContinue

if (-not $jobs) {
    Write-Host "Nema aktivnih port-forward poslova."
    exit 0
}

$jobs | Stop-Job -PassThru | Remove-Job
Write-Host "Port-forward poslovi zaustavljeni."
