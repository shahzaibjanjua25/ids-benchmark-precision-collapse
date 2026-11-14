#figure(table(columns: (1fr, 1fr, 1fr, 1fr),
inset: 5pt, stroke: 0.4pt,
table.header([Pipeline],[Fine / support],[Fine / union],[Five categories]),
[Random Forest],[0.239 (0.013)],[0.233 (0.013)],[0.483 (0.001)],
[Extra Trees],[0.223 (0.001)],[0.217 (0.001)],[0.483 (0.003)],
), kind: table, caption: [NSL-KDD overlap-controlled refits: 658 training rows removed by exact feature identity, full test cohort retained. Mean macro F1 (sample SD) across three seeds. Vocabulary ceilings are unchanged.]) <tab-overlap>
