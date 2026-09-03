#!/usr/bin/env bash
# Copy this repo's skills/dify-* folders into an Agent Skills directory.
# Usage:
#   ./scripts/install.sh user|project
#   ./scripts/install.sh --dest /path/to/skills
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/skills"

usage() {
  cat <<'U'
Install Dify operating skills into an Agent Skills directory.

  ./scripts/install.sh <target>
  ./scripts/install.sh --dest /path/to/skills

Targets:
  user       ~/.agents/skills
  project    ./.agents/skills          (cwd)

Each skill is a folder with SKILL.md. Existing folders with the same name
are replaced. Source of truth stays in this repo (skills/).
U
}

dest=""
case "${1:-}" in
  -h|--help|"") usage; exit 0 ;;
  --dest)
    dest="${2:?--dest needs a path}"
    ;;
  user) dest="$HOME/.agents/skills" ;;
  project) dest="$(pwd)/.agents/skills" ;;
  *)
    echo "unknown target: $1" >&2
    usage
    exit 1
    ;;
esac

mkdir -p "$dest"
copied=0
for skill in "$SRC"/dify-*; do
  [ -f "$skill/SKILL.md" ] || continue
  name="$(basename "$skill")"
  rm -rf "$dest/$name"
  cp -R "$skill" "$dest/$name"
  copied=$((copied + 1))
done

echo "installed $copied skills -> $dest"
echo "invoke the router with /dify-development"
