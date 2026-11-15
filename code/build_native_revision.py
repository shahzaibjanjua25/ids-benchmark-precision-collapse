"""Export the canonical revision to the journal-linked Springer class and compile it.

Requires an installed pdflatex and bibtex on PATH; publisher styles are vendored
unmodified with their provenance. This exporter fails on unhandled Typst syntax.
"""
from pathlib import Path
import re
import subprocess
import shutil
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/revision'
OUT = PAPER / 'native'

def escape(s):
    return ''.join({'&': r'\&', '%': r'\%', '_': r'\_', '#': r'\#',
                    '{': r'\{', '}': r'\}', '\\': r'\textbackslash{}'}.get(c,c) for c in s)

def math(s):
    s = s.strip()
    exact = {
      'S = {k : sum_f n_(f k) > 0}, quad n_k = sum_f n_(f k), quad m_k = sum_f n_(f k) bold(1){k in V_f}.':
      r'\begin{aligned}S&=\{k:\sum_f n_{fk}>0\},\quad n_k=\sum_f n_{fk},\\m_k&=\sum_f n_{fk}\mathbf1\{k\in V_f\}.\end{aligned}',
      'F_S <= C_S = 1/abs(S) sum_(k in S) (2 m_k)/(n_k+m_k) = 1/abs(S) sum_(k in S) (2 rho_k)/(1+rho_k).':
      r'F_S\le C_S=\frac1{|S|}\sum_{k\in S}\frac{2m_k}{n_k+m_k}=\frac1{|S|}\sum_{k\in S}\frac{2\rho_k}{1+\rho_k}.',
      'O_S = max_a 1/abs(S) sum_(k in S) (2m_k)/(n_k+m_k+a_k).':
      r'O_S=\max_a\frac1{|S|}\sum_{k\in S}\frac{2m_k}{n_k+m_k+a_k}.',
      'product_(j=1)^q j^(binom(q,j)) <= q^(2^q-1).':
      r'\prod_{j=1}^q j^{\binom qj}\le q^{2^q-1}.',
      'max(0,C_S-sum_f c_f) <= O_S <= C_S-max_f c_f.':
      r'\max(0,C_S-\sum_f c_f)\le O_S\le C_S-\max_f c_f.',
      'ell = sum_(k:a_k>0) a_k/(2+a_k).':r'\ell=\sum_{k:a_k>0}\frac{a_k}{2+a_k}.',
      'sum_(k in S) n_k (2m_k/(n_k+m_k))/sum_k n_k':r'\frac{\sum_{k\in S}n_k\frac{2m_k}{n_k+m_k}}{\sum_k n_k}',
      'sum_k m_k/sum_k n_k':r'\frac{\sum_k m_k}{\sum_k n_k}',
      'sum_(k in S) rho_k/abs(S)':r'\frac{\sum_{k\in S}\rho_k}{|S|}',
    }
    if s in exact: return exact[s]
    s = re.sub(r'"([A-Za-z]+)"', r'\\mathrm{\1}', s)
    s = re.sub(r'binom\(([^,]+),([^\)]+)\)',r'\\binom{\1}{\2}',s)
    s = re.sub(r'abs\(([^)]+)\)',r'|\1|',s)
    s = re.sub(r'ceil\(([^)]+)\)',r'\\lceil \1\\rceil',s)
    s = s.replace('subset.eq',r'\subseteq').replace('in.not',r'\notin')
    for word, tex in [('rho',r'\rho'),('Delta',r'\Delta'),('ell',r'\ell'),('quad',r'\quad'),
                      ('sum',r'\sum'),('min',r'\min'),('max',r'\max'),('square',r'\square'),('in',r'\in')]:
        s = re.sub(r'(?<![A-Za-z])'+word+r'(?![A-Za-z])',lambda _:tex,s)
    s = s.replace('<=',r'\le ').replace('>=',r'\ge ')
    s = re.sub(r'_\(([^()]*)\)',r'_{\1}',s)
    s = re.sub(r'\^\(([^()]*)\)',r'^{\1}',s)
    s = s.replace('{k:',r'\{k:').replace('{k ',r'\{k ')
    if r'\{' in s: s = s.replace('}',r'\}',1)
    return s

