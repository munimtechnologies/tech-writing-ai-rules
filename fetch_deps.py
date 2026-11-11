# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0.
"""Download study 7's published learnlabels.py (0.1.0) next to learnsnap.py. Exit 2 if the
download fails or the version is not 0.1.0."""
import re
import sys
import urllib.request

URL = ("https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/main/"
       "learnlabels.py")

try:
    req = urllib.request.Request(URL, headers={"User-Agent": "tech-writing-ai-rules-learnsnap"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
except Exception as exc:
    print("download failed: %s" % type(exc).__name__)
    sys.exit(2)
m = re.search(rb'^VERSION = "([^"]+)"', data, re.M)
if not m or m.group(1) != b"0.1.0":
    print("unexpected learnlabels version: %r" % (m.group(1) if m else None))
    sys.exit(2)
with open("learnlabels.py", "wb") as fh:
    fh.write(data)
print("learnlabels.py 0.1.0 saved (%d bytes)" % len(data))
