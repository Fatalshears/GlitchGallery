#!/usr/bin/env bash
# Build (or preview) the wiki with a pinned Quartz release.
#
#   scripts/build-site.sh          # build static site into ./public
#   scripts/build-site.sh --serve  # live preview on http://localhost:8080
#
# Quartz itself is not vendored: it is cloned into .quartz/ (gitignored) at the
# pinned tag, our config/theme from site/ is copied over it, and the small
# fixes in site/patches/ are applied (the build fails if one no longer applies).
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
for patch in "$root"/site/patches/*.patch; do
  # Reset the patched file first so repeated builds re-apply cleanly.
  git checkout --quiet -- $(sed -n 's#^+++ b/##p' "$patch")
  git apply "$patch"
done
npx quartz build --directory "$root/content" --output "$root/public" "$@"
