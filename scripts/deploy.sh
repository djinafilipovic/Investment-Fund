#!/usr/bin/env bash
# Pokretanje celog sistema pomocu Kubernetes alata.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

kubectl apply -f "${ROOT}/kubernetes/"

# ---------------------------------------------------------------------------
# Klaster (containerd) ima sopstveno skladiste image-a, odvojeno od Docker-ovog,
# pa uz oznaku "latest" moze da zadrzi ranije kesiranu kopiju umesto sveze
# izgradjene. Zato se servisi prebacuju na jedinstvenu oznaku koju je zapisao
# skript build-images.sh. Sve je lokalno - pristup internetu nije potreban.
# ---------------------------------------------------------------------------
if [[ -f "${ROOT}/.image-tag" ]]; then
  BUILD_TAG="$(cat "${ROOT}/.image-tag")"
  echo "==> Prebacujem servise na oznaku izgradnje: ${BUILD_TAG}"
  kubectl set image deployment/authentication "authentication=iep/authentication:${BUILD_TAG}"
  kubectl set image deployment/employee "employee=iep/employee:${BUILD_TAG}"
  kubectl set image deployment/director "director=iep/director:${BUILD_TAG}"
else
  echo "==> Napomena: .image-tag ne postoji (pokreni ./scripts/build-images.sh)."
fi

echo "==> Cekam da svi podovi budu spremni ..."
kubectl wait --for=condition=available --timeout=600s \
  deployment/authentication-db deployment/fund-db deployment/order-cache \
  deployment/ganache deployment/authentication deployment/employee deployment/director

kubectl get pods -o wide
kubectl get svc
