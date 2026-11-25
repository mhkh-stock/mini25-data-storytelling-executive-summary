"""Test runner for Mini #25 — Data Storytelling & Executive Summary Pack.

Runs the full independent check suite (src/checks.py) and reports a
one-line PASS/FAIL verdict. The checks themselves are the tests:
they recompute every headline number from the raw SAMPLE CSVs with
the standard library only, re-run all 10 .sql files against a
freshly rebuilt database, and compare against every output file.

Run: python3 src/run_tests.py
Exit code 0 = all checks pass.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    proc = subprocess.run([sys.executable, str(ROOT / "src" / "checks.py")],
                          capture_output=True, text=True)
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode == 0:
        print("RUN_TESTS: PASS — every check passed")
    else:
        print("RUN_TESTS: FAIL — see failures above", file=sys.stderr)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
