#!/usr/bin/env bash
set -euo pipefail

GIT_REPO_ROOT=$(git rev-parse --show-toplevel)
CHARTS_DIRECTORY="${GIT_REPO_ROOT}/helm"

FAILED=()

cd ${CHARTS_DIRECTORY}
for d in */; do
  echo "Validating chart ${d} w/ helm v3"
  helm template ${CHARTS_DIRECTORY}/${d} | kubeconform --strict --ignore-missing-schemas || FAILED+=("${d}")
done

if [[ "${#FAILED[@]}" -eq 0 ]]; then
  echo "All charts passed validations!"
  exit 0
else
  for chart in "${FAILED[@]}"; do
    printf "%40s ❌\n" "$chart"
  done
fi