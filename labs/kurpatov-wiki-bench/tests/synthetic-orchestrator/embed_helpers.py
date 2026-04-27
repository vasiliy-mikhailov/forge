#!/usr/bin/env python3
"""
embed_helpers.py — D8 Step 1-3 retrieval helpers.

Provides four CLI entrypoints (callable as `python3 embed_helpers.py <cmd>`):
  - encode <text>                     — output a JSON vector (debug)
  - rebuild <wiki_dir>                — full reindex of claims + concepts
  - update <wiki_dir> --source <slug> — incremental index for one source
  - find-claims <wiki_dir> --claim <text> [--k 5] [--threshold 0.65]
                                      — top-K nearest prior claims
  - find-concepts <wiki_dir> --slug-or-text <text> [--k 3] [--threshold 0.85]
                                      — concept dedup helper

Storage: numpy + sqlite hybrid in `wiki/data/embeddings/`:
  - claims.sqlite     (claims metadata: slug, idx, text, marker, url, ...)
  - claims.npz        (claims embeddings as a 2D numpy array, dim=768)
  - concepts.sqlite   (concepts metadata)
  - concepts.npz      (concepts embeddings)

Embedding model: intfloat/multilingual-e5-base (default; override
via EMBED_MODEL env var). e5 expects "query: " prefix on retrieval
queries and "passage: " prefix on stored documents — handled here.

We use numpy (linear cosine scan) instead of sqlite-vss because:
  - sqlite-vss requires libblas3 + libfaiss runtime (sudo on most Linux)
  - At 200 sources × 30 claims = 6 K vectors, brute-force cosine over
    a 768-dim normalized matrix is ~1 ms on CPU — same order as e5
    inference for the query itself.
  - numpy is already pulled in by sentence-transformers, no new deps.

Dependencies (ship via wiki/skills/benchmark/requirements.txt):
  sentence-transformers>=2.7
  numpy
  pyyaml>=6.0

Usage examples:
  # one-shot reindex on the wiki repo:
  python3 embed_helpers.py rebuild /path/to/wiki

  # called by source-author orchestrator after a source.md is written:
  python3 embed_helpers.py update /path/to/wiki --source "Course/Module/000 ..."

  # called by idea-classifier sub-agent for each claim:
  python3 embed_helpers.py find-claims /path/to/wiki \\
      --claim "В лимбической системе десятки ядер" --k 5 --threshold 0.65

  # called by concept-curator before creating a new concept:
  python3 embed_helpers.py find-concepts /path/to/wiki \\
      --slug-or-text "social-instinct" --k 3 --threshold 0.85
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Imports deferred to first use (sentence-transformers loads ~280 MB) ──

_model = None
_MODEL_NAME = os.environ.get("EMBED_MODEL", "intfloat/multilingual-e5-base")
_DIM = 768  # e5-base output dim

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model

def encode_passage(text: str) -> list[float]:
    """Encode a stored document. e5 expects 'passage:' prefix."""
    m = _get_model()
    vec = m.encode(f"passage: {text}", normalize_embeddings=True)
    return vec.tolist()

def encode_query(text: str) -> list[float]:
    """Encode a retrieval query. e5 expects 'query:' prefix."""
    m = _get_model()
    vec = m.encode(f"query: {text}", normalize_embeddings=True)
    return vec.tolist()


# ─── Schema and sqlite-vss bootstrap ─────────────────────────────────────

CLAIMS_SCHEMA = """\
CREATE TABLE IF NOT EXISTS claims (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  source_slug     TEXT NOT NULL,
  claim_idx       INTEGER NOT NULL,
  claim_text      TEXT NOT NULL,
  marker          TEXT NOT NULL,
  url             TEXT,
  thematic_category TEXT,
  notes           TEXT,
  indexed_at      TEXT NOT NULL,
  model_name      TEXT NOT NULL,
  UNIQUE (source_slug, claim_idx)
);
"""

CONCEPTS_SCHEMA = """\
CREATE TABLE IF NOT EXISTS concepts (
  rowid           INTEGER PRIMARY KEY AUTOINCREMENT,
  slug            TEXT UNIQUE NOT NULL,
  title           TEXT,
  definition      TEXT,
  introduced_in   TEXT,
  touched_by_json TEXT NOT NULL,
  indexed_at      TEXT NOT NULL,
  model_name      TEXT NOT NULL
);
"""

def _open_db(path: Path, schema_sql: str) -> sqlite3.Connection:
    """Open sqlite with metadata schema. Embeddings live in a sibling .npz."""
    conn = sqlite3.connect(str(path))
    conn.execute(schema_sql)
    conn.commit()
    return conn

def _embeddings_dir(wiki: Path) -> Path:
    d = wiki / "data" / "embeddings"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─── numpy embedding store ───────────────────────────────────────────────

def _load_npz(path: Path) -> tuple:
    """Load (ids, vectors) arrays. ids[i] maps to sqlite row id."""
    import numpy as np
    if not path.exists():
        return np.zeros((0,), dtype=np.int64), np.zeros((0, _DIM), dtype=np.float32)
    z = np.load(path)
    return z["ids"], z["vectors"]


def _save_npz(path: Path, ids, vectors):
    """Persist (ids, vectors) to .npz."""
    import numpy as np
    np.savez(path, ids=np.asarray(ids, dtype=np.int64),
             vectors=np.asarray(vectors, dtype=np.float32))


def _cosine_topk(query_vec, ids, vectors, k: int):
    """Linear cosine top-K over normalized vectors. Returns [(id, sim), ...]."""
    import numpy as np
    if len(ids) == 0:
        return []
    q = np.asarray(query_vec, dtype=np.float32)
    # vectors are already normalized (encode_passage uses normalize_embeddings=True)
    sims = vectors @ q  # cosine == dot for normalized
    top = np.argsort(-sims)[:k]
    return [(int(ids[i]), float(sims[i])) for i in top]


# ─── Frontmatter / claims parser (lifted from bench_grade) ───────────────

_FM_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)
_TOUCHED_BY_RE = re.compile(r"^touched_by:\s*\n((?:\s+-\s+.+\n)+)", re.MULTILINE)
_CLAIM_RE = re.compile(
    r"^(\d+)\.\s+(.+?)\s+\[(NEW|REPEATED[^\]]*|CONTRADICTS[\s_]+FACTS"
    r"|CONTRADICTS\s+EARLIER[^\]]*)\]\s*\n"
    r"((?:(?!\n\d+\.).)*?)"
    r"(?=\n\d+\.|\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_URL_RE = re.compile(r"https?://[^\s\)\]]+")

def parse_frontmatter(text: str) -> dict:
    m = _FM_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip() if v.strip() else None
    tb = _TOUCHED_BY_RE.search(m.group(1))
    if tb:
        fm["touched_by"] = [
            ln.strip().lstrip("- ").strip()
            for ln in tb.group(1).splitlines() if ln.strip()
        ]
    return fm

def parse_claims_section(text: str) -> list[dict]:
    """Returns list of {idx, text, marker, url, notes}."""
    m = re.search(r"^## Claims[^\n]*\n(.*?)(?=\n## |\Z)", text,
                  re.MULTILINE | re.DOTALL)
    if not m:
        return []
    body = m.group(1)
    out = []
    for cm in _CLAIM_RE.finditer(body):
        idx = int(cm.group(1))
        claim_text = cm.group(2).strip()
        marker = cm.group(3).strip()
        rest = cm.group(4).strip()
        # Extract URL if present in rest
        url_m = _URL_RE.search(rest)
        url = url_m.group(0) if url_m else None
        # Notes = rest minus URL
        notes = rest if rest else None
        out.append({
            "idx": idx, "text": claim_text, "marker": marker,
            "url": url, "notes": notes,
        })
    return out


# ─── Index operations ────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def index_source(wiki: Path, source_slug: str) -> int:
    """Re-index claims for one source.md. Returns number of claims indexed."""
    import numpy as np
    src_path = wiki / "data" / "sources" / f"{source_slug}.md"
    if not src_path.exists():
        raise FileNotFoundError(f"source not found: {src_path}")
    text = src_path.read_text()
    claims = parse_claims_section(text)
    if not claims:
        return 0

    edir = _embeddings_dir(wiki)
    db_path = edir / "claims.sqlite"
    npz_path = edir / "claims.npz"
    conn = _open_db(db_path, CLAIMS_SCHEMA)
    ids, vectors = _load_npz(npz_path)

    # Delete existing rows for this source (idempotent)
    cur = conn.execute("SELECT id FROM claims WHERE source_slug=?", (source_slug,))
    old_ids = set(r[0] for r in cur.fetchall())
    if old_ids:
        conn.executemany("DELETE FROM claims WHERE id=?", [(i,) for i in old_ids])
        # Filter old rows out of npz
        keep = [i for i, rid in enumerate(ids) if int(rid) not in old_ids]
        if len(keep) > 0:
            ids = ids[keep]; vectors = vectors[keep]
        else:
            ids = np.zeros((0,), dtype=np.int64)
            vectors = np.zeros((0, _DIM), dtype=np.float32)

    # Insert + embed
    new_ids = []
    new_vectors = []
    for c in claims:
        vec = encode_passage(c["text"])
        cur = conn.execute(
            "INSERT INTO claims "
            "(source_slug, claim_idx, claim_text, marker, url, "
            " thematic_category, notes, indexed_at, model_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source_slug, c["idx"], c["text"], c["marker"], c["url"],
             None, c["notes"], _now_iso(), _MODEL_NAME)
        )
        new_ids.append(cur.lastrowid)
        new_vectors.append(vec)

    if new_ids:
        ids = np.concatenate([ids, np.asarray(new_ids, dtype=np.int64)])
        vectors = np.concatenate([vectors, np.asarray(new_vectors, dtype=np.float32)])

    _save_npz(npz_path, ids, vectors)
    conn.commit()
    conn.close()
    return len(claims)


def index_concept(wiki: Path, concept_slug: str) -> int:
    """Re-index one concept. Returns 1 if indexed, 0 if not found."""
    import numpy as np
    cpt_path = wiki / "data" / "concepts" / f"{concept_slug}.md"
    if not cpt_path.exists() or concept_slug.startswith("_"):
        return 0
    text = cpt_path.read_text()
    fm = parse_frontmatter(text)
    title_m = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else concept_slug

    def_m = re.search(r"^## Definition\s*\n(.*?)(?=\n## |\Z)", text,
                      re.MULTILINE | re.DOTALL)
    definition = def_m.group(1).strip() if def_m else ""

    edir = _embeddings_dir(wiki)
    db_path = edir / "concepts.sqlite"
    npz_path = edir / "concepts.npz"
    conn = _open_db(db_path, CONCEPTS_SCHEMA)
    ids, vectors = _load_npz(npz_path)

    # Delete existing (idempotent)
    cur = conn.execute("SELECT rowid FROM concepts WHERE slug=?", (concept_slug,))
    old = cur.fetchone()
    if old:
        old_id = old[0]
        conn.execute("DELETE FROM concepts WHERE slug=?", (concept_slug,))
        keep = [i for i, rid in enumerate(ids) if int(rid) != old_id]
        if len(keep) > 0:
            ids = ids[keep]; vectors = vectors[keep]
        else:
            ids = np.zeros((0,), dtype=np.int64)
            vectors = np.zeros((0, _DIM), dtype=np.float32)

    embed_text = f"{concept_slug}\n\n{title}\n\n{definition}"
    vec = encode_passage(embed_text)
    cur = conn.execute(
        "INSERT INTO concepts (slug, title, definition, introduced_in, "
        "touched_by_json, indexed_at, model_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (concept_slug, title, definition, fm.get("introduced_in"),
         json.dumps(fm.get("touched_by", [])), _now_iso(), _MODEL_NAME)
    )
    new_id = cur.lastrowid
    ids = np.concatenate([ids, np.asarray([new_id], dtype=np.int64)])
    vectors = np.concatenate([vectors, np.asarray([vec], dtype=np.float32)])
    _save_npz(npz_path, ids, vectors)
    conn.commit()
    conn.close()
    return 1


def rebuild_index(wiki: Path) -> dict:
    """Full reindex from .md files. Returns counts."""
    # nuke and recreate
    edir = _embeddings_dir(wiki)
    for f in ("claims.sqlite", "claims.npz", "concepts.sqlite", "concepts.npz"):
        p = edir / f
        if p.exists(): p.unlink()

    n_claims = 0
    sources_dir = wiki / "data" / "sources"
    if sources_dir.exists():
        for src in sources_dir.rglob("*.md"):
            if src.stem.startswith("_"): continue
            slug = str(src.relative_to(sources_dir)).removesuffix(".md")
            n_claims += index_source(wiki, slug)

    n_concepts = 0
    concepts_dir = wiki / "data" / "concepts"
    if concepts_dir.exists():
        for cpt in concepts_dir.glob("*.md"):
            if cpt.stem.startswith("_"): continue
            n_concepts += index_concept(wiki, cpt.stem)

    return {
        "claims_indexed": n_claims,
        "concepts_indexed": n_concepts,
        "model": _MODEL_NAME,
        "indexed_at": _now_iso(),
    }


# ─── Retrieval ────────────────────────────────────────────────────────────

def find_similar_claims(wiki: Path, claim: str, k: int = 5,
                        threshold: float = 0.85,
                        module: str | None = None) -> dict:
    """Top-K nearest prior claims via numpy cosine over .npz."""
    edir = _embeddings_dir(wiki)
    db_path = edir / "claims.sqlite"
    npz_path = edir / "claims.npz"
    if not db_path.exists() or not npz_path.exists():
        return {"candidates": [], "k_requested": k, "k_returned": 0,
                "error": "index missing — run `rebuild` first"}

    qvec = encode_query(claim)
    ids, vectors = _load_npz(npz_path)
    if len(ids) == 0:
        return {"candidates": [], "k_requested": k, "k_returned": 0,
                "model": _MODEL_NAME}

    # over-fetch for module filter
    top = _cosine_topk(qvec, ids, vectors, k * 5)

    conn = _open_db(db_path, CLAIMS_SCHEMA)
    candidates = []
    below = 0
    for row_id, sim in top:
        if sim < threshold:
            below += 1
            continue
        cur = conn.execute(
            "SELECT source_slug, claim_idx, claim_text, marker, url, "
            "       thematic_category FROM claims WHERE id=?", (row_id,)
        ).fetchone()
        if not cur: continue
        source_slug, claim_idx, claim_text, marker, url, theme = cur
        if module and module not in source_slug:
            continue
        candidates.append({
            "source_slug": source_slug,
            "claim_idx": claim_idx,
            "claim_text": claim_text,
            "marker": marker,
            "url": url,
            "thematic_category": theme,
            "similarity": round(sim, 4),
        })
        if len(candidates) >= k:
            break
    conn.close()

    return {
        "candidates": candidates,
        "k_requested": k,
        "k_returned": len(candidates),
        "below_threshold": below,
        "model": _MODEL_NAME,
        "threshold": threshold,
    }


def find_similar_concepts(wiki: Path, slug_or_text: str, k: int = 3,
                          threshold: float = 0.92) -> dict:
    """Top-K nearest concepts via numpy cosine over .npz.

    Note: e5-base on Russian text gives baseline cosine ~0.80;
    paraphrase pairs are ~0.94. We use threshold 0.92 (tight) for
    concept dedup to avoid false-merges.
    """
    edir = _embeddings_dir(wiki)
    db_path = edir / "concepts.sqlite"
    npz_path = edir / "concepts.npz"
    if not db_path.exists() or not npz_path.exists():
        return {"candidates": [], "error": "index missing — run `rebuild` first"}

    qvec = encode_query(slug_or_text)
    ids, vectors = _load_npz(npz_path)
    if len(ids) == 0:
        return {"candidates": [], "k_requested": k, "k_returned": 0,
                "model": _MODEL_NAME}

    top = _cosine_topk(qvec, ids, vectors, k * 3)

    conn = _open_db(db_path, CONCEPTS_SCHEMA)
    candidates = []
    for row_id, sim in top:
        if sim < threshold:
            continue
        cur = conn.execute(
            "SELECT slug, title, definition, touched_by_json "
            "FROM concepts WHERE rowid=?", (row_id,)
        ).fetchone()
        if not cur: continue
        slug, title, definition, touched_by_json = cur
        candidates.append({
            "slug": slug,
            "title": title,
            "touched_by": json.loads(touched_by_json),
            "definition_preview": (definition or "")[:200],
            "similarity": round(sim, 4),
        })
        if len(candidates) >= k:
            break
    conn.close()

    return {
        "candidates": candidates,
        "k_requested": k,
        "k_returned": len(candidates),
        "model": _MODEL_NAME,
        "threshold": threshold,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("encode", help="encode text → vector (debug)")
    sp.add_argument("text")
    sp.add_argument("--query", action="store_true", help="use query prefix (else passage)")

    sp = sub.add_parser("rebuild", help="full reindex from .md files")
    sp.add_argument("wiki", type=Path)

    sp = sub.add_parser("update", help="incremental index for one source or concept")
    sp.add_argument("wiki", type=Path)
    sp.add_argument("--source", help="source slug")
    sp.add_argument("--concept", help="concept slug")

    sp = sub.add_parser("find-claims", help="top-K nearest prior claims")
    sp.add_argument("wiki", type=Path)
    sp.add_argument("--claim", required=True)
    sp.add_argument("--k", type=int, default=5)
    sp.add_argument("--threshold", type=float, default=0.65)
    sp.add_argument("--module", default=None,
                    help="optional module filter (substring)")

    sp = sub.add_parser("find-concepts", help="concept dedup helper")
    sp.add_argument("wiki", type=Path)
    sp.add_argument("--slug-or-text", required=True)
    sp.add_argument("--k", type=int, default=3)
    sp.add_argument("--threshold", type=float, default=0.85)

    args = p.parse_args()

    try:
        if args.cmd == "encode":
            vec = encode_query(args.text) if args.query else encode_passage(args.text)
            print(json.dumps({"dim": len(vec), "model": _MODEL_NAME,
                              "vec_preview": vec[:5] + ["..."] + vec[-2:]}))
        elif args.cmd == "rebuild":
            r = rebuild_index(args.wiki)
            print(json.dumps(r, indent=2))
        elif args.cmd == "update":
            if args.source:
                n = index_source(args.wiki, args.source)
                print(json.dumps({"action": "index_source", "source": args.source,
                                  "claims_indexed": n}))
            elif args.concept:
                n = index_concept(args.wiki, args.concept)
                print(json.dumps({"action": "index_concept", "concept": args.concept,
                                  "indexed": n}))
            else:
                print("ERROR: --source or --concept required", file=sys.stderr)
                sys.exit(2)
        elif args.cmd == "find-claims":
            r = find_similar_claims(args.wiki, args.claim, k=args.k,
                                    threshold=args.threshold, module=args.module)
            print(json.dumps(r, ensure_ascii=False, indent=2))
        elif args.cmd == "find-concepts":
            r = find_similar_concepts(args.wiki, args.slug_or_text,
                                      k=args.k, threshold=args.threshold)
            print(json.dumps(r, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}),
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
