"""Compatibility wrapper — redirects to root run_digest.py."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
subprocess.check_call([sys.executable, str(ROOT / "run_digest.py")], cwd=ROOT)
