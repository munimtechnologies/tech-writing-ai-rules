# SPDX-License-Identifier: Apache-2.0
# rawlink 0.1.0 - pre-registered check (study 17): in Mem0 OSS 2.2.1, do memories
# stored verbatim (infer=False) get entity links, and so the search "entity boost",
# only after their text is edited with update()?
# Made with AI agents working in the name of MV2 of Munim, Inc. (mv2@munimtech.com).
"""Usage: python rawlink.py --out-dir /out [--work-dir DIR]

Everything runs locally: FastEmbed embeddings, a local Qdrant folder, spaCy
en_core_web_sm for Mem0's entity extraction. No language model is called (the
LLM client gets a placeholder key and a closed local address, and its
generate_response is replaced by a function that fails loudly).

Writes observations.json and RESULT.txt to --out-dir. Exit 0 when the run
completed (whatever the verdicts); exit 1 on a crash.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import traceback
from typing import Any, Dict, Iterable, List, Optional, Set

__version__ = "0.1.0"

USER_A = "team-a"  # 10 of its 20 rules are edited with update()
USER_B = "team-b"  # the same 20 final texts, stored raw, never edited
MODEL = "BAAI/bge-small-en-v1.5"
DIMS = 384
CLOSED_LLM_URL = "http://127.0.0.1:9/v1"
SUFFIX = " Reviewers check this on every page."
BOOST_MIN = 0.001   # P3: A minus B score above this counts as boosted
SAME_MAX = 0.001    # P4: |A - B| below this counts as unchanged

# (entity named in the rule, rule text). Even indexes are edited in team A.
RULES = [
    ("GitHub", "Always spell GitHub with a capital H."),
    ("JavaScript", "Write JavaScript as one word with a capital S."),
    ("PyPI", "Call the Python package index PyPI, not Pypi."),
    ("Kubernetes", "Kubernetes is never shortened to K8s in headings."),
    ("PostgreSQL", "Write PostgreSQL in full on first mention and Postgres after that."),
    ("macOS", "Write macOS with a lowercase m."),
    ("TypeScript", "TypeScript examples must compile with strict mode on."),
    ("Docker", "Docker commands in examples use the long flag names."),
    ("Markdown", "Markdown files use ATX headings."),
    ("YAML", "YAML examples use two-space indentation."),
    ("npm", "Write npm in lowercase, even at the start of a sentence."),
    ("Visual Studio Code", "Refer to Visual Studio Code as VS Code after the first mention."),
    ("Windows", "Windows paths in examples use backslashes."),
    ("Linux", "Linux commands assume a bash shell."),
    ("Mozilla", "Link to the Mozilla Developer Network for web platform references."),
    ("Slack", "Screenshots of Slack must hide user names."),
    ("Mermaid", "Use Mermaid for diagrams instead of images."),
    ("Node.js", "Write Node.js with a capital N and a dot."),
    ("Terraform", "Terraform examples pin provider versions."),
    ("Stripe", "Name the Stripe dashboard pages exactly as Stripe does."),
]
EDITED = [i for i in range(len(RULES)) if i % 2 == 0]
UNTOUCHED = [i for i in range(len(RULES)) if i % 2 == 1]


def final_text(i: int) -> str:
    """The text rule i has at the end of the run (same in team A and team B)."""
    text = RULES[i][1]
    return text + SUFFIX if i in EDITED else text


def query_for(i: int) -> str:
    return f"What is our rule for {RULES[i][0]}?"


# ---------- pure helpers (tested offline in test_rawlink.py) ----------

def rows_of(listed: Any) -> List[Any]:
    """Mem0 vector-store list() returns [rows] or rows; mirror Mem0's own unpacking."""
    if isinstance(listed, (list, tuple)) and listed and isinstance(listed[0], list):
        return list(listed[0])
    return list(listed or [])


def linked_ids(rows: Iterable[Any]) -> Set[str]:
    """All memory ids named in entity-store rows' linked_memory_ids."""
    out: Set[str] = set()
    for row in rows:
        payload = getattr(row, "payload", None)
        if payload is None and isinstance(row, dict):
            payload = row.get("payload")
        linked = (payload or {}).get("linked_memory_ids") or []
        if isinstance(linked, list):
            out.update(str(x) for x in linked)
    return out


