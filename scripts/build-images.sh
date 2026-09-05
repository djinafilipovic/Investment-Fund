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

# ---------------------------------------------------------------------------
# Jedinstvena oznaka za ovu izgradnju.
#
# Kubernetes klaster (containerd) ima sopstveno skladiste image-a, odvojeno od
# Docker-ovog. Uz oznaku "latest" i imagePullPolicy: IfNotPresent, klaster
# zadrzi vec kesiranu kopiju i ne primeti novu izgradnju. Zbog toga se svaka
# izgradnja dodatno oznacava jedinstvenom oznakom, koju skript deploy.sh
# koristi da bi klaster sigurno preuzeo bas ovu verziju.
#
# Oznaka je lokalna - ne zahteva pristup internetu ni registry.
# ---------------------------------------------------------------------------
BUILD_TAG="build-$(date +%Y%m%d-%H%M%S)"

for service in authentication employee director; do
  docker tag "iep/${service}:latest" "iep/${service}:${BUILD_TAG}"
done

echo "${BUILD_TAG}" > "${ROOT}/.image-tag"

echo "==> Gotovo. Oznaka izgradnje: ${BUILD_TAG}"
docker images | grep '^iep/' || true