def prose(s):
    tokens = []
    def keep(value):
        tokens.append(value); return f'ZZTOKEN{len(tokens)-1}ZZ'
    s = re.sub(r'\$([^$]+)\$',lambda m:keep('$'+math(m[1])+'$'),s)
    s = re.sub(r'#link\("([^"]+)"\)\[([^\]]+)\]',lambda m:keep(r'\href{'+m[1]+'}{'+escape(m[2])+'}'),s)
    s = re.sub(r'@([\w-]+)',lambda m:keep((r'Table~\ref{' if m[1].startswith('tab-') else r'Fig.~\ref{' if m[1].startswith('fig-') else r'\cite{')+m[1]+'}'),s)
    s = escape(s)
    s = re.sub(r'\*([^*]+)\*',r'\\textbf{\1}',s)
    for i,t in enumerate(tokens): s = s.replace(f'ZZTOKEN{i}ZZ',t)
    if '#' in s or 'ZZTOKEN' in s: raise ValueError('Unhandled source syntax: '+s)
    return s

def table(path):
    text = path.read_text(encoding='utf8')
    cells = re.findall(r'\[([^\[\]]*)\]',text.split('), kind: table')[0])
    columns = text.split('table.header(')[1].split(')')[0].count('[')
    rows = [cells[i:i+columns] for i in range(0,len(cells),columns)]
    caption,label = re.search(r'caption: \[(.*)\]\) <([^>]+)>',text).groups()
    result = '\\begin{table*}[t]\n\\caption{'+prose(caption)+'}\\label{'+label+'}\n\\centering\\small\n'
    result += '\\begin{tabular}{'+'l'*columns+'}\\toprule\n'
    for i,row in enumerate(rows):
        result += ' & '.join(prose(c) for c in row)+r'\\'+'\n'
        if i==0: result += '\\midrule\n'
    return result+'\\bottomrule\\end{tabular}\n\\end{table*}\n'

def body(source):
    lines = source.splitlines(); output=[]; verbatim=False
    for line in lines:
        if line.startswith('```'):
            output.append(r'\end{verbatim}' if verbatim else r'\begin{verbatim}'); verbatim=not verbatim; continue
        if verbatim: output.append(line); continue
        if line.startswith('='):
            match = re.match(r'(=+) (.*)',line)
            output.append('\\'+{1:'section',2:'subsection',3:'subsubsection'}[len(match[1])]+'{'+prose(match[2])+'}')
        elif line.startswith('#include'):
            name=re.search(r'"generated/([^"]+)"',line)[1]
            output.append(table(PAPER/'generated'/name))
        elif line.startswith('#figure(image'):
            cap,label=re.search(r'caption: \[(.*)\]\) <([^>]+)>',line).groups()
            output.append(r'\begin{figure*}[t]\centering\includegraphics[width=\textwidth]{target_resolution.pdf}\caption{'+prose(cap)+'}\\label{'+label+'}\\end{figure*}')
        elif line.startswith('#bibliography'): output.append(r'\begingroup\small\bibliographystyle{sn-mathphys-num}\bibliography{references}\endgroup')
        elif line.startswith('$ ') and line.endswith(' $'):
            output.append(r'\begin{equation}'+math(line[2:-2])+r'\end{equation}')
        elif line.startswith('#'): raise ValueError('Unhandled command '+line)
        else: output.append(prose(line))
    return '\n'.join(output)

