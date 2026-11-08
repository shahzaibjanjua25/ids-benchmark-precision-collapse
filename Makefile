PYTHON ?= python
DATA ?= data
REFIT_OUT ?= fresh_unsw

.PHONY: verify reproduce refit solvers
verify:
	$(PYTHON) code/check_availability.py
	$(PYTHON) code/check_vocabulary_groups.py
	$(PYTHON) code/verify_release_evidence.py
	$(PYTHON) code/verify_cic_archive.py results

reproduce:
	$(PYTHON) code/reproduce_release.py --mode saved

solvers:
	$(PYTHON) code/reproduce_release.py --mode solvers

refit:
	$(PYTHON) code/run_unsw_extended.py "$(DATA)" results --fresh --outdir "$(REFIT_OUT)"
