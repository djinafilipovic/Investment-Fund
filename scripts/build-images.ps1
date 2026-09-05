# Izgradnja sva tri Docker Image artefakta koje sistem koristi.
# Pokrenuti iz korenskog direktorijuma repozitorijuma:
#   .\scripts\build-images.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

$ContractArtifact = Join-Path $Root "director\contracts\Voting.json"
if (-not (Test-Path $ContractArtifact)) {
    Write-Host "==> Artefakt ugovora ne postoji, kompajliram ga"
    & (Join-Path $PSScriptRoot "compile-contract.ps1")
}

Write-Host "==> Gradim iep/authentication:latest"
docker build -t iep/authentication:latest (Join-Path $Root "authentication")

Write-Host "==> Gradim iep/employee:latest"
docker build -t iep/employee:latest (Join-Path $Root "employee")

Write-Host "==> Gradim iep/director:latest"
docker build -t iep/director:latest (Join-Path $Root "director")

# ---------------------------------------------------------------------------
# Jedinstvena oznaka za ovu izgradnju.
#
# Kubernetes klaster (containerd) ima sopstveno skladiste image-a, odvojeno od
# Docker-ovog. Uz oznaku "latest" i imagePullPolicy: IfNotPresent, klaster
# zadrzi vec kesiranu kopiju i ne primeti novu izgradnju. Zbog toga se svaka
# izgradnja dodatno oznacava jedinstvenom oznakom, koju skript deploy.ps1
# koristi da bi klaster sigurno preuzeo bas ovu verziju.
#
# Oznaka je lokalna - ne zahteva pristup internetu ni registry.
# ---------------------------------------------------------------------------
$BuildTag = "build-" + (Get-Date -Format "yyyyMMdd-HHmmss")

foreach ($service in @("authentication", "employee", "director")) {
    docker tag "iep/${service}:latest" "iep/${service}:${BuildTag}"
}

Set-Content -Path (Join-Path $Root ".image-tag") -Value $BuildTag

Write-Host "==> Gotovo. Oznaka izgradnje: $BuildTag"
docker images | Select-String "^iep/"
