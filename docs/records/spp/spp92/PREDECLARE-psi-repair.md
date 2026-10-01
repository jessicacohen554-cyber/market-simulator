# SPP-92 — pre-declaration for the ψ-repair re-run (written BEFORE the re-run's number was computed)

Construction: SPP-53's frozen spec (docs/records/spp/spp53/{parse_2325,psi_regression,aggregate_ttc}.py) verbatim, with
exactly two corrections, both named by prior records and neither a free choice:
1. dependent variable = the actual **bubble-average** S−N spread (EIA-930 sub-BA load-weighted mean of LOAD settlement
   locations over the keeper's own load partition) instead of the SPPSOUTH_HUB − SPPNORTH_HUB spread
   (SPP-53 §0 misalignment (iii): "ψ is the Nebraska-hub → central-Oklahoma-hub sensitivity, not the bubble-to-bubble PTDF");
2. BC clock = GMTIntervalEnd − 1 min − 6 h (CST hour-beginning, the committed LMP parquet's clock, SPP-91 §2) instead of
   the local `Interval` stamp (1 h off in DST months).
L_f unchanged (SPP-53's committed limit table and registry cross-check).

Four cells are reported: (local, hub) = reproduction of 3,355 MW; (GMT, hub); (local, bubble); (GMT, bubble) = the repair.

Recommendation rule (fixed now):
- If the repaired (GMT, bubble) weighted-median T*, rounded to 100 MW, lies inside SPP-53's own stated identification width
  [2,645, 11,121] MW, the 3,400 MW rating is NOT contradicted by the repair → no change, no solve.
- If it lies outside that width, the repair is material → PRECOMMIT + one shard per year (rule 36), direction set by the
  construction, never by the residual.
- If R1 (≥3 identified with an L_f) fails, the construction cannot rate the bubble seam → no change; report it.
Either way the number is reported at full magnitude.
