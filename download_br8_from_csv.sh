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

CSV_FILE=""
OUTDIR="./downloads"
# By default only download rows with get == 0
ONLY_GET_ZERO=1
DRY_RUN=0

usage(){
  cat <<USAGE
Usage: download_br8_from_csv.sh [options]

Options:
  -f, --file FILE      CSV file to read (required). You may pass a base name like 'BR8Z3NX7XM' ('.csv' will be appended).
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
    *) echo "Positional arguments are not accepted; use -f/--file" >&2; usage; exit 1;;
  esac
done

if [[ -z "$CSV_FILE" ]]; then
  echo "Error: -f/--file is required." >&2
  usage
  exit 2
fi

# normalize CSV_FILE: append .csv if missing
if [[ "$CSV_FILE" != *.csv ]]; then
  CSV_FILE="${CSV_FILE}.csv"
fi

if [[ ! -f "$CSV_FILE" ]]; then
  echo "CSV file not found: $CSV_FILE" >&2
  exit 2
fi

# Use the CSV base name (without .csv) as the download subdirectory (ID-based)
ID_NAME=$(basename "$CSV_FILE" .csv)
OUTDIR="$OUTDIR/$ID_NAME"
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
      program = row.get('program','') or ''
      title = row.get('title','') or ''
      date = row.get('broadcast_date','') or ''
      bstart = row.get('broadcast_start','') or ''
      # output: hls, title, broadcast_date, broadcast_start, program, get
      print('\t'.join([hls, title, date, bstart, program, str(getint)]))
PY

index=1
while IFS=$'\t' read -r hls title date bstart program getflag; do
  # clean hls URL: remove CR/LF and surrounding whitespace
  hls_clean=$(printf '%s' "$hls" | tr -d '\r\n')
  hls_clean="$(echo -n "$hls_clean" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  safe_title=$(sanitize "$title")
  safe_date=$(sanitize "$date")
  outname="${safe_date}${safe_title}.mp3"
  outpath="$OUTDIR/$outname"

  if [[ -f "$outpath" ]]; then
    echo "Skipping existing: $outpath"
    ((index++))
    continue
  fi

  echo "Downloading [$index]: ${title:-<no-title>} [program:${program:-<no-program>}] (${date:-<no-date>}, start:${bstart:-<no-start>}) -> $outpath"
  # reduce ffmpeg verbosity: show only errors, and disable interactive stdin
  # Transcode to MP3 (libmp3lame) at 64 kbps
  cmd=(ffmpeg -hide_banner -loglevel error -nostdin -y -i "$hls_clean" -vn -c:a libmp3lame -b:a 64k "$outpath")
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'DRY RUN: %s\n' "${cmd[*]}"
  else
    # Run ffmpeg and only update CSV on success. Use if...then to avoid set -e exiting on non-zero.
    if "${cmd[@]}"; then
      # After successful transcode, set ID3 tags (title -> song, album -> program) using mid3v2
      if command -v mid3v2 >/dev/null 2>&1; then
        # Use broadcast_date + title as the song title
        song_title="${date} ${title}"
        # Trim leading/trailing whitespace
        song_title="$(echo -n "$song_title" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
        if [[ "$DRY_RUN" -eq 1 ]]; then
          printf 'DRY RUN: mid3v2 --song="%s" --album="%s" --artist="%s" "%s"\n' "$song_title" "$program" "NHKラジオ" "$outpath"
        else
          mid3v2 --song="$song_title" --album="$program" --artist="NHKラジオ" "$outpath" || echo "Warning: mid3v2 failed for $outpath" >&2
        fi
      else
        echo "Warning: mid3v2 not found; skipping ID3 tag write for $outpath" >&2
      fi

      # Update CSV: set get=1 for rows matching this hls URL
      export CURRENT_HLS="$hls_clean"
      python3 - <<'PY'
import os, csv, tempfile, shutil
fn = os.environ.get('CSV_FILE')
target = os.environ.get('CURRENT_HLS')
if not fn or not target:
    raise SystemExit(0)

# Read CSV
with open(fn, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames or []
    rows = list(reader)

if 'get' not in fieldnames:
    fieldnames.append('get')

changed = False
for r in rows:
    h = (r.get('hls_url') or r.get('hls') or '').strip()
    if h == target:
        try:
            if int(r.get('get','0')) != 1:
                r['get'] = '1'
                changed = True
        except Exception:
            r['get'] = '1'
            changed = True

if changed:
    # backup original
    shutil.copyfile(fn, fn + '.bak')
    dname = os.path.dirname(fn) or '.'
    fd, tmpfn = tempfile.mkstemp(prefix='csvtmp', dir=dname)
    os.close(fd)
    with open(tmpfn, 'w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    os.replace(tmpfn, fn)
PY
      unset CURRENT_HLS
    else
      echo "ffmpeg failed for: $hls_clean" >&2
    fi
  fi

  ((index++))
done < "$TEMPFILE"

echo "Done."
