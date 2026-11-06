# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc.
"""Fetch docscope.py 0.1.0 and its offline tests, unchanged, from one pinned commit of
munimtechnologies/tech-writing-ai-rules, into the current folder. Standard library only."""
import sys
import urllib.request

SHA = "44981fa2bc1bdfacb3e629b80d4cecdfb476eb3a"
BASE = "https://raw.githubusercontent.com/munimtechnologies/tech-writing-ai-rules/%s/" % SHA
FILES = ("docscope.py", "test_docscope.py")


def main():
    for name in FILES:
        req = urllib.request.Request(BASE + name, headers={"User-Agent": "tech-writing-ai-rules-docsrepos/0.1"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
        with open(name, "wb") as fh:
            fh.write(body)
        print("fetched %s at %s (%d bytes)" % (name, SHA, len(body)))
    text = open("docscope.py", encoding="utf-8").read()
    if 'VERSION = "0.1.0"' not in text:
        print("docscope.py at %s is not version 0.1.0" % SHA)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
