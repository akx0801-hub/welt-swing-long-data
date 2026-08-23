#!/usr/bin/env python3
import json, sys
from pathlib import Path
p = Path(sys.argv[1] if len(sys.argv)>1 else "output/coverage.json")
x = json.loads(p.read_text(encoding="utf-8"))
print(f"Welt-Swing data run status: {x.get('run_status')} | READY {x.get('ready_count')}/{x.get('universe_count')}")
if x.get("run_status") == "FAILED":
    raise SystemExit(2)
