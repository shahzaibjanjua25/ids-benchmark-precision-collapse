#figure(table(columns: (1fr, 1fr, 1fr, 1fr),
inset: 5pt, stroke: 0.4pt,
table.header([Pipeline],[Fine / support],[Fine / union],[Five categories]),
[Random Forest],[0.242 (0.011)],[0.236 (0.010)],[0.482 (0.007)],
[Extra Trees],[0.224 (0.001)],[0.218 (0.001)],[0.481 (0.004)],
), kind: table, caption: [Fresh NSL-KDD fits with matched preprocessing. Mean macro F1 (sample SD) over seeds 42--44; all six fits share the official test cohort. Fine support ceiling 0.553; five-category ceiling one.]) <tab-nsl>
