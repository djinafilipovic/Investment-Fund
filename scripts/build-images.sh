#!/usr/bin/env bash
# Izgradnja sva tri Docker Image artefakta koje sistem koristi.
# Pokrenuti iz korenskog direktorijuma repozitorijuma:
#   ./scripts/build-images.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# pametni ugovor se kompajlira samo ako artefakt jos ne postoji
if [[ ! -f "${ROOT}/director/contracts/Voting.json" ]]; then
  echo "==> Artefakt ugovora ne postoji, kompajliram ga"
  "${ROOT}/scripts/compile-contract.sh"
fi

echo "==> Gradim iep/authentication:latest"
docker build -t iep/authentication:latest "${ROOT}/authentication"

echo "==> Gradim iep/employee:latest"
docker build -t iep/employee:latest "${ROOT}/employee"

echo "==> Gradim iep/director:latest"
docker build -t iep/director:latest "${ROOT}/director"

echo "==> Gotovo."
docker images | grep '^iep/' || true
