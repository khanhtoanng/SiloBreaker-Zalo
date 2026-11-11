"""Compatibility command wrapper; imports do not start a workflow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.cli import main

if __name__ == "__main__":
    main(["package-check", *sys.argv[1:]])
