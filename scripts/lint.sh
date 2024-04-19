
#!/usr/bin/env bash
set -euo pipefail

GIT_REPO_ROOT=$(git rev-parse --show-toplevel)
CHARTS_DIRECTORY="${GIT_REPO_ROOT}/helm"

FAILED=()

cd ${CHARTS_DIRECTORY}
for d in */; do
  echo "Linting chart ${d} w/ helm v3"
  helm lint ${CHARTS_DIRECTORY}/${d} || FAILED+=("${d}")
done

if [[ "${#FAILED[@]}" -eq 0 ]]; then
  echo "All charts passed linting!"
  exit 0
else
  for chart in "${FAILED[@]}"; do
    printf "%40s ❌\n" "$chart"
  done
fi