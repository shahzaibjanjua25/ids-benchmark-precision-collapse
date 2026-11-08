"""One-command saved-table regeneration or a separate raw-data refit."""
import argparse
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode',choices=['saved','solvers','refit'],default='saved')
parser.add_argument('--out',type=Path)
parser.add_argument('--data',type=Path,help='UNSW official CSV directory')
parser.add_argument('--cic',type=Path,help='CIC MachineLearningCVE directory')
parser.add_argument('--nsl',type=Path,help='NSL original partition directory')
parser.add_argument('--gas',type=Path,help='UCI gas zip archive')
args=parser.parse_args()
def run(script,*params):
    command=[sys.executable,'-B',str(root/'code'/script),*map(str,params)]
    print('Running',script,flush=True)
    subprocess.run(command,cwd=root,check=True)
if args.mode=='saved':
    run('audit_nsl_destinations.py')
    run('audit_nsl_granularity.py')
    run('audit_cic_target_resolution.py')
    run('verify_release_evidence.py')
    run('verify_cic_binary_lodo.py')
    run('verify_published_score_audit.py')
    run('verify_cic_archive.py',root/'results')
    run('build_main_tables.py')
    run('plot_cic_hero.py',args.out or root/'regenerated_figures')
elif args.mode=='solvers':
    run('check_availability.py')
    run('check_vocabulary_groups.py')
    run('exact_fold_oracle.py',root/'results','--method','branch')
    run('run_solver_shapes.py',args.out or root/'results/solver_shapes_rerun.csv')
else:
    if any(x is None for x in [args.out,args.data,args.cic,args.nsl,args.gas]):
        parser.error('refit needs --out, --data, --cic, --nsl and --gas')
    if args.out.exists(): parser.error('refit --out must be a new directory')
    args.out.mkdir(parents=True)
    run('clean_repo/ids_full_study.py','--datasets','cic','--cic-dir',args.cic,
        '--out',args.out/'cic','--cic-seeds',42,'--cic-n-estimators',100,
        '--rf-arms','none','balanced_subsample','--no-threshold')
    run('run_nsl_kdd_forest.py',args.nsl,args.out/'nsl_forest','--seeds',42,43,44,45,46)
    run('run_nsl_family_seeds.py',args.nsl,args.out/'nsl_families')
    run('clean_repo/ids_full_study.py','--datasets','unsw','--unsw-dir',args.data,
        '--out',args.out/'unsw_official','--unsw-models','rf','--unsw-protocols','official',
        '--unsw-variants','raw','--rf-arms','none','--seeds',42,43,44,45,46,'--no-threshold')
    run('run_rank_audit.py',args.data,args.out/'unsw_rank')
    run('run_gas_drift.py',args.gas,args.out/'gas_adjacent','--fit')
    run('run_gas_models.py',args.gas,args.out/'gas_models')
    run('run_digits_fractional_coverage.py',args.out/'digits')
    print('Raw-data refit complete. Outputs remain separate from the frozen release results.')
