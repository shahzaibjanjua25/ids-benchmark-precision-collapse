PYTHON ?= python
DATA ?= data
REFIT_OUT ?= fresh_unsw

.PHONY: verify reproduce refit
verify:
	$(PYTHON) code/check_availability.py
	$(PYTHON) code/verify_cic_archive.py results

reproduce: verify
	$(PYTHON) code/audit_scoring_conventions.py results
	$(PYTHON) code/run_solver_shapes.py results/solver_shapes.csv
	$(PYTHON) code/run_unsw_extended.py "$(DATA)" results

refit:
	$(PYTHON) code/run_unsw_extended.py "$(DATA)" results --fresh --outdir "$(REFIT_OUT)"
