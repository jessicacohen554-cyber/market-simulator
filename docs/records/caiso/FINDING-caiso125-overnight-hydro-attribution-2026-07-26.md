# FINDING — caiso-125: the overnight hydro over-supply, attributed by measurement — the charter's premise INVERTS (the p95 ceiling BINDS overnight), every chartered candidate lever is refuted, and the honest driver is fleet shapeability heterogeneity (RoR split) + the evening–overnight spread compression

**Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED. No mechanism armed,
no A/B, nothing registered.** Derive-first session (charter: attack the
caiso-124 §5 overnight over-supply, then re-test the floor on top). The derive
killed every admissible single-delta form before any build, so the chartered
(b)–(d) steps are vacuously closed; this finding is the deliverable, with one
rule-16 diagnostic probe pair as the final attribution instrument.

Committed instruments:
`scripts/probes/_caiso125_overnight_attribution.py` (sections A–I, every number
below reproducible from the two committed caiso-124 bundles + raw EIA-930/923),
`scripts/probes/_caiso125_nightcap_probe.py` (the rule-13-labelled diagnostic
outcome-pin probe runner; out-dirs gitignored, never registered).

Charter Task 2 (re-score caiso-124 under a corrected shape gate) required
explicit owner authorization; none exists in this session, so **caiso-124 stays
KILLED as scored** and its gate constants were not touched.

---

## §1 — the charter premise is INVERTED: the ceiling BINDS overnight

The caiso-125 charter (from FINDING-caiso124 §5) carried "the p95 (month × hod)
hydro ceiling does NOT bind overnight". Measured directly on the committed
`caiso124_control_A` hourlies against the regenerated envelope (instrument §C):

| year | overnight bind share (arm A) | hours model > cap | model mean rank in measured bucket | measured bucket mean / p95 (MW) |
|---|---|---|---|---|
| 2023 | **0.830** | 0 | 0.803 | 2789 / 3382 |
| 2024 | **0.824** | 0 | 0.799 | 2810 / 3355 |
| 2025 | **0.849** | 0 | 0.815 | 2758 / 3334 |

(bind = model ≥ 0.995 × cap; the LP never exceeds the cap in 26,280 hours, so
the envelope is confirmed as the applied bound.) The overnight windows have the
highest bind share of any window alongside `late` (0.80–0.90); the belly is the
only window where dispatch is mostly interior (0.28–0.34).

