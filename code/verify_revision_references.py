"""Retrieve Crossref metadata for revision DOIs; retain failures as failures."""
import concurrent.futures
import argparse
from datetime import datetime, timezone
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def retrieve(doi):
    checked = datetime.now(timezone.utc).isoformat()
    try:
        datacite = doi.startswith('10.24432/')
        endpoint = 'https://api.datacite.org/dois/' if datacite else 'https://api.crossref.org/works/'
        req = urllib.request.Request(endpoint + doi,
                                     headers={"User-Agent": "LabelAvailabilityResearchAudit/0.10"})
        with urllib.request.urlopen(req, timeout=40) as response:
            response_data = json.load(response)
            message = response_data['data']['attributes'] if datacite else response_data['message']
        return {"doi": doi, "retrieved": checked, "status": "metadata verified",
                "registry": 'DataCite' if datacite else 'Crossref',
                "title": message.get("title"), "authors": message.get("author"),
                "venue": message.get("container-title"), "published": message.get("published"),
                "type": message.get("type"), "url": message.get("URL"),
                "registry_metadata": message,
                "scope": "Existence and metadata only; claim support requires article inspection"}
    except Exception as exc:
        return {"doi": doi, "retrieved": checked, "status": "retrieval failed", "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bib', type=Path, default=ROOT/'paper/revision/references.bib', help='Separately held BibTeX file')
    parser.add_argument('--output', type=Path, default=ROOT/'.cache/reference_metadata.json')
    args=parser.parse_args()
    if not args.bib.is_file():
        parser.error('Supply --bib PATH_TO_REFERENCES; manuscript sources are held separately')
    bib = args.bib.read_text(encoding="utf8")
    dois = re.findall(r"doi=\{([^}]+)\}", bib)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(retrieve, dois))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps({"requested": len(dois), "verified": sum(r["status"] == "metadata verified" for r in results)}))
    if not results or any(r['status']!='metadata verified' for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
