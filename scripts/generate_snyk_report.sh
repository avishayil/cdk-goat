#!/usr/bin/env bash
#
# Generate human-readable HTML reports from Snyk JSON results.
#
# Consumes the `--json-file-output` files produced by the Snyk OSS, Code and
# IaC scans (see .github/workflows/ci.yml) and renders them to HTML using the
# `snyk-to-html` tool. The resulting reports are collected in ./snyk-reports
# so they can be published as a build artifact or attached to a GitHub release.
#
# Resolves: https://github.com/avishayil/cdk-goat/issues/4
#
# Usage:
#   ./scripts/generate_snyk_report.sh
#
set -euo pipefail

REPORT_DIR="snyk-reports"
mkdir -p "${REPORT_DIR}"

# Ensure snyk-to-html is available without adding it as a permanent dependency.
SNYK_TO_HTML="npx --yes snyk-to-html"

# Map of "<label>:<path-to-json>" inputs. The JSON files are produced by the
# `snyk ... --json-file-output=<file>` steps in CI.
declare -a REPORTS=(
  "snyk-oss:cdk/containers/dvpwa/snyk-oss.json"
  "snyk-code:cdk/containers/dvpwa/snyk-code.json"
  "snyk-iac:snyk-iac.json"
)

generated=0
for entry in "${REPORTS[@]}"; do
  label="${entry%%:*}"
  json_path="${entry#*:}"

  if [[ -f "${json_path}" ]]; then
    echo "Generating HTML report for ${label} from ${json_path}"
    ${SNYK_TO_HTML} -i "${json_path}" -o "${REPORT_DIR}/${label}.html"
    generated=$((generated + 1))
  else
    echo "Skipping ${label}: ${json_path} not found"
  fi
done

if [[ "${generated}" -eq 0 ]]; then
  echo "No Snyk JSON result files found; nothing to convert." >&2
  exit 0
fi

echo "Generated ${generated} HTML report(s) in ${REPORT_DIR}/"