**The overnight level IS the envelope's p95 level.** The LP rides whatever
overnight cap it is given, because the model's overnight λ (40.3–57.9 $/MWh,
instrument §E) exceeds the month's marginal water value in ~83 % of overnight
hours. Reality's overnight sits at the *middle* of the measured distribution
(model mean percentile-rank 0.80 vs reality's 0.50 by construction). Under
bang-bang budget dispatch, the envelope percentile is not a capability
parameter — it is the dispatch level in every ridden window. The measured
overnight distribution is **water-year-invariant** (mean 2758–2810, p95
3334–3382 across a 24.4 → 21.3 TWh span), so no re-derivation from more data
would narrow it; and re-deriving the frozen percentile against this residual is
exactly what rule 21 forbids.

## §2 — candidate (ii), the water-value adder: REFUTED structurally

Monthly budget utilisation (instrument §D): **bound (≥ 0.995) in 7/5/8 of 12
months** (2023/24/25). Where the budget binds, a constant per-MWh discharge
adder `c` shifts the hydro objective by `c × E` (a constant) and cannot
re-allocate a single MWh within the month. Where it is slack — the
spring-surplus months (2024 Mar–May 0.85–0.91, 2025 Feb–Mar 0.82–0.87), where
the LP already declines water because the residual hours price negative — an
adder *raises the decline threshold*: it removes water from the **lowest-λ
hours first**. The λ ordering (§E: overnight 40–58, belly 22–40) means an adder
cannot touch a single overnight MWh before it has emptied the entire belly —
the exact opposite of both caiso-124 defects. The endogenous water value (the
budget dual) already exists; a second exogenous one would also stack a
mechanism on the same phenomenon (rule 19). **Dead in every branch.**

## §3 — the weekly-budget refinement: measured INERT for the overnight

The natural (i)/(ii) hybrid — tighten the budget grain month → week so scarce
weeks price water above the overnight λ. The LP does exercise cross-week
mobility the hydrograph forbids (instrument §G: weekly |model − meas| mean
46–54 GWh ≈ 12 % of a week, p90 ~116, max ~198; measured nightly variance is
52–59 % week-scale). But the greedy allocation proxy (instrument §H, validated
against arm A's own dispatch first — reproduces its overnight within
29–61 MW) shows the weekly grain moves the overnight mean by only **−20 to
−41 MW** (3070→3050 / 3000→2969 / 3041→3028): scarcity is paid out of the
belly first (λ ordering), and the overnight stays cap-pinned. It *does*
improve nightly hydrograph tracking (across-day r 0.69–0.78 → 0.78–0.82), so
it may have value for a different defect, but **it is not the overnight
lever**; no solve was spent on it.

## §4 — what the overnight residual actually decomposes into

**(a) PS-boundary pollution of the measured series, bounded but not
hod-resolvable.** CISO `NG: WAT` = conventional + pumped-storage net (both
documented in the envelope module); EIA-923 CISO PS net is **−529 / −139 /
+102 GWh** (2023/24/25), implying ~0.5–2.5 TWh/yr of gross pumping whose hourly
placement no on-disk or cleanly-fetchable source resolves (930 has no CISO PS
subseries; CAISO storage reports are battery-only; public bids are masked).
The LP's envelope row is already like-for-like on the model side
(`_build_gen_group_cap_rows`: hydro + PS net discharge ≤ cap, a pumping hour
loosens the row), so this is not a wiring bug — it is an irreducible
uncertainty band on the *measured* side of the comparison. Its measured
signature (instrument §I): the monthly overnight gap regresses on monthly PS
net at slope −1.31 (r −0.48) in 2023 and −2.51 (r −0.44) in 2024 — pump-heavy
months read worse — but the **intercept is +215 / +233 / +307 MW**: at zero PS
activity the overnight gap persists. PS pollution modulates the gap; it does
not explain it.

**(b) The evening–overnight spread compression (the price-formation defect
this lane cannot fix).** Model CA-weighted λ spread (evening − overnight, §E):
**+9.0 / +5.0 / +2.8 $/MWh**; adding the keeper ladder residuals (evening
−5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4) puts the real spread at
**≈ +15.6 / +9.9 / +5.3** — the model compresses the evening premium ~2× in
every year. Water (and battery discharge — model storage nets +148/+165/+421 MW
*discharging* overnight where the real stack pumps/charges) is therefore worth
nearly as much overnight as in the evening to the model, which is why arm B
paid the belly floor out of the evening peak (the K3 kill) instead of the
overnight. This is the caiso-103→108 evening λ-formation lane's defect showing
up in the water allocation; a hydro-side patch for it would be a rule-1
violation by construction.

**(c) The structural driver a future lane CAN fix: fleet shapeability
heterogeneity (the RoR split).** The model's 160–171 hydro units are all free
to shape fully within the fleet envelope; their per-plant water values are
degenerate, so the fleet moves as one bang-bang block. Reality's fleet is
~40–60 % run-of-river/canal plants whose output cannot chase λ. The greedy
proxy with a per-plant CF ≥ 0.45 split (RoR plants flat at their monthly mean,
reservoir pool shaped; instrument §H):

| year | window | measured | arm A | greedy RoR-split | (proxy bias, from validation rows) |
|---|---|---|---|---|---|
| 2023 | overnight | 2796 | 3099 | 2596 | proxy reads ~200–300 low |
| 2023 | belly | 1893 | 1306 | **1877** | — |
| 2024 | overnight | 2815 | 3061 | 2502 | " |
| 2024 | belly | 1536 | 926 | 1302 | — |
| 2025 | overnight | 2758 | 3066 | 2590 | " |
| 2025 | belly | 1292 | 744 | 1156 | — |

One structural change moves **all three windows toward measured at once** —
overnight down ~500 (bias-corrected ≈ 2750–2950 ≈ measured), belly up to
near-measured **without any floor**, evening ≈ measured — because removing the
RoR budget from the shapeable pool raises the reservoir pool's marginal water
value above the overnight λ, which is the one thing §1–§3 showed no
within-envelope lever can do. **It is not armable today:** the ORNL EHA 2024
plant database (fetched and checked this session) carries an operational
`Mode` field keyed to EIA plant ids, but for CISO it is NaN on 100 of 201
plants covering 4.66 of ~6.7 GW — including every large reservoir — and any CF
threshold chosen in-repo is a free parameter fitted next to the residual
(rule 24/13). It also overlaps the min-flow floor's driver (run-of-river
inflow), so rule 19 requires replace-or-reconcile, not stacking. **Arming this
family is an owner ask** (per the lane convention): intake a per-plant
operational-mode classification (EHA `Mode` where present + an explicitly
derived, documented completion for the unclassified plants — FERC licence
class / storage data, not the residual), design the split against the floor
(the floor's Q95 level is the fleet-aggregate shadow of the same physics — the
RoR-split greedy base measures 42.7–60.7 % of budget vs the floor's
35.7–46.3 %), and LOYO-score per rule 22.

## §5 — the rule-16 diagnostic probe: what fills the overnight hole

To answer the charter's candidate-(iii) instruction ("check what displaces
it"), one single-year (2025) throwaway pair was solved at this session's HEAD
(`results/probes/caiso125_ctrl_2025` / `caiso125_nightcap_2025`, gitignored,
NEVER registered): the keeper recipe, and the same recipe with the overnight
(hod 0–6) envelope buckets clamped from p95 to the **bucket mean** — an
explicit rule-13 outcome pin, legitimate only as attribution instrumentation.
Capacity-deliverability partition regenerated first; seam import cap
16,148 MW (delivery year 2025) affirmatively logged in both arms.

