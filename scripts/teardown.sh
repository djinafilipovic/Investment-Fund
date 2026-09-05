#!/usr/bin/env bash
# Uklanjanje sistema. Dodati --purge da bi se obrisali i trajni podaci.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

kubectl delete -f "${ROOT}/kubernetes/" --ignore-not-found

if [[ "${1:-}" == "--purge" ]]; then
  kubectl delete pvc authentication-db-data fund-db-data order-cache-data --ignore-not-found
fi
