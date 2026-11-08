"""Collect the frozen Crossref frame and reproduce its DOI sample."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd


QUERIES = ["intrusion detection temporal evaluation", "intrusion detection chronological split",
           "intrusion detection leave one day out", "intrusion detection group holdout",
           "intrusion detection unseen attacks evaluation",
           "network intrusion detection concept drift benchmark"]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("out", type=Path)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
raw = args.out / "raw"
raw.mkdir(exist_ok=True)
records = {}
for i, query in enumerate(QUERIES, 1):
    path = raw / f"query_{i}.json"
    if path.exists():
        result = json.loads(path.read_text(encoding="utf8"))
    else:
        parameters = {"query.bibliographic": query, "rows": 100,
                      "filter": "from-pub-date:2017-01-01,until-pub-date:2026-11-08",
                      "sort": "relevance", "order": "desc"}
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(parameters)
        request = urllib.request.Request(url, headers={"User-Agent": "LabelAvailabilityAudit/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.load(response)
        result = {"query": query, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                  "response": body}
        result['original_sha256'] = hashlib.sha256(json.dumps(result, ensure_ascii=False).encode('utf8')).hexdigest()
        result['redaction'] = 'Abstracts and reference lists omitted; selection uses titles and DOIs only.'
        for item in body['message']['items']:
            item.pop('abstract', None)
            item.pop('reference', None)
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf8")
        time.sleep(1)
    for item in result["response"]["message"]["items"]:
        title = " ".join(item.get("title", []))
        if "intrusion" not in title.lower() or "detect" not in title.lower():
            continue
        doi = item["DOI"].lower()
        if doi in records:
            continue
        records[doi] = {"doi": doi, "title": title, "publisher": item.get("publisher", ""),
                        "publication_type": item.get("type", ""),
                        "journal": " | ".join(item.get("container-title", [])),
                        "url": item.get("URL", ""), "first_query": i,
                        "links": json.dumps(item.get("link", [])),
                        "published": json.dumps(item.get("published", {}))}
frame = pd.DataFrame(records.values()).sort_values("doi").reset_index(drop=True)
frame.to_csv(args.out / "candidate_frame.csv", index=False)
selection = np.random.default_rng(20261108).choice(len(frame), size=min(50, len(frame)), replace=False)
sample = frame.iloc[selection].copy().reset_index(drop=True)
sample.insert(0, "record_id", [f"A{i:02d}" for i in range(1, len(sample)+1)])
sample.to_csv(args.out / "selected_sample.csv", index=False)
for column in ["eligibility", "reason", "evidence_url", "evidence_location", "dataset", "split",
               "target", "vocabulary", "support", "pooling", "label_inventory", "metric", "reported_value",
               "ceiling", "audit_status", "retrieval_status", "notes"]:
    sample[column] = "pending"
if not (args.out / "coding.csv").exists():
    sample.to_csv(args.out / "coding.csv", index=False)
digest = hashlib.sha256((args.out / "candidate_frame.csv").read_bytes()).hexdigest()
(args.out / "frame_sha256.txt").write_text(digest+"\n", encoding="ascii")
print("Frame", len(frame), "sample", len(sample), "SHA256", digest, flush=True)
print(sample[["record_id", "doi", "title"]].to_string(index=False))
