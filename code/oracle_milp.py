"""Exact integer-count formulation for modest total uncovered support."""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from label_availability.core import _prepare


def solve_milp(counts, time_limit=20):
    _, _, n, m, active = _prepare(counts)
    scored = n > 0
    classes = int(scored.sum())
    ceiling = float((2 * m[scored] / (n[scored] + m[scored])).mean())
    x = [(f, dest, amount) for f, (amount, allowed) in enumerate(active) for dest in allowed]
    max_fp = [sum(amount for amount, allowed in active if k in allowed) for k in range(len(n))]
    if sum(max_fp) > 20000:
        raise ValueError("Integer count grid too large for this MILP formulation")
    z = [(k, amount) for k in range(len(n)) for amount in range(max_fp[k] + 1)]
    objective = np.zeros(len(x) + len(z))
    matrix = lil_matrix((len(active) + 2 * len(n), len(objective)))
    target = np.r_[np.ones(len(active)), np.zeros(len(n)), np.ones(len(n))]
    for j, (fold, dest, amount) in enumerate(x):
        matrix[fold, j] = 1
        matrix[len(active) + dest, j] = amount
    for j, (k, amount) in enumerate(z, start=len(x)):
        matrix[len(active) + k, j] = -amount
        matrix[len(active) + len(n) + k, j] = 1
        if m[k]:
            base = int(n[k]) + int(m[k])
            objective[j] = 2 * int(m[k]) * amount / (base * (base + amount)) / classes
    result = milp(objective, integrality=np.ones(len(objective)), bounds=Bounds(0, 1),
                  constraints=LinearConstraint(matrix.tocsr(), target, target),
                  options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    dual = getattr(result, "mip_dual_bound", None)
    return {"milp_status": int(result.status), "milp_variables": len(objective),
            "milp_feasible_score": ceiling - result.fun if result.fun is not None else np.nan,
            "milp_score_upper": ceiling - dual if dual is not None else ceiling}
