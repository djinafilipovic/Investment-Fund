# Pokretanje celog sistema pomocu Kubernetes alata.
#   .\scripts\deploy.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

kubectl apply -f (Join-Path $Root "kubernetes")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Cekam da svi podovi budu spremni ..."
kubectl wait --for=condition=available --timeout=600s `
    deployment/authentication-db deployment/fund-db deployment/order-cache `
    deployment/ganache deployment/authentication deployment/employee deployment/director
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

kubectl get pods -o wide
kubectl get svc
