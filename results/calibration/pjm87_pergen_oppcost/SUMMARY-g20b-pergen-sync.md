# PJM 87 — per-generator OPPORTUNITY-COST reserve co-opt (G-20b successor)

**Probe (not a keeper). Keeper decision pending the pjm-86 same-tree A/B.**
Full span 2023–2025, one bundle, years sequential. Branch
`claude/pjm-pergen-oppcost-coopt-w4a-15y95u`. Solved on the current
`data/clean` tree (freshly regenerated) with the per-BA EIA-930 PJM demand
rewire (`eia_loader._load_pjm_hourly_demand`, this session).

## What was run

pjm-83 keeper recipe **verbatim** + the per-gen opportunity-cost build the
pjm-84/pjm-85 verdict relocated the residual to (`SUMMARY-g20b-pathb.md`:
"the $75–200 residual is the sub-shortage opportunity-cost reserve price,
which requires reserve to compete with energy on the same marginal unit"):

- `pjm_reserve_pergen=True` — (zone, fuel-class) pooled `R ≤ ramp10` co-opt
  (miso-39 memory tier, pjm-81 layout: joint `Σ P + R ≤ Σ cap` per pool-hour,
  measured RTO + MAD Primary families, published two-step ORDC).
- `pjm_reserve_pergen_sync=True` (**new**) — the pjm-81 non-fire fix:
  (i) the Synchronized sub-product as its own measured balance families
  (RTO `sr_req_mw` + MAD `mad_sr_req_mw`, published Synchronized ORDC rows
  as filed); (ii) each pool's R column split into a SYNC product (online
  10-min ramp only) and a NON-SYNC product (offline fast-start ramp, Manual
  11 sec 4.2), sharing the pool's joint P+R headroom row; (iii) sync caps
  online-scoped at the P0→P1 seam from the model's own P0 run pattern (the
  pjm-85 plant-online derivation, min-down gaps bridged) applied to the
  RESERVE bounds only — energy availability is NOT masked, so P1's free
  energy redispatch around the held reserve is what prices the opportunity
  cost.
- `measured_ramp_capability=True` (kept from pjm-81/84/85, rule 14).

Published two-step ORDC unchanged; Synchronized rows read from the same
cited curve CSV — no breakpoint/penalty edit (rule 11).

## Result — the mechanism fires nontrivially for the first time

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| reserve dual > 0 (h) | **133** | **44** | **50** |
| — of which afternoon (11–18h) | 62 | 43 | 35 |
| band $0–10 (h) | 131 | 41 | 38 |
| band $10–80 (h) | 2 | 3 | 12 |
| band $80–300 / $300+ (h) | 0 / 0 | 0 / 0 | 0 / 0 |
| max dual ($) | 11.4 | 11.5 | 31.4 |
| mean dual when positive ($) | 1.1 | 4.6 | 7.6 |
| demand-wtd LMP mean ($) | 29.47 | 28.01 | 38.13 |

Contrast with pjm-81's naive per-gen probe (joint headroom let idle capacity
back reserve): that fired **1 hour in 3 years**. Composing the per-gen ramp
limit **with** the online/offline product split fixes the non-fire — the
mechanism now engages in double digits to low hundreds of hours per year.

**No penalty-step firing anywhere.** Every positive dual stays under $32 —
nowhere near the $300 (Step 2) or $850 (Step 1) shortage penalties. This
confirms the mechanism prices strictly in the intended sub-shortage
opportunity-cost regime, not the shortage regime a naive tightening would
produce.

## Honest read — partial, not residual-closing

The design goal was a **$10–80 afternoon opportunity-cost band**. What
fired instead is overwhelmingly the **$0–10 band** (131/41/38 of the
133/44/50 positive hours), with only a handful of hours per year reaching
the $10–80 target band (2/3/12). The PJM afternoon $75–200 residual
(`pjm-lmp-residual.md`) is **not closed** by this mechanism at its current
magnitude — it is a genuine, correctly-structured, non-fitted opportunity-
cost signal, but a small one. No breakpoint was lowered and no penalty was
inflated to manufacture a bigger number (rule 11); this is the honest
in-LP result of the measured requirement, published curve, and physics-
gated online/offline ramp split.

## A/B vs pjm-86 (same-tree, flags off) — criterion-identical

`calibration_verdict.py` full C1–C8 scoring is **byte-for-status identical**
between this run and the `pjm86_pjm83_head_baseline` flag-off partner: not
one criterion's PASS/FAIL/CAVEAT/SKIPPED status differs. C3c (price tail /
scarcity, DA-expressible) **FAILs in both** — the mechanism does not clear
this gate at its current magnitude. C3b (price shape) is CAVEAT in both.
C1 fuel-mix per-class TWh deltas are ≤0.03 TWh/yr (CT_PEAKER ≤0.01 TWh/yr
either direction, out of 20–32 TWh/yr class volume) — confirming near-zero
dispatch redistribution, consistent with the small dual magnitude above.

## #1484 (CT_PEAKER C8 drag share) — no material movement to reconcile

CT_PEAKER class volume moves by ≤0.01 TWh/yr vs the pjm-86 baseline (2023
+0.0098, 2024 −0.0043, 2025 −0.0082 TWh — noise-level, <0.05% of the class's
20–32 TWh/yr total). No real reserve product absorbed CT_PEAKER value at a
magnitude worth D-2 reconciliation (rule 19); #1484's drag share is
unchanged from pjm-83's already-registered 9.0/14.6/10.3% (2023/24/25).

## Verdict — structurally real, criterion-neutral (the pjm-81 pattern, fixed)

Unlike pjm-81 (1 fired hour / 3 yr, effectively inert), pjm-87 fires
nontrivially and stays correctly in the opportunity-cost regime (never
crosses the $300 penalty step). But like pjm-81, it moves **zero** C1–C8
criteria — not a promotion case on its own. Mechanism retained for the next
keeper cycle (rule 1: right structure first); keeper decision (whether to
adopt alongside pjm-83, or hold pending a magnitude follow-up) is the
owner's call — see the session's `AskUserQuestion` for the DOF ledger /
ablation-twin tradeoff (rule 20/21 apply only if this is promoted).
