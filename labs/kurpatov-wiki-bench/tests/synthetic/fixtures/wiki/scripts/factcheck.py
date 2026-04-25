#!/usr/bin/env python3
"""
factcheck.py "<claim text>" — Wikipedia-backed fact-check helper.

Runs OpenSearch on en.wikipedia.org AND ru.wikipedia.org.
Returns top-5 results from each, with title, snippet/description, and
canonical URL.

The skill mandates calling this BEFORE marking any empirical claim as
fact-checked. The URLs in the output are the only legitimate citation
sources (so a CONTRADICTS_FACTS marker without a URL from this script
is suspect — see synthetic test assert.py).

Output: JSON to stdout.
{
  "query": "<claim text>",
  "results": [
    {"lang": "en", "title": "...", "description": "...", "url": "https://..."},
    {"lang": "ru", "title": "...", "description": "...", "url": "https://..."},
    ...
  ]
}
"""
import json
import sys
import urllib.parse
import urllib.request


def search(lang, query, limit=5, timeout_s=10):
    url = (
        f"https://{lang}.wikipedia.org/w/api.php?"
        f"action=opensearch&search={urllib.parse.quote(query)}"
        f"&limit={limit}&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "kurpatov-wiki-bench-factcheck/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            raw = r.read().decode("utf-8")
        # OpenSearch returns [query, [titles], [descs], [urls]]
        data = json.loads(raw)
        if not isinstance(data, list) or len(data) < 4:
            return []
        titles, descs, urls = data[1], data[2], data[3]
        return [
            {"lang": lang, "title": t, "description": d, "url": u}
            for t, d, u in zip(titles, descs, urls)
        ]
    except Exception as e:
        return [{"lang": lang, "error": str(e)[:160]}]


def main():
    if len(sys.argv) < 2:
        print('usage: factcheck.py "<claim text>"', file=sys.stderr)
        sys.exit(2)
    query = " ".join(sys.argv[1:])

    en = search("en", query)
    ru = search("ru", query)

    out = {"query": query, "results": en + ru}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