Basis note: the fresh HEAD control reproduces the committed
`caiso124_control_A` 2025 **digit-for-digit** (hydro 20.68 TWh, overnight mean
3066 MW, CA demand-weighted λ 36.5750 on this instrument's all-CA-zone
weighting) — the 12-file `4094bbe..HEAD` src window is CAISO-inert, so every
committed-bundle measurement in §1–§4 transfers to this basis exactly, and the
caiso-121/122 basis-drift caveat does not apply to this pair.

The clamp armed as designed ("nightcap clamp ACTIVE CAISO 2025: hod 0-6
ceiling p95 -> bucket mean on 2555 hours (mean cap 2758 MW, was 3337)").
Result (clamped − control, window-mean MW; analyzer in the probe runner):

| window | Δ hydro | Δ gas | Δ import | Δ storage-net | λ ctrl → clamped |
|---|---|---|---|---|---|
| overnight | **−422** | **+254** | +116 | +53 | 42.76 → 43.17 |
| morning | +181 | −82 | −99 | +0 | 33.46 → 32.99 |
| belly | +121 | −57 | −87 | +21 | 22.58 → 21.91 |
| shoulder | +125 | −67 | −68 | +11 | 31.54 → 31.11 |
| evening | +129 | −39 | −9 | −82 | 45.54 → 45.38 |
| late | +63 | −36 | −0 | −27 | 47.10 → 47.00 |

Annual: hydro −0.310 TWh (the clamp partially *declines* the freed water —
a clamp artifact the RoR-split would not share, since its RoR base holds the
belly instead of declining), gas **+0.322 TWh**, import −0.041 TWh, CA λ
36.575 → 36.396 (**−0.49 %**, toward the actual).

Three answers, all in the direction that matters:

1. **The displaced class is GAS** (60 % of the overnight hole; imports 28 %,
   storage 12 %) — the overnight hydro over-supply is a live contributor to
   the C5a gas-volume deficit, the keeper's one load-bearing FAIL. An honest
   overnight fix is worth ≈ +0.3 TWh/yr of gas at 2025 water.
2. **The freed water spreads almost uniformly** over morning / belly /
   shoulder / evening (+121…+181 MW each) rather than concentrating in the
   evening — direct confirmation of §4b: at the model's compressed spread the
   LP is near-indifferent among the day windows, exactly why arm B's floor
   was paid out of the evening peak.
3. **λ moves toward the actual** annually (−0.49 % against a +10.9 %
   C3a-2025 over-price) with only a +0.41 $/MWh overnight rise — an overnight
   fix is C3a-aligned, C5a-aligned and shape-aligned at once, which makes the
   §4c owner ask cheap to justify on rubric grounds.

## §6 — disposition

1. **Nothing armed, nothing registered, keeper unchanged.** All three
   chartered candidates and the weekly-budget hybrid are refuted by
   measurement (§1–§3); the two real drivers are another lane's defect (§4b)
   and an owner-gated structural family (§4c).
2. **The caiso-124 floor was NOT re-tested on top** — with no overnight delta
   armed, "the floor on top" would have re-run caiso-124's own A/B (forbidden
   as a redo; its K3 verdict stands as scored). The §4c RoR-split design is
   where the floor's re-test belongs: the split subsumes the floor's driver,
   so the owner ask covers both in one reconciled family.
3. **Task 3 delivered:** bundles now pin the derived solve inputs — the
   per-ISO CAMPD unit-outage extract family and the clean
   `capacity-deliverability` partition — into the content-addressed
   `shared_inputs` store at solve time
   (`scripts/lib/bundle_io.write_derived_solve_inputs`, wired in
   `run_calibration_full.solve_and_persist`; replay ignores the block by
   design). This closes the last caiso-123 §5 code-external candidate a
   future session could still close: container/partition state is now
   recorded per bundle; only alternate-optimal vertex wander remains
   unpinnable.
4. **Recommended (not built, parallel-lane blast radius):** add a per-tech
   storage hourly sidecar (battery vs pumped-storage split) to the bundle
   writer, so the hydro-lane instruments can score the like-for-like
   `hydro + PS net` aggregate the LP already constrains — the §4a band is
   currently unobservable in committed bundles.

## §7 — DO-NOT-REDO (this lane, additions)

- Re-measuring the overnight bind share / percentile-rank (this finding's §1
  numbers are from the committed bundles; instrument committed).
- Any water-value / opportunity-cost adder on hydro discharge, constant or
  budget-scoped (§2 — inert where bound, anti-directional where slack).
- The weekly (or finer) hydro budget grain as an overnight lever (§3 — the
  greedy proxy measured it inert; a nightly-tracking lane would need its own
  charter and admissibility case).
- Re-deriving the envelope/floor percentiles against this residual (rule 21;
  §1's water-year-invariance shows more data would not move them).
- A CF-threshold RoR split armed in-repo without the external classifier
  intake (the threshold is a free parameter; owner ask filed in §4c).
