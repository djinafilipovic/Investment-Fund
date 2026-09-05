#!/usr/bin/env bash
# Pokretanje celog sistema pomocu Kubernetes alata.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

kubectl apply -f "${ROOT}/kubernetes/"

echo "==> Cekam da svi podovi budu spremni ..."
kubectl wait --for=condition=available --timeout=600s \
  deployment/authentication-db deployment/fund-db deployment/order-cache \
  deployment/ganache deployment/authentication deployment/employee deployment/director

kubectl get pods -o wide
kubectl get svc
