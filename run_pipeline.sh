#!/usr/bin/env bash
set -euo pipefail

# run_pipeline_for_id.sh
# Usage: run_pipeline_for_id.sh [options] ID
# Options:
#   -d, --dir DIR       output base directory for downloads (default: ./downloads)
#   --no-dry-run        actually perform downloads (kept for backward compatibility)
#   --dry-run           perform a dry-run (default: perform real downloads)
#   -h, --help          show this help

OUTDIR="./downloads"
# Default: perform real downloads
NO_DRY_RUN=1

usage(){
  cat <<USAGE
Usage: run_pipeline_for_id.sh [options] ID

Options:
  -d, --dir DIR       output base directory for downloads (default: ./downloads)
  --no-dry-run        actually perform downloads (default: real downloads)
  --dry-run           perform a dry-run instead of real downloads
  -h, --help          show this help

This script runs:
  1) python3 download_radio_list.py ID -o ID.csv
  2) ./download_br8_from_csv.sh (-d OUTDIR) -f ID.csv

By default the download step runs in dry-run mode; pass --no-dry-run to perform real downloads.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--dir)
      OUTDIR="$2"; shift 2;;
    --no-dry-run)
      NO_DRY_RUN=1; shift;;
    --dry-run)
      NO_DRY_RUN=0; shift;;
    -h|--help)
      usage; exit 0;;
    --) shift; break;;
    -*) echo "Unknown option: $1" >&2; usage; exit 1;;
    *)
      # first non-option is the ID
      ID="$1"; shift; break;;
  esac
done

if [[ -z "${ID:-}" ]]; then
  echo "Error: ID is required" >&2
  usage
  exit 2
fi

CSV_DIR="csv"
mkdir -p "$CSV_DIR"
CSV_FILE="${CSV_DIR}/${ID}.csv"

echo "[1/2] Generating CSV for ID=${ID} -> ${CSV_FILE}"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 not found" >&2
  exit 1
fi

# Run the Python scraper; if it fails, stop.
python3 download_radio_list.py "$ID" -o "$CSV_FILE"

if [[ ! -f "$CSV_FILE" ]]; then
  echo "Error: expected CSV file not created: $CSV_FILE" >&2
  exit 1
fi

echo "[2/2] Running downloader for ${CSV_FILE} (outdir=${OUTDIR})"
DL_CMD=("./download_br8_from_csv.sh" -f "$CSV_FILE" -d "$OUTDIR")
if [[ "$NO_DRY_RUN" -eq 0 ]]; then
  DL_CMD=("./download_br8_from_csv.sh" --dry-run -f "$CSV_FILE" -d "$OUTDIR")
fi

echo "Executing: ${DL_CMD[*]}"
"${DL_CMD[@]}"

echo "Pipeline finished."
