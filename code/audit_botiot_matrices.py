"""Re-score six binary matrices in the author manuscript of Bot-IoT (2019)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MATRICES = {'svm_10': [[477,0],[426550,3241495]], 'svm_full': [[64,413],[0,3668045]],
            'lstm_10': [[149,328],[9139,3658906]], 'lstm_full': [[430,47],[71221,3596824]],
            'rnn_10': [[127,350],[9171,3658874]], 'rnn_full': [[379,98],[76718,3591327]]}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', type=Path)
    args = parser.parse_args()
    out = ROOT/'results/continuation_20261115/botiot_matrices'
    out.mkdir(parents=True,exist_ok=True)
    records=[]
    for name, value in MATRICES.items():
        c=np.array(value,dtype=np.int64); n=c.sum()
        assert n==3668522 and np.array_equal(c.sum(axis=1),[477,3668045])
        f=2*np.diag(c)/(c.sum(axis=0)+c.sum(axis=1))
        records.append({'model':name,'observations':int(n),'accuracy':float(np.trace(c)/n),
                        'normal_f1':float(f[0]),'attack_f1':float(f[1]),'derived_macro_f1':float(f.mean()),
                        'legal_binary_ceiling':1.0})
    pd.DataFrame(records).to_csv(out/'summary.csv',index=False)
    (out/'matrices.json').write_text(json.dumps(MATRICES,indent=2),encoding='utf8')
    if args.source_pdf:
        import pymupdf
        doc=pymupdf.open(args.source_pdf)
        text='\n'.join(p.get_text(sort=True) for p in doc)
        verified=[]
        for table,stem in [(10,'svm'),(11,'lstm'),(12,'rnn')]:
            match=re.search(r'Table '+str(table)+r': Confusion matrices.*?(?=Figure)',text,re.S)
            assert match, table
            block=match[0]
            normal=re.search(r'Normal \(0\)\s+(\d+)\s+(\d+)\s+Normal \(0\)\s+(\d+)\s+(\d+)',block)
            attack=re.search(r'Attack \(1\)\s+(\d+)\s+(\d+)\s+Attack \(1\)\s+(\d+)\s+(\d+)',block)
            assert normal and attack
            for offset,suffix in [(0,'10'),(2,'full')]:
                extracted=[[int(normal[i+offset]) for i in [1,2]], [int(attack[i+offset]) for i in [1,2]]]
                assert extracted==MATRICES[f'{stem}_{suffix}']
                verified.append(f'{stem}_{suffix}')
        (out/'source_verification.json').write_text(json.dumps({
            'source_url':'https://arxiv.org/pdf/1811.00701',
            'published_study_doi':'10.1016/j.future.2019.05.041',
            'version_scope':'Author manuscript arXiv:1811.00701v1; journal PDF identity not asserted',
            'source_sha256':hashlib.sha256(args.source_pdf.read_bytes()).hexdigest(),
            'tables':[10,11,12], 'matrices_verified':verified,'integer_cells_verified':24,
            'interpretation':'Derived macro F1 is our additional metric; the source does not claim these values as macro F1.'
        },indent=2),encoding='utf8')
    print(pd.DataFrame(records).to_string(index=False))

if __name__=='__main__': main()
