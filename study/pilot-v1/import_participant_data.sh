#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: ./study/pilot-v1/import_participant_data.sh path/to/export.zip [destination-directory]"
  echo
  echo "Example:"
  echo "  ./study/pilot-v1/import_participant_data.sh ~/Downloads/gum-pilot-v1-p01.zip ~/.cache/gum-pilot-v1-p01"
  exit 1
fi

ARCHIVE="$1"
DEST_DIR="${2:-}"

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE"
  exit 1
fi

if [ -z "$DEST_DIR" ]; then
  IMPORT_ROOT="$HOME/.cache"
else
  IMPORT_ROOT="$(dirname "$DEST_DIR")"
  DEST_BASENAME="$(basename "$DEST_DIR")"
fi

mkdir -p "$IMPORT_ROOT"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

unzip -q "$ARCHIVE" -d "$TMP_DIR"

EXTRACTED_DIR="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [ -z "$EXTRACTED_DIR" ]; then
  echo "Could not find a GUM data directory inside the archive."
  exit 1
fi

if [ -z "$DEST_DIR" ]; then
  FINAL_DIR="$IMPORT_ROOT/$(basename "$EXTRACTED_DIR")"
else
  FINAL_DIR="$IMPORT_ROOT/$DEST_BASENAME"
fi

if [ -e "$FINAL_DIR" ]; then
  echo "Destination already exists: $FINAL_DIR"
  echo "Move or remove it first, or pass a different destination directory."
  exit 1
fi

mv "$EXTRACTED_DIR" "$FINAL_DIR"

echo "Imported participant GUM data to:"
echo "$FINAL_DIR"
echo
echo "Query it with:"
echo "  gum --data-directory \"$FINAL_DIR\" --recent"
echo "  gum --data-directory \"$FINAL_DIR\" -q \"your query\" -l 10"
