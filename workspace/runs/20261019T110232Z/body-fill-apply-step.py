#!/usr/bin/env python3
"""Print one notion-update-page arguments JSON (for CallDynamicTool). Usage: apply-step.py PATH.json"""
import sys
from pathlib import Path
sys.stdout.write(Path(sys.argv[1]).read_text())
