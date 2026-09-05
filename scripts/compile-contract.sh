#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Kompajliranje pametnog ugovora u artefakt director/contracts/Voting.json.
#
# Skript se pokrece jednom (i ponovo samo ako se izmeni Voting.sol). Rezultat
# su ABI i EVM bytecode, sto ne zavisi od arhitekture racunara, pa se dobijeni
# artefakt samo prenosi u Docker Image i za izgradnju image-a nije potreban
# ni kompajler ni pristup internetu.
#
# Kompajliranje se izvrsava u jednokratnom linux/amd64 kontejneru jer Solidity
# tim ne objavljuje solc 0.8.19 za linux/arm64.
#
#   ./scripts/compile-contract.sh
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SOLC_VERSION="${SOLC_VERSION:-0.8.19}"
SOLC_BUILD="${SOLC_BUILD:-solc-linux-amd64-v0.8.19+commit.7dd6d404}"
SOLC_SHA256="${SOLC_SHA256:-7a5c1d3dc9a8eba62bb2ec37192c9178ae5fe8a54a56e5573fd3c9c17cd9eb48}"
# podrazumevani izvor biblioteke py-solc-x (solc-bin.ethereum.org) vise ne
# postoji; zvanicna zamena je binaries.soliditylang.org
SOLC_URL="https://binaries.soliditylang.org/linux-amd64/${SOLC_BUILD}"

CACHE="${ROOT}/.solc-cache"
BINARY="${CACHE}/solc-v${SOLC_VERSION}"

mkdir -p "${CACHE}"

if [[ ! -x "${BINARY}" ]]; then
  echo "==> Preuzimam solc ${SOLC_VERSION}"
  curl -fsSL --max-time 300 -o "${BINARY}.part" "${SOLC_URL}"

  # sha256sum (Linux, WSL, Git Bash) ili shasum (macOS) - sta god je dostupno
  if command -v sha256sum >/dev/null 2>&1; then
    DIGEST="$(sha256sum "${BINARY}.part" | cut -d' ' -f1)"
  else
    DIGEST="$(shasum -a 256 "${BINARY}.part" | cut -d' ' -f1)"
  fi
  if [[ "${DIGEST}" != "${SOLC_SHA256}" ]]; then
    rm -f "${BINARY}.part"
    echo "GRESKA: neispravna kontrolna suma (${DIGEST})" >&2
    exit 1
  fi

  mv "${BINARY}.part" "${BINARY}"
  chmod +x "${BINARY}"
  echo "==> Kontrolna suma je ispravna."
else
  echo "==> Koristim vec preuzet solc iz .solc-cache/"
fi

echo "==> Kompajliram Voting.sol (linux/amd64 kontejner)"

docker run --rm --platform linux/amd64 \
  -v "${ROOT}/director:/app" \
  -v "${BINARY}:/opt/solc/solc-v${SOLC_VERSION}:ro" \
  -w /app \
  -e SOLCX_BINARY_PATH=/opt/solc \
  -e SOLC_VERSION="${SOLC_VERSION}" \
  python:3.11-slim \
  bash -c 'pip install --quiet --no-cache-dir py-solc-x==2.0.3 && python compile_contract.py'

echo "==> Gotovo:"
python3 - "${ROOT}/director/contracts/Voting.json" <<'PY'
import json, pathlib, sys

artifact = json.loads(pathlib.Path(sys.argv[1]).read_text())
print("    contractName:", artifact["contractName"])
print("    solcVersion: ", artifact["solcVersion"])
print("    evmVersion:  ", artifact["evmVersion"])
print("    abi stavki:  ", len(artifact["abi"]))
print("    bytecode:    ", len(artifact["bytecode"]), "karaktera")
PY
