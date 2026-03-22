"""Build a single-file executable with PyInstaller.

Usage:
    python build_executable.py
"""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).parent
cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--windowed",
    "--name",
    "ExtinvalInbox",
    "--add-data",
    f"{root / 'assets'}{';' if sys.platform.startswith('win') else ':'}assets",
    "app/main.py",
]
subprocess.run(cmd, check=True)
