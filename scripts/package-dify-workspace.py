#!/usr/bin/env python3
"""Zip skills/<name>/ so SKILL.md sits at the archive root.

Dify 1.17 Skills → Import accepts .zip / .skill and requires SKILL.md inside
the package. Putting SKILL.md at the zip root avoids a nested folder surprise.

This only packages existing skill folders. It does not rewrite SKILL.md.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
DIST = ROOT / "dist"

# Operator checklists that are useful as in-app drafts on Dify 1.17.
DEFAULT_SKILLS = (
    "dify-troubleshooting",
    "dify-compose-and-config",
    "dify-plugin-install",
    "dify-console-api",
)

SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def skill_dirs(names: list[str] | None, all_skills: bool) -> list[Path]:
    if all_skills:
        dirs = sorted(p for p in SKILLS.glob("dify-*") if (p / "SKILL.md").is_file())
        if not dirs:
            raise SystemExit("no skills/dify-*/SKILL.md found")
        return dirs
    wanted = names or list(DEFAULT_SKILLS)
    dirs: list[Path] = []
    missing: list[str] = []
    for name in wanted:
        path = SKILLS / name
        if not (path / "SKILL.md").is_file():
            missing.append(name)
            continue
        dirs.append(path)
    if missing:
        raise SystemExit("missing SKILL.md for: " + ", ".join(missing))
    return dirs


def iter_skill_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        files.append(path)
    return files


def write_archive(skill_dir: Path, dest: Path) -> None:
    files = iter_skill_files(skill_dir)
    if not any(p.name == "SKILL.md" and p.parent == skill_dir for p in files):
        raise SystemExit(f"{skill_dir.name}: SKILL.md must be at the skill folder root")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arcname = path.relative_to(skill_dir).as_posix()
            if arcname.startswith("/") or ".." in Path(arcname).parts:
                raise SystemExit(f"{skill_dir.name}: unsafe path {arcname}")
            zf.write(path, arcname)
    with zipfile.ZipFile(dest, "r") as zf:
        names = zf.namelist()
    if "SKILL.md" not in names:
        raise SystemExit(f"{dest.name}: packed archive is missing SKILL.md at zip root")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Package skills/<name>/ into dist/*.zip (or .skill) with SKILL.md at the "
            "archive root for Dify 1.17 Skills Import."
        )
    )
    parser.add_argument(
        "names",
        nargs="*",
        help="skill directory names under skills/ (default: the four operator checklists)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="package every skills/dify-* folder that has SKILL.md",
    )
    parser.add_argument(
        "--format",
        choices=("zip", "skill"),
        default="zip",
        dest="fmt",
        help="archive extension (Dify Import accepts both .zip and .skill)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DIST,
        help="output directory (default: dist/)",
    )
    args = parser.parse_args()
    if args.names and args.all:
        parser.error("pass either skill names or --all, not both")

    dirs = skill_dirs(args.names, args.all)
    suffix = ".zip" if args.fmt == "zip" else ".skill"
    written: list[Path] = []
    for skill_dir in dirs:
        dest = args.out / f"{skill_dir.name}{suffix}"
        write_archive(skill_dir, dest)
        written.append(dest)
        print(f"wrote {dest.relative_to(ROOT)} ({dest.stat().st_size} bytes)")
    print(f"packed {len(written)} skill(s) -> {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