def score_for(items: List[Dict[str, Any]], memory_id: str) -> Optional[float]:
    for item in items:
        if str(item.get("id")) == str(memory_id):
            score = item.get("score")
            return float(score) if score is not None else None
    return None


def grade(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Apply the pre-registered gate and predictions P1-P4 to observations."""
    v: Dict[str, Any] = {}
    gate = bool(obs.get("spacy_loaded")) and obs.get("queries_with_entities", 0) >= 15
    v["gate"] = gate
    if not gate:
        v["status"] = "not graded (gate failed: spaCy model or entity extraction unavailable)"
        return v
    v["P1"] = obs.get("linked_after_adds", -1) == 0
    edited_linked = obs.get("edited_linked_after_update", 0)
    v["P2"] = (edited_linked >= 8 and obs.get("untouched_linked_after_update", -1) == 0
               and obs.get("team_b_linked", -1) == 0)
    deltas_e = [d for d in obs.get("delta_edited", []) if d is not None]
    deltas_u = [d for d in obs.get("delta_untouched", []) if d is not None]
    v["P3"] = len(deltas_e) == len(EDITED) and sum(1 for d in deltas_e if d > BOOST_MIN) >= 8
    v["P4"] = len(deltas_u) == len(UNTOUCHED) and sum(1 for d in deltas_u if abs(d) < SAME_MAX) >= 9
    v["status"] = "graded"
    return v


# ---------- the run ----------

def configure_env(base_dir: str) -> None:
    os.environ["MEM0_TELEMETRY"] = "False"
    os.environ["MEM0_DIR"] = os.path.join(base_dir, "mem0-home")
    os.environ["OPENAI_API_KEY"] = "placeholder-no-llm-calls"
    os.environ["OPENAI_BASE_URL"] = CLOSED_LLM_URL
    os.environ.pop("OPENROUTER_API_KEY", None)


def open_memory(base_dir: str):
    os.makedirs(base_dir, exist_ok=True)
    configure_env(base_dir)
    from mem0 import Memory
    return Memory.from_config({
        "vector_store": {"provider": "qdrant", "config": {
            "collection_name": "rules", "embedding_model_dims": DIMS,
            "path": os.path.join(base_dir, "qdrant"), "on_disk": True}},
        "embedder": {"provider": "fastembed", "config": {"model": MODEL, "embedding_dims": DIMS}},
        "history_db_path": os.path.join(base_dir, "history.db"),
    })


def add_raw(memory, user: str, text: str) -> str:
    res = memory.add([{"role": "user", "content": text}], user_id=user, infer=False)
    items = (res or {}).get("results") or []
    if len(items) != 1:
        raise RuntimeError(f"expected one memory, got {res!r}")
    return items[0]["id"]


def entity_linked(memory, user: str) -> Set[str]:
    listed = memory.entity_store.list(filters={"user_id": user}, top_k=10000)
    return linked_ids(rows_of(listed))


def search_scores(memory, user: str, query: str) -> List[Dict[str, Any]]:
    res = memory.search(query, top_k=len(RULES), filters={"user_id": user}, threshold=0.0)
    return list((res or {}).get("results") or [])


def run(work_dir: str) -> Dict[str, Any]:
    obs: Dict[str, Any] = {"tool": "rawlink", "version": __version__, "model": MODEL}
    try:
        from importlib import metadata
        obs["versions"] = {p: _ver(metadata, p) for p in
                           ("mem0ai", "spacy", "en-core-web-sm", "fastembed", "qdrant-client")}
    except Exception:
        obs["versions"] = {}

    from mem0.utils.spacy_models import get_nlp_full
    from mem0.utils.entity_extraction import extract_entities
    obs["spacy_loaded"] = get_nlp_full() is not None
    ents = {i: extract_entities(query_for(i)) for i in range(len(RULES))}
    obs["query_entities"] = {query_for(i): [list(e) for e in ents[i]] for i in ents}
    obs["queries_with_entities"] = sum(1 for i in ents if ents[i])

    llm_calls: List[int] = []

    def no_llm(*a, **k):
        llm_calls.append(1)
        raise AssertionError("an LLM call was attempted")

    memory = open_memory(os.path.join(work_dir, "store"))
    memory.llm.generate_response = no_llm

    ids_a = {i: add_raw(memory, USER_A, RULES[i][1]) for i in range(len(RULES))}
    ids_b = {i: add_raw(memory, USER_B, final_text(i)) for i in range(len(RULES))}

    linked_a = entity_linked(memory, USER_A)
    linked_b = entity_linked(memory, USER_B)
    obs["linked_after_adds"] = len((linked_a | linked_b) & (set(ids_a.values()) | set(ids_b.values())))

    # Scores before any edit (for the record; not graded).
    before = {i: score_for(search_scores(memory, USER_A, query_for(i)), ids_a[i]) for i in range(len(RULES))}

    for i in EDITED:
        memory.update(ids_a[i], text=final_text(i))

    linked_a = entity_linked(memory, USER_A)
    obs["edited_linked_after_update"] = sum(1 for i in EDITED if ids_a[i] in linked_a)
    obs["untouched_linked_after_update"] = sum(1 for i in UNTOUCHED if ids_a[i] in linked_a)
    obs["team_b_linked"] = len(entity_linked(memory, USER_B) & set(ids_b.values()))

    per_rule = []
    for i in range(len(RULES)):
        items_a = search_scores(memory, USER_A, query_for(i))
        items_b = search_scores(memory, USER_B, query_for(i))
        sa, sb = score_for(items_a, ids_a[i]), score_for(items_b, ids_b[i])
        rank_a = next((r for r, it in enumerate(items_a, 1) if str(it.get("id")) == str(ids_a[i])), None)
        rank_b = next((r for r, it in enumerate(items_b, 1) if str(it.get("id")) == str(ids_b[i])), None)
        per_rule.append({
            "i": i, "entity": RULES[i][0], "edited": i in EDITED, "query": query_for(i),
            "score_a_before_edit": before[i], "score_a": sa, "score_b": sb,
            "delta": (sa - sb) if (sa is not None and sb is not None) else None,
            "rank_a": rank_a, "rank_b": rank_b,
            "result_keys": sorted(items_a[0].keys()) if items_a else [],
        })
    obs["per_rule"] = per_rule
    obs["delta_edited"] = [r["delta"] for r in per_rule if r["edited"]]
    obs["delta_untouched"] = [r["delta"] for r in per_rule if not r["edited"]]
    obs["top1_a"] = sum(1 for r in per_rule if r["rank_a"] == 1)
    obs["top1_b"] = sum(1 for r in per_rule if r["rank_b"] == 1)
    obs["llm_calls"] = len(llm_calls)

    client = getattr(getattr(memory, "vector_store", None), "client", None)
    if client is not None and hasattr(client, "close"):
        client.close()
    return obs


def _ver(metadata, pkg):
    try:
        return metadata.version(pkg)
    except Exception:
        return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="out")
    parser.add_argument("--work-dir", default="")
    args = parser.parse_args(argv)
    os.makedirs(args.out_dir, exist_ok=True)
    work_dir = args.work_dir or tempfile.mkdtemp(prefix="rawlink-")
    obs: Dict[str, Any] = {}
    crash = None
    try:
        obs = run(work_dir)
    except Exception:
        crash = traceback.format_exc()
    verdicts = grade(obs) if crash is None else {"status": "crashed"}
    report = {"observations": obs, "verdicts": verdicts, "crash": crash}
    with open(os.path.join(args.out_dir, "observations.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    lines = [f"rawlink {__version__}: {verdicts.get('status')}"]
    for key in ("gate", "P1", "P2", "P3", "P4"):
        if key in verdicts:
            lines.append(f"{key}: {'HELD' if verdicts[key] else 'FAILED'}")
    for key in ("linked_after_adds", "edited_linked_after_update", "untouched_linked_after_update",
                "team_b_linked", "queries_with_entities", "top1_a", "top1_b", "llm_calls"):
        if key in obs:
            lines.append(f"{key} = {obs[key]}")
    if crash:
        lines.append("CRASH:\n" + crash)
    with open(os.path.join(args.out_dir, "RESULT.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if crash else 0


if __name__ == "__main__":
    sys.exit(main())
