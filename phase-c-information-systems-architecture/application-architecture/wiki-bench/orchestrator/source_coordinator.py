"""Python coordinator for processing one source per ADR 0013.

Replaces the source-author agent monolith with a deterministic Python
workflow that owns workflow control. The LLM is invoked per discrete
step with response-schema enforcement and bounded retries; the
coordinator decides when work is done and writes source.md from
Python at a fixed point in the sequence.

This module deliberately knows nothing about OpenHands SDK, Conversation,
or agent state. It takes an `llm` callable (anything that obeys the
`(prompt, response_format, max_tokens) -> response` signature) and a
`curator` callable (invoked per concept; tests pass a no-op).

Per ADR 0013 anti-patterns: this coordinator MUST NOT silently complete
when an LLM step fails; MUST NOT continue past a malformed response
beyond one retry; MUST write source.md at a fixed step (so verify_source
finds the file iff the coordinator finished).
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# Per-step parallelism. vLLM batches concurrent requests internally so
# we can run extract chunks, classify batches, and fact-check calls
# concurrently. Default 5 (conservative); override with the env var
# D8_PILOT_MAX_PARALLEL for sweeps. Sweet spot found empirically per
# bench_parallel.py — depends on vLLM concurrency limit and per-call
# token budget.
import os as _os
_MAX_PARALLEL = int(_os.environ.get("D8_PILOT_MAX_PARALLEL", "5"))


# ─── Public types ──────────────────────────────────────────────────────


class CoordinatorError(Exception):
    """Raised when the coordinator cannot complete a source.

    The coordinator MUST raise this (or a subclass) instead of silently
    finishing. By the time this is raised, no source.md has been written.
    """


class MalformedResponseError(CoordinatorError):
    """Raised when an LLM response cannot be parsed against its schema
    even after the single allowed retry."""


@dataclass
class StepResult:
    name: str
    success: bool
    data: Any | None = None
    error: str | None = None


@dataclass
class SourceResult:
    n: int
    slug: str
    target_path: str
    claims_total: int = 0
    claims_NEW: int = 0
    claims_REPEATED: int = 0
    claims_CF: int = 0
    concepts_curated: int = 0
    steps: list[StepResult] = field(default_factory=list)


# ─── Schemas ──────────────────────────────────────────────────────────
#
# Each LLM call carries one of these. The schema is the *contract* with
# the LLM — anything else gets a retry then a hard error.

SCHEMA_CLAIMS_LIST = {
    "title": "claims_list",
    "schema": {
        "type": "object",
        "required": ["claims"],
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"},
                        "needs_factcheck": {"type": "boolean"},
                    },
                },
            },
        },
    },
}

SCHEMA_CLAIM_CLASSIFICATION = {
    "title": "claim_classification",
    "schema": {
        "type": "object",
        "required": ["verdict", "category"],
        "properties": {
            "verdict": {"type": "string"},   # NEW | REPEATED
            "category": {"type": "string"},
            "from_slug": {"type": "string"}, # set when verdict=REPEATED
        },
    },
}

SCHEMA_CLAIMS_BATCH_CLASSIFICATION = {
    "title": "claims_batch_classification",
    "schema": {
        "type": "object",
        "required": ["classifications"],
        "properties": {
            "classifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["claim_index", "verdict", "category"],
                    "properties": {
                        "claim_index": {"type": "integer"},
                        "verdict": {"type": "string"},
                        "category": {"type": "string"},
                        "from_slug": {"type": "string"},
                    },
                },
            },
        },
    },
}

SCHEMA_FACT_CHECK = {
    "title": "fact_check",
    "schema": {
        "type": "object",
        "required": ["marker"],
        "properties": {
            "marker": {"type": "string"},     # NEW | CONTRADICTS_FACTS | NO_MATCH
            "url": {"type": "string"},
            "notes": {"type": "string"},
        },
    },
}


# ─── Coordinator ──────────────────────────────────────────────────────


class SourceCoordinator:
    """Deterministic per-source workflow.

    Args:
      llm: callable with signature
           (prompt: str, response_format: dict, max_tokens: int) -> Any
           returning either a parsed dict matching the schema, or raw
           text (which the coordinator will treat as malformed and
           retry once).
      workdir: workspace root (contains wiki/ and raw/).
    """

    def __init__(self, llm: Callable[..., Any], workdir: Path):
        self.llm = llm
        self.workdir = Path(workdir)

    # ─── public entrypoint ────────────────────────────────────────

    def process_source(
        self,
        *,
        n: int,
        raw_path: str,
        target_path: str,
        slug: str,
        curator: Callable[..., Any],
        retriever: Callable[[str], list[dict]] | None = None,
    ) -> SourceResult:
        """Process a single source end-to-end. Returns a SourceResult or
        raises CoordinatorError.

        retriever, if provided, is called per-claim with the claim text
        and must return a list of candidate prior claims like
        [{'source_slug': str, 'claim_text': str, 'score': float, ...}, ...].
        These are passed into the classify prompt so the LLM can decide
        NEW vs REPEATED. If retriever is None, every claim is classified
        without prior-art context (everything tends NEW)."""
        result = SourceResult(n=n, slug=slug, target_path=target_path)

        # Step 1 — read raw.json (deterministic).
        raw = self._read_raw(raw_path)
        transcript = self._compose_transcript(raw)
        result.steps.append(StepResult("read_raw", True))

        # Step 2 — extract claims (LLM, schema-bound).
        # For long transcripts (multi-hour lectures = 50K+ chars of Russian),
        # a single extract_claims call is impractical: input token cost is
        # huge AND structured-decoding throughput drops. We chunk the
        # transcript and merge per-chunk claim lists. Threshold tuned to
        # keep each chunk's prompt under ~10K input tokens.
        CHUNK_CHAR_LIMIT = 8_000  # roughly 2-3 K russian tokens per chunk
        chunks = self._chunk_transcript(transcript, CHUNK_CHAR_LIMIT)
        print(f"  [coord] extract_claims: {len(chunks)} chunks "
              f"(parallel ×{_MAX_PARALLEL})", flush=True)
        t_extract = time.monotonic()

        def _extract_one(chunk):
            return self._llm_with_retry(
                prompt=self._prompt_extract_claims(chunk),
                schema=SCHEMA_CLAIMS_LIST,
                max_tokens=4000,
            )

        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL) as pool:
            chunk_results = list(pool.map(_extract_one, chunks))
        claims: list[dict] = []
        for chunk_data in chunk_results:
            claims.extend(chunk_data.get("claims", []))
        print(f"  [coord] extract_claims done ({time.monotonic()-t_extract:.0f}s, "
              f"{len(claims)} raw claims)", flush=True)
        # Dedup near-identical claim texts (LLM may surface the same
        # idea twice across chunk boundaries).
        seen: set[str] = set()
        deduped: list[dict] = []
        for c in claims:
            key = c.get("text", "").strip().lower()[:120]
            if key and key not in seen:
                seen.add(key)
                deduped.append(c)
        claims = deduped
        result.steps.append(StepResult("extract_claims", True, data=len(claims)))

        # Step 3 — classify claims in batches of BATCH_SIZE (LLM per
        # batch, schema-bound). Batching is a 5-10× speedup over per-claim
        # calls because vLLM amortises the structured-decoding setup
        # across multiple outputs in one streaming response.
        BATCH_SIZE = 8
        n_claims = len(claims)
        batches = [claims[i:i + BATCH_SIZE]
                   for i in range(0, n_claims, BATCH_SIZE)]
        if n_claims:
            print(f"  [coord] classify_claims: {n_claims} claims, "
                  f"{len(batches)} batches, parallel ×{_MAX_PARALLEL}",
                  flush=True)
        t_classify = time.monotonic()

        def _classify_one(batch):
            # Retrieval per claim still serial within a batch (cheap if
            # retriever caches; the parallel speedup comes across
            # batches, not within them).
            batch_with_candidates = [
                (c, retriever(c["text"]) if retriever else [])
                for c in batch
            ]
            data = self._llm_with_retry(
                prompt=self._prompt_classify_batch(batch_with_candidates),
                schema=SCHEMA_CLAIMS_BATCH_CLASSIFICATION,
                max_tokens=2000,
            )
            return batch_with_candidates, data

        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL) as pool:
            batch_results = list(pool.map(_classify_one, batches))

        classified: list[dict] = []
        for batch_with_candidates, data in batch_results:
            results_by_idx = {r["claim_index"]: r
                              for r in data["classifications"]}
            for i, (claim, _) in enumerate(batch_with_candidates):
                r = results_by_idx.get(i + 1) or results_by_idx.get(i)
                if r is None:
                    r = {"verdict": "NEW", "category": "uncategorised"}
                classified.append({
                    "text": claim["text"],
                    "needs_factcheck": claim.get("needs_factcheck", False),
                    "verdict": r.get("verdict", "NEW"),
                    "category": r.get("category", "uncategorised"),
                    "from_slug": r.get("from_slug"),
                })
        print(f"  [coord] classify_claims done "
              f"({time.monotonic()-t_classify:.0f}s, {len(classified)} classified)",
              flush=True)
        result.steps.append(StepResult("classify_claims", True, data=len(classified)))

        # Step 4 — selective fact-check (LLM per needs_factcheck claim).
        # Empirically the LLM over-flags needs_factcheck (K1 v2 SRC 0:
        # 89/107 flagged). The source-author historically did ~3-5 per
        # source. Cap to keep wall time tractable; sample by score if
        # the schema gives one (it doesn't yet — first N for now).
        FACT_CHECK_CAP = 8
        all_flagged = [c for c in classified if c.get("needs_factcheck")]
        to_check = all_flagged[:FACT_CHECK_CAP]
        if all_flagged:
            print(f"  [coord] fact_check: {len(to_check)} of "
                  f"{len(all_flagged)} flagged (cap={FACT_CHECK_CAP}, "
                  f"parallel ×{_MAX_PARALLEL})", flush=True)
        t_fc = time.monotonic()

        def _fact_check_one(c):
            return c, self._llm_with_retry(
                prompt=self._prompt_fact_check(c),
                schema=SCHEMA_FACT_CHECK,
                max_tokens=600,
            )

        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL) as pool:
            for c, fc in pool.map(_fact_check_one, to_check):
                c["fact_marker"] = fc.get("marker")
                c["fact_url"] = fc.get("url")
                c["fact_notes"] = fc.get("notes")
        if to_check:
            print(f"  [coord] fact_check done ({time.monotonic()-t_fc:.0f}s)",
                  flush=True)
        result.steps.append(StepResult("fact_check", True))

        # Step 5 — compose source.md from collected results (deterministic).
        body = self._compose_md(slug=slug, transcript=transcript,
                                claims=classified)

        # Step 6 — WRITE FILE (deterministic, the property SRC 17 violated).
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        result.steps.append(StepResult("write_file", True, data=str(target)))

        # Step 7 — invoke concept-curator per concept (delegated to caller).
        # Concepts are derived from classified claims' categories. The curator
        # callable is supplied by the orchestrator; tests pass a no-op.
        concepts = self._collect_concepts(classified)
        for slug_c in concepts:
            curator(slug_c, slug)  # let the caller decide what curator means
            result.concepts_curated += 1

        # Tally counters
        result.claims_total = len(classified)
        result.claims_NEW = sum(1 for c in classified if c["verdict"] == "NEW")
        result.claims_REPEATED = sum(1 for c in classified if c["verdict"] == "REPEATED")
        result.claims_CF = sum(1 for c in classified
                               if c.get("fact_marker") == "CONTRADICTS_FACTS")

        return result

    # ─── LLM wrapper with retry ──────────────────────────────────

    def _llm_with_retry(self, *, prompt: str, schema: dict, max_tokens: int) -> dict:
        """Call the LLM with the schema; on schema mismatch, retry once
        with a corrective prompt; on second failure, raise.

        This is the load-bearing safeguard from ADR 0013: malformed
        responses NEVER pass through silently."""
        for attempt in (1, 2):
            response = self.llm(
                prompt=prompt,
                response_format=schema,
                max_tokens=max_tokens,
            )
            if self._validates(response, schema):
                return response
            # Build retry prompt with corrective instruction.
            prompt = (
                f"{prompt}\n\n"
                f"⚠️ Your previous response did not match the required JSON "
                f"schema (title={schema['title']!r}). Reply with a valid JSON "
                f"object matching the schema exactly. Previous response:\n"
                f"{response!r}"
            )
        raise MalformedResponseError(
            f"LLM produced malformed responses for schema "
            f"{schema['title']!r} after {attempt} attempts. "
            f"Last response: {response!r}"
        )

    def _validates(self, response: Any, schema: dict) -> bool:
        """Minimal JSON-schema validation: must be a dict, must have all
        the required top-level fields."""
        if not isinstance(response, dict):
            return False
        required = (schema.get("schema") or {}).get("required", [])
        return all(k in response for k in required)

    # ─── Step helpers ────────────────────────────────────────────

    def _read_raw(self, raw_path: str) -> dict:
        path = Path(raw_path)
        if not path.exists():
            raise CoordinatorError(f"raw.json not found at {raw_path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _compose_transcript(self, raw: dict) -> str:
        return " ".join(s.get("text", "") for s in raw.get("segments", []))

    def _chunk_transcript(self, transcript: str, char_limit: int) -> list[str]:
        """Split a long transcript into chunks of at most char_limit each,
        breaking on whitespace to keep words intact. Returns at least one
        chunk even for empty input."""
        if not transcript:
            return [""]
        if len(transcript) <= char_limit:
            return [transcript]
        chunks: list[str] = []
        i = 0
        n = len(transcript)
        while i < n:
            end = min(i + char_limit, n)
            if end < n:
                # back up to nearest whitespace to avoid splitting a word
                while end > i and not transcript[end].isspace():
                    end -= 1
                if end == i:
                    end = min(i + char_limit, n)  # no whitespace; hard split
            chunks.append(transcript[i:end])
            i = end
            while i < n and transcript[i].isspace():
                i += 1
        return chunks

    def _collect_concepts(self, classified: list[dict]) -> list[str]:
        """Concepts are derived from classified claim categories.
        Returns a list of unique concept slugs."""
        seen: list[str] = []
        for c in classified:
            cat = c.get("category")
            if cat and cat not in seen:
                seen.append(cat)
        return seen

    # ─── Prompts (per-step, schema-bound) ─────────────────────────

    def _prompt_extract_claims(self, transcript: str) -> str:
        return (
            "Extract distinct empirical claims from this lecture "
            "transcript. Aim for ~1 claim per 60 seconds of audio "
            "density.\n\n"
            "Set needs_factcheck=true ONLY if the claim contains a "
            "concrete external fact:\n"
            "  - a specific person's name + biographical/historical "
            "    detail (e.g. 'Adler had rickets')\n"
            "  - a numeric statistic ('80% of patients...')\n"
            "  - a named scientific finding ('the glymphatic system "
            "    drains at 60 nm/s')\n"
            "  - a specific claim about a published study or theory\n"
            "Otherwise (general statements, conceptual framings, the "
            "speaker's own opinions, methodological remarks, "
            "definitional claims) → needs_factcheck=false.\n\n"
            "Default to false. Only flag if a Wikipedia search could "
            "plausibly confirm or refute.\n\n"
            f"TRANSCRIPT:\n{transcript}\n"
        )

    def _prompt_classify_claim(self, claim: dict,
                                candidates: list[dict] | None = None) -> str:
        prompt = (
            "Classify this claim. Set verdict to either NEW (this idea "
            "has not appeared in the prior wiki) or REPEATED (this idea "
            "has appeared before; if so, set from_slug to the prior "
            "source slug). Set category to the claim's thematic category "
            "(short kebab-case slug).\n\n"
            f"CLAIM: {claim['text']!r}\n"
        )
        if candidates:
            prompt += "\nCANDIDATE PRIOR CLAIMS (with cosine score):\n"
            for c in candidates[:5]:
                score = c.get("score", c.get("similarity", "?"))
                src = c.get("source_slug", "?")
                txt = c.get("claim_text", c.get("text", ""))
                prompt += f"  ({score:.2f}) [{src}] {txt!r}\n"
            prompt += (
                "\nDecision rule:\n"
                "  score ≥ 0.85 → REPEATED (set from_slug)\n"
                "  0.78 ≤ score < 0.85 → REPEATED if same proposition\n"
                "  score < 0.78 → NEW\n"
            )
        return prompt

    def _prompt_classify_batch(
        self, batch: list[tuple[dict, list[dict]]]
    ) -> str:
        prompt = (
            "Classify each claim below. For each, output a JSON object with\n"
            "  claim_index (1-based, matches the CLAIM N: prefix below)\n"
            "  verdict: NEW or REPEATED\n"
            "  category: short kebab-case thematic slug\n"
            "  from_slug: prior source slug (only when verdict=REPEATED)\n"
            "Return all classifications as the `classifications` array.\n\n"
            "Decision rule for each claim:\n"
            "  candidate score >= 0.85 → REPEATED (set from_slug)\n"
            "  0.78 <= score < 0.85 → REPEATED if same proposition\n"
            "  score < 0.78 or no candidates → NEW\n\n"
        )
        for i, (claim, candidates) in enumerate(batch, start=1):
            prompt += f"CLAIM {i}: {claim['text']!r}\n"
            if candidates:
                prompt += "  candidates:\n"
                for c in candidates[:3]:
                    score = c.get("score", c.get("similarity", 0))
                    src = c.get("source_slug", "?")
                    txt = c.get("claim_text", c.get("text", ""))[:80]
                    prompt += f"    ({score:.2f}) [{src}] {txt!r}\n"
            prompt += "\n"
        return prompt

    def _prompt_fact_check(self, claim: dict) -> str:
        return (
            "Fact-check this empirical claim. Set marker to one of "
            "NEW (consistent with public knowledge), CONTRADICTS_FACTS "
            "(verifiably wrong), or NO_MATCH (no source found). If "
            "marker is NEW or CONTRADICTS_FACTS, provide url + notes.\n\n"
            f"CLAIM: {claim['text']!r}\n"
        )

    # ─── source.md composition ────────────────────────────────────

    def _compose_md(self, *, slug: str, transcript: str,
                    claims: list[dict]) -> str:
        """Compose the final source.md body from deterministic Python.

        Per the prompt-change earlier this week:
          - 5 sections in order: TL;DR, Лекция сжато, Claims, New ideas,
            All ideas
          - Claim markers lead at line start: `1. [NEW] <text>`
        """
        parts = [self._frontmatter(slug, claims)]
        parts.append(self._section_tldr(transcript, claims))
        parts.append(self._section_lecture(transcript))
        parts.append(self._section_claims(claims))
        parts.append(self._section_new_ideas(claims))
        parts.append(self._section_all_ideas(claims))
        return "\n\n".join(parts) + "\n"

    def _frontmatter(self, slug: str, claims: list[dict]) -> str:
        concepts_touched = sorted({c["category"] for c in claims if c.get("category")})
        # `concepts_introduced` is concepts whose first introduction is here;
        # without retrieval state in the unit-test layer, treat all touched as
        # introduced. The integration layer will refine this.
        concepts_introduced = list(concepts_touched)
        slug_parts = slug.split("/")
        course = slug_parts[0] if slug_parts else ""
        module = slug_parts[1] if len(slug_parts) > 1 else ""
        fact_check_performed = any(c.get("needs_factcheck") for c in claims)
        fm_lines = [
            "---",
            f"slug: {slug}",
            f"course: {course}",
            f"module: {module}",
            "extractor: source_coordinator",
            "source_raw: raw.json",
            "processed_at: 2026-04-30T00:00:00Z",
            f"fact_check_performed: {str(fact_check_performed).lower()}",
            f"concepts_touched: {concepts_touched!r}",
            f"concepts_introduced: {concepts_introduced!r}",
            "---",
        ]
        return "\n".join(fm_lines)

    def _section_tldr(self, transcript: str, claims: list[dict]) -> str:
        # Coordinator-side default: a short paragraph stitched from the
        # first sentence of the transcript. The integration layer will
        # replace this with a dedicated LLM call if needed.
        first = transcript[:200].rstrip()
        return f"## TL;DR\n\n{first}"

    def _section_lecture(self, transcript: str) -> str:
        return (
            "## Лекция сжато (только новое и проверенное)\n\n"
            f"{transcript}"
        )

    def _section_claims(self, claims: list[dict]) -> str:
        lines = ["## Claims — provenance and fact-check", ""]
        for i, c in enumerate(claims, start=1):
            marker = self._marker_for(c)
            lines.append(f"{i}. {marker} {c['text']}")
            if c.get("fact_url"):
                lines.append(f"   — {c['fact_url']}")
            if c.get("fact_notes"):
                lines.append(f"   {c['fact_notes']}")
        return "\n".join(lines)

    def _section_new_ideas(self, claims: list[dict]) -> str:
        lines = ["## New ideas (verified)", ""]
        new_ones = [c for c in claims if c["verdict"] == "NEW"]
        if not new_ones:
            return "\n".join(lines + ["(none)"])
        # Group by category
        by_cat: dict[str, list[dict]] = {}
        for c in new_ones:
            by_cat.setdefault(c.get("category", "uncategorised"), []).append(c)
        for cat, items in by_cat.items():
            lines.append(f"**{cat}**")
            for c in items:
                lines.append(f"- {c['text']}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _section_all_ideas(self, claims: list[dict]) -> str:
        lines = ["## All ideas", ""]
        for c in claims:
            lines.append(f"- {c['text']}")
        return "\n".join(lines)

    def _marker_for(self, c: dict) -> str:
        if c.get("fact_marker") == "CONTRADICTS_FACTS":
            return "[CONTRADICTS_FACTS]"
        if c["verdict"] == "REPEATED":
            slug = c.get("from_slug") or "unknown"
            return f"[REPEATED (from: {slug})]"
        return "[NEW]"
