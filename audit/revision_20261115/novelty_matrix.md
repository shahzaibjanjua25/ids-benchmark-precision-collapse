# Novelty assessment

| Prior work | Verified subject | Relationship | Remaining distinction / uncertainty |
|---|---|---|---|
| Opitz and Burst, arXiv:1911.03347 | Two macro-F1 formulas and ranking differences | Strong prior evaluation-metric context | Does not itself establish the inspected fold-vocabulary grouped oracle |
| Forman and Scholz, DOI 10.1145/1882471.1882479 | Aggregation pitfalls in CV | Pooling is established prior concern | We condition on explicitly fold-dependent output legality |
| Opitz, DOI 10.1162/tacl_a_00675 | Metric properties and evaluation practice | Broad metric analysis is prior work | Present implementation adds legal-vocabulary feasible-set audit |
| Narasimhan et al., PMLR 37:2398-2407 | Confusion-matrix objectives in learning | Optimization of metrics is established | Here truth and vocabulary constrain an oracle; no learning consistency claim |
| Reis, DOI 10.3390/electronics15143090 | Explicit multiclass coverage mismatch under scenario splitting | Direct evidence the practical issue is already recognized | No inspected exact pooled vocabulary oracle; do not claim discovery of mismatch |
| CLAIRE, DOI 10.3390/electronics14224547 | Selected training-label coverage | Label coverage is not a new concept | Fold-weighted test-row coverage differs from selected-class fraction |
| OpenTriIDS, DOI 10.3390/s26206369 | Explicit scored unknown operational output | Confirms training absence does not imply unknown-output illegality | Our audit must declare the transformed three-label task |
| Xin et al., arXiv:2609.36039 | Multi-tier IDS benchmark | Hierarchical target comparisons are already explored | Preprint; abstract-level inspection, not evidence of first taxonomy analysis |
| Balikas et al., Efficient Model Selection for Regularized Classification by Exploiting Unlabeled Data, DOI 10.1007/978-3-319-24465-5_3 | Author-hosted search record describes quantification bounds for model selection | Potentially relevant earlier F1 bound | PDF retrieval timed out; not ruled out. No mathematical priority claim made |

The elementary inequality follows from TP <= covered support and FP >= 0.
It should not be advertised as a fundamentally new F1 theorem. The most substantial
candidate contribution is the exact feasible-set characterization with mandatory
false-positive allocation, grouping, complexity analysis and an auditable software
interface. Literature priority for that characterization is not conclusively
established. Rational certificates are an engineering improvement, not automatically
a new optimization method. The manuscript states these boundaries.
