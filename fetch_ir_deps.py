# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Download the published learnlabels.py (0.1.0, study 7) and learnshown.py (0.2.0, study 8)
next to includereach.py (study 13). Exit 2 if a download fails or a version is not the one
expected. Made by MV2 of Munim, Inc., with AI agents working in his name."""
import re
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
WANT = {"learnlabels.py": b"0.1.0", "learnshown.py": b"0.2.0"}

for name, version in WANT.items():
    try:
        req = urllib.request.Request(BASE + name, headers={"User-Agent": "tech-writing-ai-rules-includereach"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except Exception as exc:
        print("download of %s failed: %s" % (name, type(exc).__name__))
        sys.exit(2)
    m = re.search(rb'^VERSION = "([^"]+)"', data, re.M)
    if not m or m.group(1) != version:
        print("unexpected %s version: %r" % (name, m.group(1) if m else None))
        sys.exit(2)
    with open(name, "wb") as fh:
        fh.write(data)
    print("%s %s saved (%d bytes)" % (name, version.decode(), len(data)))
