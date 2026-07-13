#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/assets/portrait-source.png"
OUTPUT="$ROOT/assets/portrait.txt"
PALETTE=' .-:+*osydmNM@'
EXPECTED_VERSION='jp2a 1.3.3'
NIXPKGS_REV='b5aa0fbd538984f6e3d201be0005b4463d8b09f8'

if command -v jp2a >/dev/null 2>&1; then
  converter=(jp2a)
elif command -v nix >/dev/null 2>&1; then
  # jp2a is currently marked broken in nixpkgs on Darwin even though the
  # package builds and runs. Keep the exception scoped to this invocation.
  converter=(env NIXPKGS_ALLOW_BROKEN=1 nix shell --impure "github:NixOS/nixpkgs/$NIXPKGS_REV#jp2a" -c jp2a)
else
  echo "error: jp2a or Nix is required to generate the portrait" >&2
  exit 1
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "error: missing portrait source: $SOURCE" >&2
  exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

version="$("${converter[@]}" --version 2>&1 | head -n 1)"
if [[ "$version" != "$EXPECTED_VERSION" ]]; then
  echo "error: expected $EXPECTED_VERSION, found $version" >&2
  exit 1
fi

"${converter[@]}" \
  --width=50 \
  --chars="$PALETTE" \
  --output="$tmp" \
  "$SOURCE"

# jp2a can append a final form-feed when writing to a file. Keep only printable
# ASCII plus newlines so the result is safe to embed as literal SVG text.
LC_ALL=C tr -cd '\11\12\15\40-\176' < "$tmp" \
  | sed -E 's/[[:blank:]]+$//' \
  > "$OUTPUT"

if grep -qi 'StartNTNU' "$OUTPUT"; then
  echo "error: generated portrait unexpectedly contains excluded logo text" >&2
  exit 1
fi

echo "Generated $OUTPUT with $version"
