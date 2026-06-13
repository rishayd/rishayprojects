#!/usr/bin/env bash
#
# Downloads Synthea (if not already present) and generates a synthetic
# patient population as CSV files into data/synthea/csv/.
#
# Usage:
#   ./run_synthea.sh [population_size] [state]
#
# Examples:
#   ./run_synthea.sh                # 2000 patients, Massachusetts
#   ./run_synthea.sh 5000 California

set -euo pipefail

SYNTHEA_VERSION="3.3.0"
POPULATION="${1:-2000}"
STATE="${2:-Massachusetts}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JAR_DIR="${ROOT_DIR}/.synthea"
OUTPUT_DIR="${ROOT_DIR}/data/synthea"
JAR_PATH="${JAR_DIR}/synthea-with-dependencies.jar"

mkdir -p "${JAR_DIR}" "${OUTPUT_DIR}"

if [ ! -f "${JAR_PATH}" ]; then
  echo "Downloading Synthea v${SYNTHEA_VERSION}..."
  curl -L -o "${JAR_PATH}" \
    "https://github.com/synthetichealth/synthea/releases/download/v${SYNTHEA_VERSION}/synthea-with-dependencies.jar"
fi

echo "Generating ${POPULATION} synthetic patients for ${STATE}..."
java -jar "${JAR_PATH}" \
  -p "${POPULATION}" \
  --exporter.csv.export=true \
  --exporter.csv.folder_per_run=false \
  --exporter.fhir.export=false \
  --exporter.hospital.fhir.export=false \
  --exporter.practitioner.fhir.export=false \
  --exporter.baseDirectory="${OUTPUT_DIR}" \
  "${STATE}"

echo ""
echo "Done. CSVs written to ${OUTPUT_DIR}/csv/"
echo "Next: run 'python src/data_generation/simulate_app_events.py' to generate app engagement data."
