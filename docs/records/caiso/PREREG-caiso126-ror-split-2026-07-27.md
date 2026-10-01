# PRE-REGISTRATION — caiso-126 RoR-split family (classifier split + reconciled Q95 floor)

**Written and committed BEFORE arm B was solved.** No B-arm result existed when
this document was frozen. Gates below are final — a gate this document does not
contain cannot be quoted as a pass. Format follows
`PREREG-caiso124-hydro-min-flow-floor-2026-07-26.md`.

Owner grant (the caiso-126 charter): building the RoR-split mechanism
default-off and running its A/B is GRANTED; promotion is NOT pre-granted, and
the caiso-124 shape-gate re-score stays untouched.

---

## §1 — the delta (ONE reconciled family, two registered switches)

**Arm B** = the `2026-07-23-caiso-netrev-margin-keeper` recipe replayed at this
session's HEAD **plus the reconciled RoR family**:

```
scripts/replay_keeper.py results/calibration/caiso_netrev_margin \
    --out-dir results/calibration/caiso126_rorsplit_B \
    --set hydro_ror_split=true --set hydro_min_flow_floor=true \
    --note "caiso-126 RoR-split + reconciled Q95 floor (one family)"
```

- **Arm A** `results/calibration/caiso126_control_A` — keeper recipe, no
  delta, same HEAD, same container, same regenerated `capacity-deliverability`
  partition (2025 seam import cap affirmatively verified at **16,148 MW**
  before either solve). NOT registered (FINDING-caiso92b protocol).
- Both arms `--year 2023 2024 2025` in one invocation (rule 16), years
  sequential within each run, arms sequential to each other (rule 12; CAISO is
  single-solve-only on this 15 GB box).

Both switches arm ONE mechanism family (rule 19), per the charter's
"floor-reconciled, single family" and FINDING-caiso125 §6.2 ("the caiso-124
floor's re-test lives INSIDE this family" — a floor-only arm would be a
caiso-124 redo, forbidden):

| half | driver / level |
|---|---|
| `hydro_ror_split` | plants the EXTERNAL hydro-plant-modes classifier (ORNL EHA FY2024 `Mode` + the documented categorical HILARRI/Corps-dam completion, curated by `scripts/data/curate_hydro_plant_modes.py`, validated residual-blind at 86/97 plants / 84.7 % of labeled MW) marks non-shapeable dispatch FLAT at their own measured monthly water, `budget[g,m]/hours[m]` (min_gen == availability cap == the flat level, `MECH_HYDRO_ROR_FLAT`, D-4 window h0-23). |
| `hydro_min_flow_floor` (reconciled) | the caiso-124 mechanism UNCHANGED in level and derivation (frozen mirrored Q95, rule 21), but allocated over the RESERVOIR class only at `max(0, Q95[m] − RoR_base[m])` — so the total forced sustained base equals the frozen Q95 evidence exactly, never stacked (rule 19). No RoR unit carries both stamps (test-pinned). |

**DOF added: zero.** The classifier is categorical-external (no threshold —
the caiso-125 CF-cut is exactly what this intake replaces); the flat level is
the plant's own budget; the floor level/percentile is caiso-124's, untouched.

Classifier coverage measured on the LP fleet (intake session, before any
solve): RoR-class = 67/61/61 of 166/160/160 plants, **12.5 / 11.1 / 10.3 % of
the 2023/24/25 budget** — the caiso-125 §4c "~half the fleet" was plant-COUNT;
energy-weighted the CISO RoR class is a ~1/9 minority. Monthly RoR flat base
128–385 MW vs floor Q95 30–2,102 MW ⇒ the reservoir class carries most of the
sustained-base evidence (the reconciliation direction is floor-dominant).

## §2 — baseline (arm A expectation, measured off the committed caiso-124 bundles)

From `caiso124_control_A` (same recipe class; caiso-125 measured the
`4094bbe..HEAD` window CAISO-inert) and EIA-930 `NG: WAT`:

| quantity | 2023 | 2024 | 2025 |
|---|---|---|---|
| overnight (hod 0-6) hydro, model − measured (MW) | **+303** | **+246** | **+308** |
| belly (hod 9-15) hydro, model − measured (MW) | −587 | −610 | −548 |
| evening (hod 17-21) hydro, model − measured (MW) | +110 | −143 | −19 |
| overnight envelope bind share | 0.830 | 0.824 | 0.849 |
| hydro D-1 profile r / cv_ratio (model/actual) | 0.958 / 1.44-ish | 0.972 / 1.44 | 0.982 / 1.42 |

Arm A is expected to reproduce these within vertex-wander noise; a material
divergence is itself a finding (the caiso-123 §5 residual class) and is
reported, not absorbed.

## §3 — derive-first effect prediction (recorded BEFORE the solve)

The caiso-125 greedy proxy re-run with the HONEST classifier split (fixed
arm-A λ, no feedback; validation rows reproduce arm A within ~30-60 MW):

| year | overnight Δ (proxy) | belly Δ (proxy) | needed to close |
|---|---|---|---|
| 2023 | −55 | +95 | −303 / +587 |
| 2024 | −132 | +156 | −246 / +610 |
| 2025 | −49 | +95 | −308 / +548 |

