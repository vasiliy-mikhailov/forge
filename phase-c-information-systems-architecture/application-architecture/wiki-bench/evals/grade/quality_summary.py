"""Print quality-contract summary from a bench_grade JSON output."""
import json, sys

g = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/k1-v2-grade.json"))
a = g["aggregate"]
print()
print(f"sources_count             = {a.get('sources_count', '?')}")
print(f"concepts_total            = {a['concepts_total']}")
print()
print(f"all_violations_count      = {a['all_violations_count']}")
print(f"quality_violations_count  = {a['quality_violations_count']}")
print()
print("=== source quality (per ADR 0013) ===")
print(f"  sources_with_short_lecture            = {a['sources_with_short_lecture']}")
print(f"  sources_with_low_factcheck_coverage   = {a['sources_with_low_factcheck_coverage']}")
print(f"  sources_with_quality_violations       = {a['sources_with_quality_violations']}")
print()
print("=== concept quality (per ADR 0013) ===")
print(f"  concepts_with_thin_definition          = {a['concepts_with_thin_definition']}")
print(f"  concepts_with_zero_xrefs               = {a['concepts_with_zero_xrefs']}")
print(f"  concepts_with_definition_is_repetition = {a['concepts_with_definition_is_claim_repetition']}")
print(f"  concepts_with_quality_violations       = {a['concepts_with_quality_violations']}")
print()
print(f"=== quality content ratios ===")
src_total = len(g['sources'])
con_total = a['concepts_total']
if src_total:
    print(f"  short Лекция rate:  {a['sources_with_short_lecture']}/{src_total} = "
          f"{a['sources_with_short_lecture']/src_total:.0%}")
    print(f"  low fact-check rate: {a['sources_with_low_factcheck_coverage']}/{src_total} = "
          f"{a['sources_with_low_factcheck_coverage']/src_total:.0%}")
if con_total:
    print(f"  thin Definition rate: {a['concepts_with_thin_definition']}/{con_total} = "
          f"{a['concepts_with_thin_definition']/con_total:.0%}")
    print(f"  zero xrefs rate: {a['concepts_with_zero_xrefs']}/{con_total} = "
          f"{a['concepts_with_zero_xrefs']/con_total:.0%}")
