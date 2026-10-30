#!/usr/bin/env bash
# Build (or preview) the wiki with a pinned Quartz release.
#
#   scripts/build-site.sh          # build static site into ./public
#   scripts/build-site.sh --serve  # live preview on http://localhost:8080
#
# Quartz itself is not vendored: it is cloned into .quartz/ (gitignored) at the
# pinned tag, and our config/theme from site/ is copied over it.
set -euo pipefail

QUARTZ_VERSION="v4.5.2"
root="$(cd "$(dirname "$0")/.." && pwd)"
qdir="$root/.quartz"

if [ ! -f "$qdir/.version" ] || [ "$(cat "$qdir/.version")" != "$QUARTZ_VERSION" ]; then
  rm -rf "$qdir"
  git clone --quiet --depth 1 --branch "$QUARTZ_VERSION" https://github.com/jackyzha0/quartz.git "$qdir"
  echo "$QUARTZ_VERSION" > "$qdir/.version"
  (cd "$qdir" && npm ci --no-audit --no-fund --loglevel=error)
fi

cp "$root/site/quartz.config.ts" "$qdir/quartz.config.ts"
cp "$root/site/quartz.layout.ts" "$qdir/quartz.layout.ts"
cp "$root/site/custom.scss" "$qdir/quartz/styles/custom.scss"

cd "$qdir"
npx quartz build --directory "$root/content" --output "$root/public" "$@"
