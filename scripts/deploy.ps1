# Pokretanje celog sistema pomocu Kubernetes alata.
#   .\scripts\deploy.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

kubectl apply -f (Join-Path $Root "kubernetes")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# ---------------------------------------------------------------------------
# Klaster (containerd) ima sopstveno skladiste image-a, odvojeno od Docker-ovog,
# pa uz oznaku "latest" moze da zadrzi ranije kesiranu kopiju umesto sveze
# izgradjene. Zato se servisi prebacuju na jedinstvenu oznaku koju je zapisao
# skript build-images.ps1. Sve je lokalno - pristup internetu nije potreban.
# ---------------------------------------------------------------------------
$TagFile = Join-Path $Root ".image-tag"
if (Test-Path $TagFile) {
    $BuildTag = (Get-Content $TagFile -Raw).Trim()
    Write-Host "==> Prebacujem servise na oznaku izgradnje: $BuildTag"
    kubectl set image deployment/authentication "authentication=iep/authentication:${BuildTag}"
    kubectl set image deployment/employee "employee=iep/employee:${BuildTag}"
    kubectl set image deployment/director "director=iep/director:${BuildTag}"
} else {
    Write-Host "==> Napomena: .image-tag ne postoji (pokreni .\scripts\build-images.ps1)."
}

Write-Host "==> Cekam da svi podovi budu spremni ..."
kubectl wait --for=condition=available --timeout=600s `
    deployment/authentication-db deployment/fund-db deployment/order-cache `
    deployment/ganache deployment/authentication deployment/employee deployment/director
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

kubectl get pods -o wide
kubectl get svc