def main():
    OUT.mkdir(exist_ok=True)
    shutil.copyfile(PAPER/'references.bib',OUT/'references.bib')
    shutil.copyfile(PAPER/'generated/target_resolution.pdf',OUT/'target_resolution.pdf')
    maintext=(PAPER/'manuscript.typ').read_text(encoding='utf8')
    abstract=maintext.split('*Abstract.* ')[1].split('\n\n*Keywords:')[0]
    assert 150 <= len(abstract.split()) <= 250
    preamble=r'''\RequirePackage{fix-cm}
\documentclass[twocolumn]{svjour3}
\smartqed
\usepackage{amsmath,amssymb,graphicx,booktabs}
\usepackage[numbers,sort&compress]{natbib}
\usepackage[hidelinks]{hyperref}
\providecommand{\bibcommenthead}{}
\providecommand{\burl}[1]{\url{#1}}
\providecommand{\arxivurl}[1]{\url{#1}}
\newenvironment{bchapter}{}{}
\newenvironment{barticle}{}{}
\newenvironment{botherref}{}{}
\newenvironment{bbook}{}{}
\setlength{\emergencystretch}{2em}
\hyphenation{un-known}
\journalname{International Journal of Information Security}
\begin{document}
'''
    title=r'''\title{Legal Label Vocabularies and Attainable Macro F1 in Intrusion Detection Benchmarks}
\titlerunning{Legal vocabularies and attainable macro F1}
\author{Shah Zaib Sajid}
\institute{Shah Zaib Sajid \at Independent Researcher, Rawalpindi, Pakistan\\\email{shahzaibjanjua25@gmail.com}}
\date{}
\maketitle
'''
    article=preamble+title+'\\begin{abstract}\n'+prose(abstract)+r'\keywords{Intrusion detection \and Benchmark evaluation \and Macro F1 \and Label vocabulary \and Reproducibility}\end{abstract}'+'\n'+body('= Introduction'+maintext.split('= Introduction',1)[1])+r'\end{document}'
    (OUT/'manuscript.tex').write_text(article,encoding='utf8')
    supp=(PAPER/'supplement.typ').read_text(encoding='utf8')
    supplement=preamble.replace('[twocolumn]','[onecolumn]')+r'\title{Supplementary mathematical and reproducibility notes}\author{Shah Zaib Sajid}\institute{Independent Researcher, Rawalpindi, Pakistan}\date{}\maketitle'+'\n'+body('= Worst-case'+supp.split('= Worst-case',1)[1])+r'\end{document}'
    (OUT/'supplement.tex').write_text(supplement,encoding='utf8')
    for name in ['manuscript','supplement']:
        commands=[['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex']]
        if name=='manuscript': commands += [['bibtex',name]]
        commands += [['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex']]*2
        for i,cmd in enumerate(commands):
            run=subprocess.run(cmd,cwd=OUT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (OUT/f'{name}-build-{i}.log').write_bytes(run.stdout)
            if run.returncode: raise RuntimeError(run.stdout.decode(errors='replace')[-5000:])
        log=(OUT/(name+'.log')).read_text(encoding='utf8',errors='replace')
        for bad in ['Overfull \\hbox','Overfull \\vbox','Undefined control sequence',
                    'There were undefined references','Citation `','Missing character:']:
            if bad in log: raise RuntimeError(f'Unresolved final LaTeX diagnostic: {bad}')
        print(name, (OUT/(name+'.pdf')).stat().st_size)
    report={'compiler':subprocess.check_output(['pdflatex','--version'],text=True).splitlines()[0],
            'documents':[], 'final_diagnostics':'No overfull boxes, undefined citations/references or missing characters'}
    for name in ['manuscript','supplement']:
        report['documents'].append({'name':name,'commands':'pdflatex; '+('bibtex; ' if name=='manuscript' else '')+'pdflatex; pdflatex',
             'pdf_sha256':hashlib.sha256((OUT/(name+'.pdf')).read_bytes()).hexdigest()})
    folder=ROOT/'review/continuation_20261115';folder.mkdir(parents=True,exist_ok=True)
    (folder/'native_build.json').write_text(json.dumps(report,indent=2),encoding='utf8')

if __name__=='__main__': main()
