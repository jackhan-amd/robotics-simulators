#!/usr/bin/env python3
"""Build an optional local recipe index without local run data."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from simulators.site import build
if __name__=='__main__':print(json.dumps(build()))
