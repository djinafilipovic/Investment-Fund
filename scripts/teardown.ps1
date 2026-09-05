# Uklanjanje sistema.
#   .\scripts\teardown.ps1              # uklanja sve osim trajnih podataka
#   .\scripts\teardown.ps1 -Purge       # uklanja i trajne podatke iz baza

param(
    [switch]$Purge
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

kubectl delete -f (Join-Path $Root "kubernetes") --ignore-not-found

if ($Purge) {
    kubectl delete pvc authentication-db-data fund-db-data order-cache-data --ignore-not-found
}
