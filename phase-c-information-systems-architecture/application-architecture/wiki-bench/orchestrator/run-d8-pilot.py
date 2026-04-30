"""
D8 pilot production orchestrator — module 005 of "Психолог-консультант".

Ports the validated step7 architecture to production, with retrieval
plugged in (D8 Steps 4-7):
  - Python `for` loop top-orchestrator (Invariant A — bounded context)
  - Canonical skill v2 concept shape (Invariant B — `## Contributions
    by source` + per-touched-by `### <slug>` sub-sections)
  - source-author extracts excerpt+timestamp_sec from whisper segments
  - Per-source git commit on success (each source = its own commit)
  - Fail-fast on first verify=fail
  - Retrieval-augmented dedup (claims): orchestrator rebuilds
    embed_helpers index before each source; source-author calls
    find-claims per-claim and feeds top-K candidates to
    idea-classifier (replaces bulk prior_claims_json that didn't
    scale past ~7 sources).
  - Retrieval-augmented dedup (concepts): source-author also calls
    find-concepts per concept_touched slug to canonicalise it
    against the existing concept index (threshold ≥ 0.85). Closes
    the concept-count gap by collapsing near-synonym slugs into
    one canonical slug + one concept file.

Validated on synth (step7_orchestrator.py): 4/4 verified=ok,
claims=21, REPEATED=7, CF=2, urls=12, top-orch events=5-6 per source,
6/6 concepts pass template v3.

Cyrillic paths preserved. Wikipedia rate-limit mitigated via
identifiable User-Agent + selective fact-check.

Usage:
  python3 orchestrator/run-d8-pilot.py
Env:
  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL — vLLM config
  GITHUB_TOKEN — for git push (via gh auth)
  D8_PILOT_WORKDIR (optional) — default /tmp/d8-pilot-prod
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

# Per ADR 0013 — Python coordinator replaces the source-author agent
# monolith. The coordinator owns workflow control and uses litellm for
# per-step structured LLM calls, so the OpenHands SDK Agent/Conversation
# stack is no longer used by the per-source loop.
sys.path.insert(0, str(Path(__file__).parent))
from source_coordinator import (
    SourceCoordinator, CoordinatorError, MalformedResponseError,
)
import litellm


# ─── Configuration ───────────────────────────────────────────────────────

WORKDIR = Path(os.environ.get("D8_PILOT_WORKDIR", "/tmp/d8-pilot-prod"))
RAW_REPO = "kurpatov-wiki-raw"
WIKI_REPO = "kurpatov-wiki-wiki"
GH_USER = "vasiliy-mikhailov"
SKILL_BRANCH = "skill-v2"
COURSE = os.environ.get("D8_PILOT_COURSE", "Психолог-консультант")
MODULE = os.environ.get("D8_PILOT_MODULE", "005 Природа внутренних конфликтов. Базовые психологические потребности")

# bench_grade.py path: container has it baked at /opt/forge/, host venv runs use the repo path.
BENCH_GRADE = (
    "/opt/forge/bench_grade.py" if Path("/opt/forge/bench_grade.py").exists()
    else "/home/vmihaylov/forge/labs/wiki-bench/evals/grade/bench_grade.py"
)






# ─── Helpers ──────────────────────────────────────────────────────────────

def run_cmd(cmd, cwd=None, check=True):
    print(f"[cmd] {cmd}", file=sys.stderr)
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if r.stdout: print(r.stdout, file=sys.stderr)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        if check: raise RuntimeError(f"command failed: {cmd}")
    return r


def _renormalise_to_nfc(root: Path) -> int:
    """Walk `root` bottom-up; rename any directory entry whose name is not in
    Unicode NFC to its NFC equivalent. Returns the rename count.

    Implements ADR 0011 M1 (cross-platform path normalisation): forge canonical
    form is NFC. macOS-origin data ships NFD; the LLM tokenizer cannot preserve
    NFD bytes through tokens, so the agent's file_editor and bash commands
    always emit NFC. If the on-disk filesystem is NFD, every agent action
    fails with "No such file or directory". We solve this once at clone time
    by renaming NFD entries to NFC; the agent and verify_source then operate
    in a single canonical form (NFC) for the rest of the run.
    """
    import unicodedata
    renamed = 0
    for d, dirs, files in os.walk(root, topdown=False):
        for n in files + dirs:
            target = unicodedata.normalize("NFC", n)
            if target != n:
                src = os.path.join(d, n)
                dst = os.path.join(d, target)
                if os.path.exists(dst):
                    # Two entries with same NFC form. Surface, do not silently
                    # collide — that's a data integrity hazard.
                    raise RuntimeError(
                        f"NFC rename collision under {root}: "
                        f"{src!r} would clobber existing {dst!r}"
                    )
                os.rename(src, dst)
                renamed += 1
    return renamed


def setup_workspace():
    # Clean *contents* of WORKDIR rather than the directory itself —
    # avoids EBUSY on mount points (containers).
    WORKDIR.mkdir(parents=True, exist_ok=True)
    skip_clone = os.environ.get("D8_PILOT_SKIP_CLONE", "").lower() in ("1", "true", "yes")
    if skip_clone:
        # Synth mode — caller pre-populated WORKDIR/raw and WORKDIR/wiki.
        if not (WORKDIR / "raw").exists() or not (WORKDIR / "wiki").exists():
            raise RuntimeError(f"D8_PILOT_SKIP_CLONE set but {WORKDIR}/raw or /wiki missing")
        # ADR 0011 M1 — renormalise to NFC even in SKIP_CLONE mode. Synth
        # fixtures preserve NFD on purpose (per fidelity rules) but the
        # orchestrator's contract is NFC, so we normalise in-place at the
        # boundary. The fixture stays NFD-faithful pre-orchestrator.
        renamed_raw = _renormalise_to_nfc(WORKDIR / "raw")
        renamed_wiki = _renormalise_to_nfc(WORKDIR / "wiki")
        if renamed_raw or renamed_wiki:
            print(f"[setup] NFC normalised {renamed_raw} entries in raw, "
                  f"{renamed_wiki} in wiki", file=sys.stderr)
        served = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8").replace("openai/", "")
        user_email = os.environ.get("GIT_AUTHOR_EMAIL", "bench@wiki-bench.local")
        user_name = os.environ.get("GIT_AUTHOR_NAME", "wiki-bench")
        subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)
        subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)
        # Mark workspace as a safe directory in case docker uid != git tree owner.
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=False)
        branch = os.environ.get("D8_PILOT_BRANCH", f"synth-test-{date.today().isoformat()}-{served}")
        run_cmd(f"cd wiki && git checkout -B {branch} 2>&1 || true", cwd=str(WORKDIR), check=False)
        print(f"[setup] SKIP_CLONE mode — using pre-populated {WORKDIR}; branch={branch}", file=sys.stderr)
        return branch, served

    if any(WORKDIR.iterdir()):
        print(f"[setup] cleaning existing contents of {WORKDIR}", file=sys.stderr)
        for child in WORKDIR.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()

    # git author identity for in-container commits — env vars or fallback.
    user_email = os.environ.get("GIT_AUTHOR_EMAIL", "bench@wiki-bench.local")
    user_name = os.environ.get("GIT_AUTHOR_NAME", "wiki-bench")
    subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)
    subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)

    # GitHub token: env first (canonical for containers), then `gh` CLI fallback (host).
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    if not token:
        raise RuntimeError("no GITHUB_TOKEN env nor `gh auth token` available")
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{RAW_REPO}.git raw", cwd=str(WORKDIR))
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{WIKI_REPO}.git wiki", cwd=str(WORKDIR))
    run_cmd(f"cd wiki && git checkout {SKILL_BRANCH} && git pull --ff-only", cwd=str(WORKDIR))

    # ADR 0011 M1 — renormalise filenames in raw and wiki to forge canonical
    # NFC. macOS-origin scrapes (kurpatov-wiki-raw) ship NFD entries; we MUST
    # rewrite them to NFC before any agent or list_sources.py touches them.
    # Without this, the LLM's NFC-only token output collides with NFD on disk.
    # Renames are scoped to the freshly-cloned WORKDIR, so they do not affect
    # the upstream git repos.
    renamed_raw = _renormalise_to_nfc(WORKDIR / "raw")
    renamed_wiki = _renormalise_to_nfc(WORKDIR / "wiki")
    if renamed_raw or renamed_wiki:
        print(f"[setup] ADR 0011 M1 — NFC renamed: raw={renamed_raw}, wiki={renamed_wiki}",
              file=sys.stderr)

    # Optional: strip the legacy module 005 baseline so the wiki only
    # contains content this run produces. The skill-v2 baseline shipped
    # with English-named module 005 sources + concepts (predates ADR
    # 0013's language contract). For a publishable single-language wiki,
    # delete that baseline at setup time. Trade-off: lose cross-module
    # REPEATED detection against module 005 content. Set
    # D8_PILOT_STRIP_BASELINE=1 to enable.
    if os.environ.get("D8_PILOT_STRIP_BASELINE", "").lower() in ("1", "true", "yes"):
        wiki = WORKDIR / "wiki"
        sources_root = wiki / "data" / "sources"
        concepts_root = wiki / "data" / "concepts"
        deleted_sources = 0
        deleted_concepts = 0
        # Delete pre-existing module 005 source dirs.
        for course_dir in sources_root.iterdir() if sources_root.exists() else []:
            if not course_dir.is_dir():
                continue
            for module_dir in course_dir.iterdir():
                if not module_dir.is_dir():
                    continue
                if module_dir.name.startswith("005 "):
                    shutil.rmtree(module_dir)
                    deleted_sources += 1
        # Delete every pre-existing concept file (they'll be rebuilt by
        # the coordinator from the run's claims).
        if concepts_root.exists():
            for f in concepts_root.glob("*.md"):
                f.unlink()
                deleted_concepts += 1
        # Also drop the embeddings index — it would otherwise still
        # match against the deleted content.
        emb_dir = wiki / "data" / "embeddings"
        if emb_dir.exists():
            shutil.rmtree(emb_dir)
        # Drop concept-index too — coordinator will rebuild.
        ci = wiki / "data" / "concept-index.json"
        if ci.exists():
            ci.unlink()
        print(f"[setup] D8_PILOT_STRIP_BASELINE — deleted {deleted_sources} "
              f"module-005 source dirs + {deleted_concepts} concept files "
              f"+ embeddings + concept-index", file=sys.stderr)
        # Commit the strip so the experiment branch starts from a clean state.
        run_cmd("cd wiki && git add -A && "
                "git commit -m 'strip legacy module 005 baseline (D8_PILOT_STRIP_BASELINE)' "
                "|| true", cwd=str(WORKDIR), check=False)

    served = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8").replace("openai/", "")
    branch = os.environ.get("D8_PILOT_BRANCH", f"experiment/D8-pilot-{date.today().isoformat()}-{served}")
    print(f"[setup] experiment branch: {branch}", file=sys.stderr)

    run_cmd(f"cd wiki && git push origin --delete {branch} 2>&1 || true", cwd=str(WORKDIR), check=False)
    run_cmd(f"cd wiki && git checkout -b {branch} && git push -u origin {branch}", cwd=str(WORKDIR))
    return branch, served


def list_sources():
    # Multi-module support: D8_PILOT_MODULES is a pipe-separated list of
    # module names. Falls back to single MODULE if unset.
    modules_env = os.environ.get('D8_PILOT_MODULES', '').strip()
    if modules_env:
        modules = [m.strip() for m in modules_env.split('|') if m.strip()]
    else:
        modules = [MODULE]

    sources = []
    for m in modules:
        r = run_cmd(
            f"python3 wiki/skills/benchmark/list_sources.py {repr(COURSE)} {repr(m)}",
            cwd=str(WORKDIR),
        )
        data = json.loads(r.stdout)
        if isinstance(data, dict) and 'error' in data:
            raise RuntimeError(f"list_sources.py: {data['error']}")
        # All sources of this module, sorted by index.
        in_module = [s for s in data if m in s.get('slug', '')]
        in_module.sort(key=lambda s: s.get('index', 10**9))
        sources.extend(in_module)

    # Renumber index globally so per-source state keys are unique across
    # modules. The orchestrator's SRC N tag becomes the global position.
    for new_idx, s in enumerate(sources):
        s['original_index'] = s.get('index', -1)
        s['index'] = new_idx

    # Optional source-count cap for small-N pilots (e.g. G3 quality probe).
    limit_str = os.environ.get('D8_PILOT_SOURCES_LIMIT')
    if limit_str:
        n = int(limit_str)
        original_n = len(sources)
        sources = sources[:n]
        print(f'[list_sources] D8_PILOT_SOURCES_LIMIT={n} → returning {len(sources)} of {original_n} sources', flush=True)
    print(f'[list_sources] modules={modules} → {len(sources)} sources', flush=True)
    return sources


def build_inputs(sources):
    inputs = []
    for s in sources:
        n = s["index"]
        original_n = s.get("original_index", n)
        abs_raw = s["raw_json_path"]
        prefix = str(WORKDIR) + "/"
        if not abs_raw.startswith(prefix):
            raise RuntimeError(f"unexpected raw_json_path: {abs_raw}")
        raw_path = abs_raw[len(prefix):]
        target_path = f"wiki/data/sources/{s['slug']}.md"
        # Module subdir + stem derived from slug = Course/Module/<stem>.
        slug_parts = s["slug"].split("/")
        module_subdir = "/".join(slug_parts[:2]) if len(slug_parts) >= 2 else ""
        stem = slug_parts[-1] if slug_parts else s["slug"]
        inputs.append((n, original_n, module_subdir, stem, raw_path, target_path, s["slug"]))
    return inputs


def verify_source(n, original_n=None, module_subdir="", stem="", deadline_secs=90.0):
    """Verify a per-source artifact. Two phases:

    1. **Existence poll** — wait for the target source.md to appear
       on disk (up to 30 s, 500 ms cadence). Required because the
       agent's file_editor signals completion to the agent loop
       before close() durably propagates; without this we got
       intermittent "no source file matching" verdicts on files
       that landed seconds later. We poll the exact path rather
       than re-running the whole bench_grade rglob each time.
    2. **Structural grade** — run bench_grade.py ONCE for
       per-source contract checks (frontmatter, sections, claims).
       No retry here; if the file is on disk and grade fails,
       that's a real structural problem, not a timing one.
    """
    if stem and module_subdir:
        target = WORKDIR / "wiki" / "data" / "sources" / module_subdir / f"{stem}.md"
    else:
        target = None  # legacy path — no existence pre-check

    def _resolve_nfc_tolerant(p: Path) -> Path:
        """Belt-and-suspenders for ADR 0011: if the literal path doesn't exist
        but a sibling whose name NFC-normalises to the same string does, return
        that sibling. With M1 in place this should never fire — but if any
        future code path leaks an NFD entry into the wiki, this keeps the
        verifier from reporting a phantom verify-fail."""
        import unicodedata
        if p.exists() or not p.parent.exists():
            return p
        target_nfc = unicodedata.normalize("NFC", p.name)
        for entry in p.parent.iterdir():
            if unicodedata.normalize("NFC", entry.name) == target_nfc:
                if entry.name != p.name:
                    print(f"[verify_source] NFC-tolerant match: {p.name!r} → "
                          f"{entry.name!r} (ADR 0011 belt-and-suspenders)",
                          file=sys.stderr)
                return p.parent / entry.name
        return p

    if target is not None:
        target = _resolve_nfc_tolerant(target)
        # Two-stage poll:
        #   stage 1 (existence) — wait until target.exists() AND size > 0;
        #   stage 2 (stability)  — wait until (size, mtime) unchanged
        #     across two consecutive 500ms-spaced samples. This catches
        #     partial writes (size growing) and rewrites (mtime changing).
        # Total deadline 30s for both stages.
        deadline = time.monotonic() + deadline_secs
        # stage 1
        appeared = False
        iter_count = 0
        first_status = None
        last_status = None
        while time.monotonic() < deadline:
            iter_count += 1
            # Re-resolve each iteration so a file that lands at the NFC
            # variant after the first miss is found on the next poll.
            target = _resolve_nfc_tolerant(target)
            try:
                st = target.stat()
                last_status = f"size={st.st_size} mtime={st.st_mtime}"
                if first_status is None:
                    first_status = last_status
                if st.st_size > 0:
                    appeared = True
                    break
            except FileNotFoundError as e:
                last_status = f"FileNotFoundError: {e}"
                if first_status is None:
                    first_status = last_status
            time.sleep(0.5)
        if not appeared:
            # Diagnostic — what was the file like during the poll?
            try:
                parent = target.parent
                parent_listing = list(parent.iterdir()) if parent.exists() else []
                parent_listing_str = [p.name for p in parent_listing]
            except Exception as e:
                parent_listing_str = f"ERR: {e}"
            return {"verified": "fail",
                    "violations": [
                        f"source.md did not appear at {target} within {deadline_secs:.0f}s — agent likely did not write the file",
                        f"diag: iter_count={iter_count} first={first_status} last={last_status}",
                        f"diag: parent_exists={target.parent.exists()} parent_listing={parent_listing_str!r}",
                    ]}

        # stage 2 — wait for stability (same size+mtime across two samples)
        prev = (-1, -1.0)
        stable = False
        while time.monotonic() < deadline:
            try:
                st = target.stat()
                cur = (st.st_size, st.st_mtime)
            except FileNotFoundError:
                cur = (-1, -1.0)
            if cur == prev and cur[0] > 0:
                stable = True
                break
            prev = cur
            time.sleep(0.5)
        if not stable:
            return {"verified": "fail",
                    "violations": [f"source.md at {target} never stabilised within {deadline_secs:.0f}s (size or mtime kept changing) — agent may still be writing or repeatedly rewriting"]}

    cmd = ["python3", BENCH_GRADE, str(WORKDIR / "wiki"), "--single-source-json"]
    if stem:
        cmd += ["--single-source-stem", stem]
    else:
        src_n_for_grade = original_n if original_n is not None else n
        cmd += ["--single-source", str(src_n_for_grade)]
    if module_subdir:
        cmd += ["--module-subdir", module_subdir]

    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        # Empty/non-JSON stdout almost always means bench_grade.py crashed or
        # rejected its argv (argparse errors → empty stdout, error to stderr).
        # Surface stderr + the cmd so the operator can act on it instead of
        # debugging a phantom verify-fail.
        return {"verified": "fail",
                "violations": [
                    f"non-JSON: stdout={r.stdout[:200]!r}",
                    f"stderr={r.stderr[:400]!r}",
                    f"exit={r.returncode}",
                    f"cmd={cmd}",
                ]}


def commit_and_push_per_source(n, slug, branch):
    msg = f"source: {slug}"
    run_cmd("git add -A", cwd=str(WORKDIR / "wiki"))
    diff_r = subprocess.run("git diff --cached --quiet", shell=True, cwd=str(WORKDIR / "wiki"))
    if diff_r.returncode == 0:
        print(f"[commit] no changes for source {n}", file=sys.stderr)
        return None
    run_cmd(f'git commit -m "{msg}"', cwd=str(WORKDIR / "wiki"))
    run_cmd(f"git push origin {branch}", cwd=str(WORKDIR / "wiki"))
    sha = subprocess.run("git rev-parse --short HEAD", shell=True, cwd=str(WORKDIR / "wiki"),
                         capture_output=True, text=True).stdout.strip()
    return sha


def record_per_source_outcome(state, n, slug, verify_result, policy="fail_fast"):
    """Append a per-source state entry and decide whether the
    orchestrator's main loop should stop or continue.

    state            — list to append the entry to (mutated).
    n, slug          — source identification.
    verify_result    — dict from verify_source.
    policy           — "fail_fast" (default; legacy v5 behavior:
                       stop on first verify-fail) or "continue"
                       (K1 behavior: log fail, keep processing).

    Returns "stop" if the loop should break, "continue" otherwise.

    Either policy records the failure to state with stopped="verify_fail"
    so post-pilot grading can see what went wrong; the difference is only
    in whether the loop terminates.
    """
    entry = {"n": n, "slug": slug, "verify": verify_result}
    if verify_result.get("verified") == "ok":
        state.append(entry)
        return "continue"
    # verify=fail — record stopped reason regardless of policy
    entry["stopped"] = "verify_fail"
    state.append(entry)
    if policy == "continue":
        return "continue"
    return "stop"


# ─── Coordinator wiring (ADR 0013) ─────────────────────────────────────


def _make_coordinator_llm():
    """Return a callable for SourceCoordinator that wraps litellm.completion
    with response_format=json_schema. Reads LLM config from the same env
    vars the OpenHands LLM uses."""
    base_url = os.environ.get("LLM_BASE_URL", "https://inference.mikhailov.tech/v1")
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8")

    def llm(*, prompt, response_format, max_tokens):
        rf = {
            "type": "json_schema",
            "json_schema": {
                "name": response_format["title"],
                "schema": response_format["schema"],
                "strict": True,
            },
        }
        try:
            resp = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=rf,
                max_tokens=max_tokens,
                api_base=base_url,
                api_key=api_key,
                timeout=120.0,
            )
        except Exception as e:
            # Pass-through to coordinator's retry logic — return string,
            # which fails schema validation and triggers the retry path.
            return f"litellm error: {type(e).__name__}: {e}"
        content = resp.choices[0].message.content
        try:
            return json.loads(content)
        except Exception:
            return content
    return llm


def _make_retriever(embed_helpers_path: str, workdir_wiki: Path):
    """Return a retriever callable that subprocesses to embed_helpers
    find-claims and parses the result. Returns [] on any error so the
    coordinator can still classify (without prior-art context)."""
    def retrieve(claim_text: str) -> list[dict]:
        try:
            r = subprocess.run(
                ["python3", embed_helpers_path, "find-claims",
                 str(workdir_wiki), "--claim", claim_text,
                 "--k", "5", "--threshold", "0.65"],
                capture_output=True, text=True, timeout=20.0,
            )
            if r.returncode != 0:
                return []
            data = json.loads(r.stdout)
            cands = data.get("candidates", [])
            # Normalise field names so the coordinator's prompt formatter
            # gets `score`, `source_slug`, `claim_text`.
            for c in cands:
                if "score" not in c and "similarity" in c:
                    c["score"] = c["similarity"]
            return cands
        except Exception:
            return []
    return retrieve


def _make_concept_curator(workdir: Path):
    """Concept curator that writes a richly-content'd concept.md per
    concept slug. The coordinator generates definition + per-source
    contribution + related_concepts via batched LLM calls (per ADR 0013
    Quality contract step #15) and passes them in concept_data; this
    function just writes the file. Falls back to claim-text dump if the
    LLM content is missing (test stubs)."""
    concepts_dir = workdir / "wiki" / "data" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    def _xref_lines(related: list[str]) -> list[str]:
        if not related:
            return []
        return [
            "## Related concepts",
            "",
            "\n".join(
                f"- [{slug}](./{slug}.md)" for slug in related
                if slug and isinstance(slug, str)
            ),
        ]

    def curator(concept_slug: str, source_slug: str,
                concept_data: dict | None = None):
        path = concepts_dir / f"{concept_slug}.md"
        cd = concept_data or {}
        claims = cd.get("claims", [])
        claim_texts = [c.get("text", "").strip() for c in claims if c.get("text")]
        # Prefer LLM-generated definition + contribution; fall back to
        # claim text only if absent (test stubs / coordinator bypass).
        definition = (cd.get("definition") or "").strip()
        contribution = (cd.get("contribution") or "").strip()
        related = cd.get("related_concepts") or []
        if not definition:
            definition = claim_texts[0] if claim_texts else (
                f"_(no claim text available for slug {concept_slug!r})_"
            )
        if not contribution:
            if claim_texts:
                contribution = (
                    "В этом источнике обсуждаются следующие положения, "
                    "относящиеся к этому концепту:\n\n"
                    + "\n".join(f"- {t}" for t in claim_texts)
                )
            else:
                contribution = ("_(no specific claims classified under this "
                                "concept for this source)_")
        contrib_block = (
            f"### {source_slug}\n\n"
            f"{contribution}\n"
        )
        if path.exists():
            body = path.read_text(encoding="utf-8")
            if f"- {source_slug}" not in body:
                body = re.sub(
                    r"(touched_by:\n(?:  - .+\n)+)",
                    lambda m: m.group(1) + f"  - {source_slug}\n",
                    body, count=1,
                )
            if f"### {source_slug}" not in body:
                # Insert before "## Related concepts" if present, else append.
                if "## Related concepts" in body:
                    body = body.replace(
                        "## Related concepts",
                        contrib_block + "\n## Related concepts",
                        1,
                    )
                else:
                    body = body.rstrip() + "\n\n" + contrib_block
            path.write_text(body, encoding="utf-8")
            return
        # First introduction of this concept — write a fresh file.
        parts = [
            "---",
            f"slug: {concept_slug}",
            f"first_introduced_in: {source_slug}",
            f"touched_by:\n  - {source_slug}",
            "---",
            f"# {concept_slug}",
            "",
            "## Definition",
            "",
            definition,
            "",
            "## Contributions by source",
            "",
            contrib_block.rstrip(),
        ]
        xref = _xref_lines(related)
        if xref:
            parts.append("")
            parts.extend(xref)
        path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return curator


# Back-compat alias — older code paths reference the old name.
_make_stub_curator = _make_concept_curator


_FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)
_TOUCHED_BY_RE = re.compile(r"^touched_by:\s*\n((?:\s+-\s+.+\n)+)", re.MULTILINE)
_BULLET_RE = re.compile(
    r"^- \[([^\]]+)\]\((\.\./sources/[^)]+)\)\s*"
    r"(.+?)(?=\n- \[|\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_frontmatter(text):
    m = _FRONTMATTER_RE.match(text)
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


def validate_concept_v3(concept_path):
    """Canonical skill v2 concept shape (matches bench_grade.py L1.5):

      ## Definition
      ## Contributions by source
        ### <source-slug 1>
          - bullets …
          - See [<short title>](../sources/<slug>.md). [optional mm:ss]
        ### <source-slug 2>
          - …
      ## Related concepts
    """
    violations = []
    name = concept_path.name
    if name == "_template.md":
        return violations
    text = concept_path.read_text()
    fm = parse_frontmatter(text)
    touched_by = fm.get("touched_by", [])
    if not touched_by:
        violations.append(f"{name}: touched_by empty/missing")
        return violations
    if "## Definition" not in text:
        violations.append(f"{name}: ## Definition heading missing")
    if "## Contributions by source" not in text:
        violations.append(f"{name}: ## Contributions by source heading missing")
        return violations
    contrib_match = re.search(
        r"^## Contributions by source\s*\n(.*?)(?=\n## |\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    contrib_section = contrib_match.group(1) if contrib_match else ""
    sub_headings = re.findall(r"^### (.+)$", contrib_section, re.MULTILINE)
    sub_set = {h.strip() for h in sub_headings}
    for slug in touched_by:
        if slug not in sub_set:
            violations.append(
                f"{name}: touched_by '{slug[:60]}…' has no "
                f"### sub-section in Contributions by source"
            )
    if "## Related concepts" not in text:
        violations.append(f"{name}: ## Related concepts heading missing")
    return violations


# ─── Bench report ──────────────────────────────────────────────────────

def write_bench_report(state, branch, partial=False):
    report = WORKDIR / "wiki" / "bench-report.md"
    lines = [f"# bench report — D8 pilot {'(partial)' if partial else ''}",
             "", f"branch: `{branch}`",
             f"sources processed: {len(state)}/7",
             "",
             "## Architectural invariants",
             "",
             "- INVARIANT B (concept template v3): see concept_violations row",
             "",
             "## Per-source", ""]
    for entry in state:
        v = entry.get("verify", {})
        m = entry.get("coord_metrics", {})
        lines.append(
            f"- source {entry['n']}: verified={v.get('verified','?')}, "
            f"claims={v.get('claims_total','?')} "
            f"(NEW={v.get('claims_NEW','?')}, "
            f"REPEATED={v.get('claims_REPEATED','?')}, "
            f"CF={v.get('claims_CF','?')}, "
            f"unmarked={v.get('claims_unmarked','?')}), "
            f"urls={v.get('wiki_url_count','?')}, "
            f"coord_wall={m.get('wall_min','?')}min, "
            f"commit={entry.get('commit','?')}"
        )
    lines.append("")
    if partial:
        lines.append("## Stop point\n\nRun stopped fail-fast at first failure.")
    report.write_text("\n".join(lines))


def main():
    print("=" * 70, file=sys.stderr)
    print("D8 pilot production orchestrator (Python-loop top-orch + concept v3)", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    branch, served = setup_workspace()
    sources = list_sources()
    print(f"[main] {len(sources)} sources in module 005", file=sys.stderr)
    if not sources:
        print("FATAL: no sources found", file=sys.stderr); sys.exit(2)

    inputs = build_inputs(sources)

    resume_from = int(os.environ.get('D8_PILOT_RESUME_FROM', '0'))
    if resume_from > 0:
        original_count = len(inputs)
        inputs = [t for t in inputs if t[0] >= resume_from]
        print(f'[main] D8_PILOT_RESUME_FROM={resume_from} \u2192 {len(inputs)}/{original_count} sources to process', file=sys.stderr)

    # The coordinator (ADR 0013) talks to vLLM directly via litellm \u2014
    # no OpenHands SDK Agent/Conversation in the per-source loop.
    coordinator_llm = _make_coordinator_llm()

    # ─── Python-loop top-orchestrator (per-source coordinator) ─────
    state = []
    stopped_at = None
    t0_total = time.time()

    fail_policy = os.environ.get("D8_PILOT_FAIL_POLICY", "fail_fast")
    if fail_policy not in ("fail_fast", "continue"):
        raise RuntimeError(f"D8_PILOT_FAIL_POLICY must be \"fail_fast\" or \"continue\"; got {fail_policy!r}")
    print(f"[main] fail_policy={fail_policy}", file=sys.stderr)

    # Resolve embed_helpers.py path (container-baked vs host).
    embed_helpers_path = (
        "/opt/forge/embed_helpers.py"
        if Path("/opt/forge/embed_helpers.py").exists()
        else "/home/vmihaylov/forge/labs/wiki-bench/orchestrator/embed_helpers.py"
    )

    for (n, original_n, module_subdir, stem, raw_path, target_path, slug) in inputs:
        print(f"\n{'=' * 70}", file=sys.stderr)
        print(f"=== SRC {n}: {slug}", file=sys.stderr)
        print(f"{'=' * 70}", file=sys.stderr)

        # ── Rebuild retrieval index over committed sources (every prior
        # source.md + concept.md is now embedded). For source 0 the
        # index will be empty; for source N≥1 it covers sources 0..N-1.
        # The source-author calls find-claims via embed_helpers.py.
        print(f"[retrieval] rebuilding index before SRC {n}…", file=sys.stderr)
        rebuild_r = subprocess.run(
            ["python3", embed_helpers_path, "rebuild", str(WORKDIR / "wiki")],
            capture_output=True, text=True,
        )
        if rebuild_r.returncode != 0:
            print(f"!!! retrieval rebuild failed before SRC {n}: "
                  f"{rebuild_r.stderr[:400]}", file=sys.stderr)
            stopped_at = n
            state.append({"n": n, "slug": slug,
                          "stopped": "retrieval_rebuild_fail"})
            break
        else:
            print(f"[retrieval] {rebuild_r.stdout.strip()}", file=sys.stderr)

        # ─── Per-source via Python coordinator (ADR 0013) ────────────
        # Replaces the source-author agent monolith with deterministic
        # Python workflow + per-step structured LLM calls. The class of
        # "agent claimed done but didn't write the file" is structurally
        # impossible: the coordinator either calls write_text or raises
        # CoordinatorError. No SDK-side silent acceptance can happen
        # because there is no SDK in the per-source loop.
        coord = SourceCoordinator(llm=coordinator_llm, workdir=WORKDIR)
        coord_curator = _make_concept_curator(WORKDIR)
        coord_retriever = _make_retriever(embed_helpers_path, WORKDIR / "wiki")

        t0 = time.time()
        coord_failed_msg = None
        try:
            coord_result = coord.process_source(
                n=n,
                raw_path=str(WORKDIR / raw_path),
                target_path=str(WORKDIR / target_path),
                slug=slug,
                curator=coord_curator,
                retriever=coord_retriever,
            )
        except CoordinatorError as e:
            coord_failed_msg = str(e)
            coord_result = None
        wall_min = (time.time() - t0) / 60

        if coord_failed_msg is not None:
            # Coordinator hard-failed (e.g. malformed responses ×2). No
            # file was written. Treat as verify-fail and let the policy
            # decide stop vs continue.
            print(f"!!! SRC {n}: coordinator failed: {coord_failed_msg}",
                  file=sys.stderr)
            v = {"verified": "fail",
                 "violations": [f"coordinator_error: {coord_failed_msg}"]}
            decision = record_per_source_outcome(state, n, slug, v, policy=fail_policy)
            state[-1]["coord_metrics"] = {"wall_min": wall_min, "failed": True}
            if decision == "stop":
                stopped_at = n
                break
            continue

        coord_metrics = {
            "wall_min": wall_min,
            "claims": coord_result.claims_total,
            "claims_NEW": coord_result.claims_NEW,
            "claims_REPEATED": coord_result.claims_REPEATED,
            "concepts": coord_result.concepts_curated,
        }
        print(f"=== SRC {n}: coordinator wall {wall_min:.1f}min, "
              f"claims={coord_result.claims_total} "
              f"(NEW={coord_result.claims_NEW}, "
              f"REPEATED={coord_result.claims_REPEATED}, "
              f"CF={coord_result.claims_CF}), "
              f"concepts={coord_result.concepts_curated} ===",
              file=sys.stderr)

        # Functional verify (still runs — confirms file on disk + grades).
        v = verify_source(n, original_n=original_n, module_subdir=module_subdir, stem=stem)
        if v.get("verified") == "ok":
            try:
                commit = commit_and_push_per_source(n, slug, branch)
            except Exception as e:
                # Don't let a transient git/push failure stop the whole pipeline;
                # source.md is on disk and verify=ok, that's the canonical truth.
                commit = f"commit-failed: {type(e).__name__}: {e}"
                print(f"=== SRC {n}: commit_and_push failed but verify=ok, continuing: {e}",
                      file=sys.stderr)
            decision = record_per_source_outcome(state, n, slug, v, policy=fail_policy)
            # decoration on the appended entry — coordinator metrics + commit
            state[-1]["coord_metrics"] = coord_metrics
            state[-1]["commit"] = commit
            print(f"=== SRC {n}: verified=ok, claims={v.get('claims_total')}, "
                  f"REPEATED={v.get('claims_REPEATED')}, CF={v.get('claims_CF')}, "
                  f"commit={commit} ===", file=sys.stderr)
            assert decision == "continue", "verify=ok but policy said stop"
        else:
            decision = record_per_source_outcome(state, n, slug, v, policy=fail_policy)
            state[-1]["coord_metrics"] = coord_metrics
            print(f"!!! SRC {n}: verify=fail, violations={v.get('violations')[:3]}",
                  file=sys.stderr)
            if decision == "stop":
                stopped_at = n
                break
            # else policy=continue — keep going to next source.

    wall_total_min = (time.time() - t0_total) / 60
    print(f"\n[main] total wall: {wall_total_min:.1f} min", file=sys.stderr)

    # ─── INVARIANT B — concept template v3 validation ──────────────
    print(f"\n{'=' * 70}", file=sys.stderr)
    print("=== INVARIANT B (concept template v3) ===", file=sys.stderr)
    print(f"{'=' * 70}", file=sys.stderr)
    concepts = list((WORKDIR / "wiki" / "data" / "concepts").glob("*.md"))
    template_violations = []
    for c in concepts:
        v = validate_concept_v3(c)
        template_violations.extend(v)
    if template_violations:
        print(f"  TEMPLATE VIOLATIONS ({len(template_violations)}):", file=sys.stderr)
        for v in template_violations[:15]:
            print(f"    - {v}", file=sys.stderr)
    else:
        print(f"  all {len(concepts)} concepts pass template v3", file=sys.stderr)

    # ─── Bench report + commit ─────────────────────────────────────
    partial = stopped_at is not None
    write_bench_report(state, branch, partial=partial)
    run_cmd("git add bench-report.md && git commit -m 'bench-report' && git push origin " + branch,
            cwd=str(WORKDIR / "wiki"), check=False)
    print(f"\n[main] branch pushed: {branch}", file=sys.stderr)

    # ─── Final summary ─────────────────────────────────────────────
    # Three distinct counts per ADR 0012 (no silent skip): ok, skipped (verify-fail
    # under continue policy), errored (loop-terminating problems like retrieval
    # rebuild fail or invariant A breakage). Aggregate metrics ONLY over ok.
    sources_ok = [s for s in state if s.get("verify", {}).get("verified") == "ok"]
    sources_skipped = [s for s in state if s.get("stopped") == "verify_fail"]
    sources_errored = [s for s in state
                       if s.get("stopped") and s.get("stopped") != "verify_fail"]

    total_claims = sum(s.get("verify", {}).get("claims_total", 0) for s in sources_ok)
    total_repeated = sum(s.get("verify", {}).get("claims_REPEATED", 0) for s in sources_ok)
    total_cf = sum(s.get("verify", {}).get("claims_CF", 0) for s in sources_ok)

    print(f"\nFINAL counts (per ADR 0012):", file=sys.stderr)
    print(f"  verified_ok           = {len(sources_ok)} / {len(inputs)}", file=sys.stderr)
    print(f"  verified_fail_skipped = {len(sources_skipped)}  (correctness debt)", file=sys.stderr)
    print(f"  errored               = {len(sources_errored)}", file=sys.stderr)
    print(f"agg (over verified_ok only): claims={total_claims}, "
          f"REPEATED={total_repeated}, CF={total_cf}", file=sys.stderr)
    print(f"concepts: {len(concepts)} (template v3 violations: {len(template_violations)})",
          file=sys.stderr)
    print(f"per-source coord wall (min): "
          f"{[s.get('coord_metrics', {}).get('wall_min', '?') for s in state]}",
          file=sys.stderr)

    # ─── ADR 0012 enforcement: skipped-sources manifest + WIKI INCOMPLETE banner ──
    # P6 (completeness over availability) forbids silent skips. Continue-on-fail
    # is allowed as an opt-in for partial overnight progress, but it MUST surface
    # every skip via a manifest and a non-zero exit code so downstream tooling
    # cannot treat skipped == ok.
    if sources_skipped:
        manifest_path = WORKDIR / "skipped_sources.json"
        manifest = [
            {
                "n": s.get("n"),
                "slug": s.get("slug"),
                "violations": (s.get("verify") or {}).get("violations", []),
                "wall_min": (s.get("coord_metrics") or {}).get("wall_min"),
                "claims": (s.get("coord_metrics") or {}).get("claims"),
            }
            for s in sources_skipped
        ]
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        bar = "=" * 60
        print(file=sys.stderr)
        print(bar, file=sys.stderr)
        print(f"WIKI INCOMPLETE — {len(sources_skipped)} sources skipped",
              file=sys.stderr)
        print(f"  manifest: {manifest_path}", file=sys.stderr)
        print(f"  reconcile every entry before publishing this wiki "
              f"(per ADR 0012)", file=sys.stderr)
        print(bar, file=sys.stderr)
        # Exit code carries the skip count so CI cannot confuse "completed"
        # with "completed with skips". Cap at 125 (Posix-friendly upper bound).
        skip_exit = min(125, len(sources_skipped))
        print(f"\n=== EXIT INCOMPLETE ({skip_exit}) ===", file=sys.stderr)
        sys.exit(skip_exit)

    if partial:
        # errored (not the same as skipped). Loop-terminating fault.
        print("\n=== EXIT FAILED ===", file=sys.stderr); sys.exit(1)
    print("\n=== EXIT OK ===", file=sys.stderr); sys.exit(0)


if __name__ == "__main__":
    main()
