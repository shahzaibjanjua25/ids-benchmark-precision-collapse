"""Retrieve Crossref metadata for revision DOIs; retain failures as failures."""
import concurrent.futures
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def retrieve(doi):
    try:
        req = urllib.request.Request("https://api.crossref.org/works/" + doi,
                                     headers={"User-Agent": "LabelAvailabilityResearchAudit/0.10"})
        with urllib.request.urlopen(req, timeout=40) as response:
            message = json.load(response)["message"]
        return {"doi": doi, "retrieved": "2026-11-15", "status": "metadata verified",
                "title": message.get("title"), "authors": message.get("author"),
                "venue": message.get("container-title"), "published": message.get("published"),
                "type": message.get("type"), "url": message.get("URL"),
                "scope": "Existence and metadata only; claim support requires article inspection"}
    except Exception as exc:
        return {"doi": doi, "retrieved": "2026-11-15", "status": "retrieval failed", "error": str(exc)}


def main():
    bib = (ROOT / "paper/revision/references.bib").read_text(encoding="utf8")
    dois = re.findall(r"doi=\{([^}]+)\}", bib)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(retrieve, dois))
    path = ROOT / "audit/revision_20261115"
    path.mkdir(parents=True, exist_ok=True)
    (path / "reference_metadata.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps({"requested": len(dois), "verified": sum(r["status"] == "metadata verified" for r in results)}))


if __name__ == "__main__":
    main()
