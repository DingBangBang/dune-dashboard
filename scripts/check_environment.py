#!/usr/bin/env python3
"""Environment self-check for the dune-dashboard project.

Run with:  conda run -n dune-dashboard python scripts/check_environment.py
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PKGS = ["requests", "dotenv", "pandas"]

OK = "\033[92m✓\033[0m"
BAD = "\033[91m✗\033[0m"


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  {OK if ok else BAD} {label}{(' — ' + detail) if detail else ''}")
    return ok


def main() -> int:
    print("dune-dashboard environment check\n")
    all_ok = True

    all_ok &= check("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0])

    for pkg in REQUIRED_PKGS:
        try:
            importlib.import_module(pkg)
            all_ok &= check(f"python package: {pkg}", True)
        except ImportError:
            all_ok &= check(f"python package: {pkg}", False, "pip install -r requirements.txt")

    sql_files = sorted((ROOT / "queries").glob("*.sql"))
    all_ok &= check("SQL queries present", len(sql_files) >= 10, f"{len(sql_files)} files")

    all_ok &= check("docs/screenshots/ exists", (ROOT / "docs" / "screenshots").is_dir())
    all_ok &= check("git available", shutil.which("git") is not None)
    all_ok &= check("gh cli available", shutil.which("gh") is not None)

    try:
        branch = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        check("git repo initialised", True, f"branch={branch}")
    except subprocess.CalledProcessError:
        all_ok &= check("git repo initialised", False, "run: git init")

    print("\n" + ("All good ✅" if all_ok else "Some checks failed ⚠️"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