At fixed prices the honest split closes only ~15-25 % of the overnight gap —
**the PRIMARY gates below may well fail, and that is an acceptable, registered
outcome** (rule 15). The A/B remains decisive because the proxy CANNOT
represent the mechanism's actual channel (FINDING-caiso125 §4c): removing the
RoR budget from the shapeable pool raises the reservoir pool's endogenous
marginal water value, and whether it crosses the overnight λ (40-58 $/MWh) is
an LP-feedback question no fixed-λ instrument answers. The floor half
additionally supplies the caiso-124 belly lift (−98/−54/−84 residual gaps in
its arm B) with the split now holding a flat base the LP cannot pay out of the
evening peak.

## §4 — PRIMARY gates (the family's OWN gates — rule 1: never judged on C3a recovery)

All three years must clear each.

- **P1 overnight.** |overnight (hod 0-6) hydro gap| ≤ **150 MW** in every
  year, AND strictly smaller than arm A's |gap| in every year.
- **P2 belly.** |belly (hod 9-15) hydro gap| strictly smaller than arm A's in
  every year.
- **P3 shape = the D-1 PAIR as C7 scores it** (the caiso-124 §2/§3 lesson —
  NOT raw profile-r-vs-control, whose 24-point correlation penalised the
  amplitude correction it should have rewarded): in every year, (a) hydro
  diurnal `profile_r` ≥ **0.8** (the rubric's `d1_min_profile_r`, C7's own
  absolute gate), AND (b) amplitude error |`cv_ratio` − 1| ≤ arm A's
  |`cv_ratio` − 1| (cv_ratio = model/actual off-peak CV as
  `legitimacy_diagnostics.d1_shape_metrics` computes it).
- **P4 mechanism accounting clean.** `legitimacy_diagnostics.json` carries
  D-2 rows for `hydro_ror_flat` (and `hydro_min_flow`) and D-4 rows with
  off-window share **0.0000** for both (window is all-hours — any non-zero is
  a wiring bug); no unit carries both stamps; both mechanisms sit in
  `NON_THERMAL_MECHS` (never a merchant thermal C8 budget consumer). Forced
  share is *reported* (expected: RoR flat ~10-13 % of hydro energy + the
  reconciled floor's remainder ≈ the caiso-124 30-46 % class total).

## §5 — KILL criteria (any one ⇒ family rejected as armed, whatever the headline)

- **K1 evening regression.** |evening (hod 17-21) hydro gap| > **300 MW** in
  any year, either direction (arm A sits at +110/−143/−19 — well inside — so
  any breach is the delta's own doing; this is the charter's kill, subsuming
  caiso-124's K1/K2 pair at the tighter bound).
- **K2 C8 breach.** Any new C8 forced-share breach on a merchant thermal
  class traceable to the family (it forces no thermal unit — a breach means
  the mechanism leaked outside the hydro fleet).
- **K3 off-window binding.** D-4 off-window share > 0 for `hydro_ror_flat` or
  `hydro_min_flow`.
- **K4 infeasibility / derivation disagreement.** Any LP infeasibility; the
  floor allocator's feasibility clip binding on any reservoir plant-month; or
  the RoR nameplate clip discarding > 1 % of the RoR class's annual budget
  (2023 measures 23 small plant-months clipped — the loss must stay
  immaterial or the source data is wrong, not the result).

## §6 — SECONDARY, directional only (reported, never pass/fail for this family)

- **S1 C5a/C3a direction** (the caiso-125 §5 probe case): an honest overnight
  fix displaces the overnight excess into GAS (+≈0.3 TWh/yr at full closure)
  and moves CA λ toward the actual. Both deltas reported with sign.
- **S2 rubric verdicts** C1-C8 for both arms (official
  `calibration_verdict.py` scores). C3a-2025 is expected to read ≈ +11 % in
  BOTH arms (the caiso-123 attributed extract basis, not this delta — the
  family is neither credited nor debited for it).
- **S3 parks-at-zero and bind share**: hours < 10 MW / < 100 MW, overnight
  envelope bind share, budget utilisation — both arms.

## §7 — rule-22 LOYO statement

The family carries **zero fitted parameters** — the classifier is external
and categorical, the flat level is the plant's own measured budget, and the
floor level is the frozen caiso-124 mirror percentile. There is nothing to
re-estimate under a held-out year, so leave-one-year-out reduces exactly to
the per-year consistency the PRIMARY gates already enforce (each year must
improve independently; no year's result can tune another's input). A
promotion discussion (owner-gated regardless, §8) cites the three per-year
gate outcomes as the LOYO record.

## §8 — what a PASS does and does not authorize

A pass (or any completed A/B) registers arm B on the backcast dashboard
(rule 15, top-15 retention). **Promotion to the keeper is an OWNER call
regardless of score** — and it still sits behind the two open sequencing
decisions this session does not touch: the extract over-count freeze
(neiso-66, ACTIVE) and the caiso-123 §6 re-tune-vs-wait question. Arm A is
not registered. Nothing here promotes anything, and the caiso-124 verdict
stays KILLED as scored (its re-test lives inside this family's B arm only).

Rule 21 applies to the classifier from this point: the hydro-plant-modes
table re-derives only when the EHA/HILARRI source vintages update, never
because a residual moved.
