"""Build readable PDFs with Pandoc/Typst, separately from the publisher class."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pandoc',default=shutil.which('pandoc'))
parser.add_argument('--typst',default=shutil.which('typst'))
args=parser.parse_args()
if not args.pandoc or not args.typst: parser.error('Install Pandoc and Typst or supply their paths')
args.pandoc=str(Path(args.pandoc).resolve())
args.typst=str(Path(args.typst).resolve())
folder=Path(__file__).resolve().parent
main=(folder/'main.tex').read_text(encoding='utf8')
anonymous=re.sub(r'(?m)^\\author\{.*\}\r?\n','',main)
for text,name in [(main,'manuscript'),(anonymous,'anonymous'),((folder/'supplementary.tex').read_text(encoding='utf8'),'supplement')]:
    text=re.sub(r'(figures/[^}]+)\.pdf',r'\1.png',text)
    text=text.replace('table*}','table}').replace('figure*}','figure}')
    if name=='supplement': text=text.replace(r'\section*{Supplementary replication notes}','')
    command=[args.pandoc,'-f','latex','-t','typst','--pdf-engine='+args.typst,
             '--citeproc','--csl=ieee.csl','--bibliography=references.bib','--resource-path=.',
             '-M','reference-section-title=References','-V','papersize=us-letter',
             '-o',name+'.pdf']
    title='Supplementary replication notes' if name=='supplement' else 'Label Coverage Bounds Pooled Macro F1 in Closed-Set Benchmarks'
    command.extend(['-M','title='+title])
    if name=='manuscript': command.extend(['-M','author=Shah Zaib Sajid'])
    subprocess.run(command,input=text,encoding='utf8',cwd=folder,check=True)
