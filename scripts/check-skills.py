#!/usr/bin/env python3
"""Fail if skills are unpublished-quality: missing frontmatter, secrets, host paths."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
FORBIDDEN = (
    re.compile(r"/workspace/"),
    re.compile(r"/home/box\b"),
    re.compile(r"zl@dify"),
    re.compile(r"gho_[A-Za-z0-9]+"),
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
    re.compile(r"pbocwx", re.I),
    re.compile(r"zhulei@"),
    re.compile(r"wx@qq\.com"),
    re.compile(r"app-blPfU6KGVCAbMIBGB4DADo8b"),
    re.compile(r"192\.168\.33\."),
    re.compile(r"10\.10\.1\.4"),
)
errors: list[str] = []
skills = sorted(p for p in SKILLS.glob("*/SKILL.md"))
if not skills:
    errors.append("no skills/*/SKILL.md found")

for path in skills:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    if not text.startswith("---"):
        errors.append(f"{rel}: missing YAML frontmatter")
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{rel}: unterminated frontmatter")
        continue
    fm, body = parts[1], parts[2]
    if "name:" not in fm:
        errors.append(f"{rel}: frontmatter missing name")
    if "description:" not in fm:
        errors.append(f"{rel}: frontmatter missing description")
    elif "Use this when" not in fm and "Use this first" not in fm:
        errors.append(f"{rel}: description should say when to use the skill")
    if len(body.strip()) < 200:
        errors.append(f"{rel}: body too short")
    for pat in FORBIDDEN:
        if pat.search(text):
            errors.append(f"{rel}: forbidden pattern {pat.pattern}")

version = (ROOT / "VERSION").read_text(encoding="utf-8")
if "dify:" not in version:
    errors.append("VERSION: missing dify pin")
if "status:" not in version:
    errors.append("VERSION: missing status")

if errors:
    print("check-skills: FAIL")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
print(f"check-skills: OK ({len(skills)} skills)")
