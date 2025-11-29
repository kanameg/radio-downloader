#!/usr/bin/env bash
set -euo pipefail

# download_br8_from_csv.sh
# Read `BR8Z3NX7XM.csv` (or a specified CSV) and download each `hls_url` with ffmpeg.
# Usage:
#   ./download_br8_from_csv.sh [options]
# Options:
#   -f, --file FILE      CSV file to read (default: BR8Z3NX7XM.csv)
#   -d, --dir DIR        output directory (default: ./downloads)
#   --only-get-zero      only download rows with get == 0
#   --dry-run            print ffmpeg commands instead of executing them
#   -h, --help           show help

CSV_FILE="BR8Z3NX7XM.csv"
OUTDIR="./downloads"
# By default only download rows with get == 0
ONLY_GET_ZERO=1
DRY_RUN=0

usage(){
  cat <<USAGE
Usage: download_br8_from_csv.sh [options]

Options:
  -f, --file FILE      CSV file to read (default: BR8Z3NX7XM.csv)
  -d, --dir DIR        Output directory (default: ./downloads)
  --only-get-zero      Only download rows with get == 0 (default)
  --all                Download all rows regardless of `get`
  --dry-run            Print ffmpeg commands instead of running them
  -h, --help           Show this help

CSV must contain header with at least `hls_url`. Optional: `title`, `broadcast_date`, `get`.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)
      CSV_FILE="$2"; shift 2;;
    -d|--dir)
      OUTDIR="$2"; shift 2;;
    --only-get-zero)
      ONLY_GET_ZERO=1; shift;;
    --all)
      ONLY_GET_ZERO=0; shift;;
    --dry-run)
      DRY_RUN=1; shift;;
    -h|--help)
      usage; exit 0;;
    --) shift; break;;
    -*) echo "Unknown option: $1" >&2; usage; exit 1;;
    *) CSV_FILE="$1"; shift;;
  esac
done

if [[ ! -f "$CSV_FILE" ]]; then
  echo "CSV file not found: $CSV_FILE" >&2
  exit 2
fi

mkdir -p "$OUTDIR"

sanitize(){
  local s="$1"
  s="$(echo "$s" | tr '\n\r' '  ')"
  s="$(echo "$s" | sed -E 's#[/\\:\"?*<>|]+#_#g')"
  s="$(echo "$s" | sed -E 's/[^[:print:]]+/_/g')"
  s="$(echo "$s" | tr ' ' '_')"
  echo "${s:0:120}"
}

# Temporary file to receive parsed rows (tab-separated)
TEMPFILE=$(mktemp)
trap 'rm -f "$TEMPFILE"' EXIT

export CSV_FILE="$CSV_FILE"
export ONLY_GET_ZERO="$ONLY_GET_ZERO"

# Use Python csv module to parse reliably
python3 - <<'PY' > "$TEMPFILE"
import csv,os,sys
fn = os.environ.get('CSV_FILE')
only_get_zero = os.environ.get('ONLY_GET_ZERO','0') == '1'
with open(fn, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        hls = (row.get('hls_url') or row.get('hls') or '').strip()
        if not hls:
            continue
        getv = row.get('get','')
        try:
            getint = int(getv) if getv!='' else 0
        except Exception:
            getint = 0
        if only_get_zero and getint != 0:
            continue
        title = row.get('title','') or ''
        date = row.get('broadcast_date','') or ''
        print('\t'.join([hls, title, date, str(getint)]))
PY

index=1
while IFS=$'\t' read -r hls title date getflag; do
  # clean hls URL: remove CR/LF and surrounding whitespace
  hls_clean=$(printf '%s' "$hls" | tr -d '\r\n')
  hls_clean="$(echo -n "$hls_clean" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  safe_title=$(sanitize "$title")
  safe_date=$(sanitize "$date")
  outname="${safe_date}_${safe_title}.m4a"
  outpath="$OUTDIR/$outname"

  if [[ -f "$outpath" ]]; then
    echo "Skipping existing: $outpath"
    ((index++))
    continue
  fi

  echo "Downloading [$index]: ${title:-<no-title>} (${date:-<no-date>}) -> $outpath"
  # reduce ffmpeg verbosity: show only errors, and disable interactive stdin
  cmd=(ffmpeg -hide_banner -loglevel error -nostdin -y -i "$hls_clean" -c copy -bsf:a aac_adtstoasc "$outpath")
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'DRY RUN: %s\n' "${cmd[*]}"
  else
    "${cmd[@]}"
  fi

  ((index++))
done < "$TEMPFILE"

echo "Done."
