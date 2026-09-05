# ---------------------------------------------------------------------------
# Kompajliranje pametnog ugovora u artefakt director/contracts/Voting.json.
#
# Skript se pokrece jednom (i ponovo samo ako se izmeni Voting.sol). Rezultat
# su ABI i EVM bytecode, sto ne zavisi od arhitekture racunara, pa se dobijeni
# artefakt samo prenosi u Docker Image i za izgradnju image-a nije potreban
# ni kompajler ni pristup internetu.
#
# Kompajliranje se izvrsava u jednokratnom linux/amd64 kontejneru. Na Windows
# racunarima (skoro uvek amd64) ovo se izvrsava nativno, bez emulacije.
#
#   .\scripts\compile-contract.ps1
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

$SolcVersion = if ($env:SOLC_VERSION) { $env:SOLC_VERSION } else { "0.8.19" }
$SolcBuild   = if ($env:SOLC_BUILD)   { $env:SOLC_BUILD }   else { "solc-linux-amd64-v0.8.19+commit.7dd6d404" }
$SolcSha256  = if ($env:SOLC_SHA256)  { $env:SOLC_SHA256 }  else { "7a5c1d3dc9a8eba62bb2ec37192c9178ae5fe8a54a56e5573fd3c9c17cd9eb48" }
# podrazumevani izvor biblioteke py-solc-x (solc-bin.ethereum.org) vise ne
# postoji; zvanicna zamena je binaries.soliditylang.org
$SolcUrl = "https://binaries.soliditylang.org/linux-amd64/$SolcBuild"

$Cache  = Join-Path $Root ".solc-cache"
$Binary = Join-Path $Cache "solc-v$SolcVersion"

New-Item -ItemType Directory -Force -Path $Cache | Out-Null

if (-not (Test-Path $Binary)) {
    Write-Host "==> Preuzimam solc $SolcVersion"
    $PartFile = "$Binary.part"
    Invoke-WebRequest -Uri $SolcUrl -OutFile $PartFile -TimeoutSec 300

    $Digest = (Get-FileHash -Path $PartFile -Algorithm SHA256).Hash.ToLower()
    if ($Digest -ne $SolcSha256) {
        Remove-Item -Force $PartFile
        Write-Error "GRESKA: neispravna kontrolna suma ($Digest)"
        exit 1
    }

    Move-Item -Force $PartFile $Binary
    Write-Host "==> Kontrolna suma je ispravna."
} else {
    Write-Host "==> Koristim vec preuzet solc iz .solc-cache/"
}

Write-Host "==> Kompajliram Voting.sol (linux/amd64 kontejner)"

docker run --rm --platform linux/amd64 `
    -v "$(Join-Path $Root 'director'):/app" `
    -v "${Binary}:/opt/solc/solc-v${SolcVersion}:ro" `
    -w /app `
    -e SOLCX_BINARY_PATH=/opt/solc `
    -e SOLC_VERSION=$SolcVersion `
    python:3.11-slim `
    bash -c 'pip install --quiet --no-cache-dir py-solc-x==2.0.3 && python compile_contract.py'

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Gotovo:"
$Artifact = Get-Content (Join-Path $Root "director\contracts\Voting.json") | ConvertFrom-Json
Write-Host "    contractName:" $Artifact.contractName
Write-Host "    solcVersion: " $Artifact.solcVersion
Write-Host "    evmVersion:  " $Artifact.evmVersion
Write-Host "    abi stavki:  " $Artifact.abi.Count
Write-Host "    bytecode:    " $Artifact.bytecode.Length "karaktera"
