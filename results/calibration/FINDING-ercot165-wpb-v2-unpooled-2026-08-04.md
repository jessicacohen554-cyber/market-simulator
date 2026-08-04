# FINDING — ercot-165: WP-B v2 is BUILT and A/B-tested. The diurnal-family split is identified and LOYO-stable, both arms clear every pre-registered kill gate and improve [3e] wind curtailment volume — but the charter's SHAPE target is MISSED: the added curtailment lands overnight, not in the mid-afternoon mode the layer exists to close. Arm SHARE dominates arm TIE, and is PROMOTED to keeper.

**Session ercot-165, 2026-08-04.** Two full-span 2023–2025 solves, both
registered (rule 15). **KEEPER → `2026-08-04-ercot165-unpooled-share`**
(arm B), superseding `2026-08-03-ercot158-pool-arm`; determination NOT-YET and
the fail set IDENTICAL in kind (C3a 2023-only, C3b 2023-only, C3c, C7
2023-lignite cv-leg). Charter: `FINDING-ercot164-wpb-nodal-identification-2026-08-04.md` §6,
authorized by the ercot-165 dispatch prompt (the ercot-159/162 precedent).
Pre-registration: `docs/PRECOMMIT-ercot165-wpb-v2-unpooled-curtailment-2026-08-04.md`,
written and pushed **before either arm solved**.

Rule 22: 2023–2025 only. No holdout year solved, scored or read.

---

## 0. Verdict

1. **Phase 0 PASSES — the family split is identifiable without a tuned
   threshold, and it generalizes.** The rule is a pure LIFT test against each
   year's *measured* SCED-execution exposure, so the boundary is the null:
   family D peaks h14–15 and correlates **+0.775 / +0.959 / +0.775** with
   ACTUAL solar curtailment; family N peaks h21–23 (**−0.961 / −0.945 /
   −0.838**). LOYO binding-weighted membership agreement **0.755 / 0.942 /
   0.968**, held-out family-share hod corr **+0.744…+0.999**, and the
   per-family table's LOYO shape correlation **beats the pooled table in every
   year** (D +0.388/+0.424/+0.419, N +0.400/+0.473/+0.473 vs pooled
   +0.347/+0.380/+0.338).
2. **Both arms clear all five pre-registered kill gates in all three years**,
   and both are criterion-for-criterion IDENTICAL to the keeper — same
   PASS/FAIL set, the one C7 failure the same pre-existing 2023-lignite
   cv-leg, D-1/D-2/D-4 verdicts unchanged.
3. **[3e] curtailment VOLUME — the criterion this quantity object is judged on
   — improves materially.** Wind model/reported: keeper .951/.890/.787 (mean
   abs error **0.124**) → tie 1.171/1.032/.935 (**0.089**) → share
   1.109/.974/.887 (**0.083**).
4. **THE CHARTER'S SHAPE TARGET IS MISSED. This is the headline, and Phase 0
   predicted it before the LP ran.** 2025 wind-curtailment hod corr moves only
   −0.077 → −0.066 (tie) / **−0.058** (share) — still negative. The afternoon
   mass share is essentially unmoved (0.159 → 0.158 / 0.159 against actual
   **0.222**) and overnight ticks **UP** (0.357 → 0.362 / 0.360 against actual
   0.266). **The added curtailment landed overnight.** The volume gain is
   therefore a level re-centring effect — the depth re-identified against a
   West-weighted corridor share — not the daytime-mode insight the layer was
   chartered for.
5. **Arm SHARE dominates arm TIE on every axis measured** (volume error 0.083
   vs 0.089; 2025 shape −0.058 vs −0.066; 2023 over-curtailment 11 % vs 17 %),
   and it was the Phase-0 structurally-indicated arm.
6. **What the arms DO fix is real and rule-19-shaped**, independent of the
   shape miss: the keeper has TWO mechanisms owning the Panhandle phenomenon
   and both put it at night, and the pooled share's overnight shape is a
   measured ARTIFACT of union saturation rather than the corridor's pressure
   distribution. Each arm reduces the Panhandle to one owner.
7. **The charter's OTHER half is REFUTED by measurement and is now CLOSED.**
   The rule-14 hypothesis that `data/gtc.py`'s non-active-hour static stand-in
   over-constrains the tie does not survive: measured active-hour p50 over
   static rating is **0.963 / 1.209 / 1.048** for PNHNDL (WESTEX 1.000–1.038,
   NE_LOB 0.966–1.191). The level is right. No `gtc.py` change was built.
8. **Keeper MOVED to arm B**, owner-promoted in-session under the standing
   standard ("If structural integrity improves but gates regress that may
   still be a keeper") on this session's YES recommendation — see §5.

---

## 1. What was built

Two `ScenarioConfig` fields, both **default-off/"tie"**, ERCOT-scoped, in the
run's `run_config.json` (rule 24), with their matrix row in the same PR
(rule 28c):

* `ercot_wtx_curtail_unpooled` — read the per-family share table instead of the
  pooled union.
* `ercot_wtx_panhandle_owner` ∈ {`"tie"`, `"share"`} — the pre-registered A/B.

Data layer: `ercot-wtx-congestion` **schema v2** adds
`congestion_frac_family_d` / `_family_n` / `_pnhndl` (and their count columns)
through the data-intake contract;
`derive_ercot_wtx_curtailment_share.py --family` builds
`data/raw/reference/ercot_wtx_curtailment_share_family.csv` on the SAME
(net-load decile × hod × season) axis.

**Family membership rule (rule 23 — a source-data derive, frozen against
residuals).** An element joins family D exactly when its own binding weight in
h9–17 exceeds the year's *measured* SCED-execution exposure in those hours:

```
family(c) = "D" if day_share(c) > exposure_day(year) else "N"
```

No cutoff, no minimum-n, no per-year tuning. This **replaces** ercot-164's
exploratory `aft>0.30 & n>=200` heuristic. PNHNDL is held out of the split
because its owner is a mechanism choice, not a family; **WESTEX is not** — it
lands in D on its own measured lift (1.074 / 1.216 / 1.074) in all three years,
which is the design call the charter left open, answered from its own data.

**Per-zone assignment.** West takes **D + N additively**, not the saturating OR.
Saturation is exactly what made the pooled union inherit the overnight family's
shape (its mean reaches 0.64 in 2025, so a daytime element binding adds nothing
to the union). The Panhandle zone's ceiling is the A/B.

**DOF: still exactly TWO.** The per-tech depths, re-identified per arm on the
**capacity-weighted** corridor share — weights measured from the EIA-860
operable fleet through the model's own `zone_assignment._ercot_zone` boundaries
(wind 0.630 West / 0.370 Panhandle; solar 0.969 / 0.031). Every corridor zone
is counted, including one whose share an arm zeroes, so both arms are centred
on the same measured curtailment total and differ only in how they distribute
it. Resulting depths: tie 0.1507 / 0.1627, share 0.1354 / 0.1614.

---

## 2. Phase 0 — identification, measured before the LP

Probe `scripts/probes/ercot165_family_split_phase0.py` →
`results/calibration/ercot165_family_split_phase0.json`.

**Vintage duty, on THIS session's own population and the production curate
path's spine (`data/raw/ercot-settlement-points`):**

| year | binding station rows | distinct stations | resolved | endpoint weight |
|---|---|---|---|---|
| 2023 | 216,138 | 693 | 633 (91.3 %) | 92.5 % |
| 2024 | 260,271 | 713 | 644 (90.3 %) | 94.4 % |
| 2025 | 353,416 | 765 | 689 (90.1 %) | 93.0 % |

ERCOT-164's and ERCOT-160's rates are NOT inherited.

**The families, 2025 (full three-year tables in the probe JSON):**

| signal | mean | peak | aft | ovn | day | gapHod | vs act wind | vs act solar |
|---|---|---|---|---|---|---|---|---|
| family D | 0.194 | h9 | 0.294 | 0.181 | 0.563 | **+0.821** | +0.440 | +0.775 |
| family N | 0.507 | h23 | 0.110 | 0.394 | 0.183 | −0.874 | −0.211 | −0.838 |
| PNHNDL | 0.098 | h10 | 0.262 | 0.171 | 0.541 | **+0.961** | +0.628 | +0.684 |
| pooled (as armed) | 0.637 | h23 | 0.157 | 0.324 | 0.297 | −0.705 | +0.054 | −0.815 |

**THE PHASE-0 NEGATIVE, declared in the PRECOMMIT before either solve.** The
bare share profile is not what the driver *does*. On the HSL-weighted bound
reduction — `share(t) × HSL(t)`, what the ceiling actually removes and the
depth's own denominator — the 2025 wind profile's correlation with actual
curtailment goes pooled **−0.001** → D+N **−0.076** → D+N+PNHNDL **+0.012**.
The additive sum is still dominated by family N's weight, and any re-weighting
is precisely the extra DOF the charter fences. The only shape lever available
at two depths is the **per-zone assignment**: the Panhandle zone's ceiling
shape goes from the pooled overnight profile (2025 wind bite corr −0.001) to
the PNHNDL profile (**+0.729**). That is why Phase 0 structurally indicated
arm B, and it is recorded here so it cannot be retro-fitted.

**The second negative — the charter's rule-14 half, refuted.** Measured
active-hour p50 limit over the static rating `data/gtc.py` fills non-active
hours with:

| GTC → link | 2023 | 2024 | 2025 |
|---|---|---|---|
| PNHNDL → Panhandle→North | 0.963 | 1.209 | 1.048 |
| WESTEX → West→North | 1.000 | 1.024 | 1.000 |
| WESTEX → West→South_Central | 1.014 | 1.038 | 1.014 |
| NE_LOB → Northeast→North | 0.966 | 0.969 | 1.191 |

The level is right within ~5 % for PNHNDL in 2023 and 2025 and the direction is
mixed, not one-way. So the manufactured overnight binding is **not** a data
error: it is the reduced network's *aggregate* flow reaching a correct cap in
hours the real *nodal* system had headroom — a topology-resolution limit, and
the West/Panhandle topology split stays CLOSED. Releasing the cap on
non-active hours would be a fabricated relaxation with no forward analogue
(rule 13) and is refused. **No `gtc.py` change was built**, which also keeps
NE_LOB out of the A/B as a confound.

---

## 3. The A/B result

Runs `2026-08-04-ercot165-unpooled-tie` (`ercot165_unpooled_tie_A`) and
`2026-08-04-ercot165-unpooled-share` (`ercot165_unpooled_share_B`), single-delta
replays off the keeper via `scripts/replay_keeper.py --set`. Scorer
`scripts/probes/_ercot165_unpooled_ab.py` →
`results/calibration/_ercot165_unpooled_ab.json`.

**[3e] wind curtailment, model / reported TWh:**

| | 2023 | 2024 | 2025 | mean abs err |
|---|---|---|---|---|
| keeper | 5.73 / 6.03 | 6.39 / 7.17 | 6.89 / 8.76 | 0.124 |
| A tie | 7.06 / 6.03 | 7.40 / 7.17 | 8.19 / 8.76 | 0.089 |
| B share | 6.69 / 6.03 | 6.99 / 7.17 | 7.76 / 8.76 | **0.083** |

Solar is marginally WORSE in both arms (2025 ratio .862 → .843).

**The §4 shape — the target:**

| | 2025 hod corr | aft (act .222) | ovn (act .266) |
|---|---|---|---|
| keeper | −0.077 | 0.159 | 0.357 |
| A tie | −0.066 | 0.158 | 0.362 |
| B share | −0.058 | 0.159 | 0.360 |

**Kill gates:** K1 over-curtailment, K2 shape regression, K3 zonal starvation,
K4 C2 collapse, K5 spurious scarcity — **ALL CLEAR, both arms, all years**
(zero new tail hours vs the keeper's set in every year).

**Rubric criteria:** identical PASS/FAIL set to the keeper. C3a 2023 −32.8 % →
−32.5 / −32.6 %, 2025 −8.1 % → −7.7 / −7.9 %; C2 2025 gas −2.0 % → −1.5 /
−1.7 %; C1/C4/C8 PASS; C7 the same 2023-lignite failure. Governance shows
UNATTESTED only because a candidate bundle carries no
`calibration_attestation.json` — not a model result.

---

## 4. Reported against interest

* The mechanism does not do what the charter said it would. The daytime mode is
  not recovered; the extra curtailment is overnight, where the model already
  over-weighted.
* **2023 flips from 5 % UNDER-curtailment to 11 % (share) / 17 % (tie) OVER.**
  The keeper's 2023 wind volume was its best year (.951); both arms give that up.
* Solar volume degrades slightly in both arms.
* The volume improvement is attributable to the depth re-centring on a
  West-weighted corridor share, not to the family decomposition. The
  decomposition's demonstrated value is that it *enables* the per-zone
  assignment and removes PNHNDL's mis-broadcast from the West share — not that
  it re-times the West ceiling.
* **Known confound, bounded.** The committed pooled share table is a 2026-07
  vintage that no longer byte-reproduces from today's archives (870 vs 872
  cells, mean |Δ| 0.019). The keeper solved on the committed vintage; both arms
  solve on tables derived from today's sources. Effect is negligible —
  re-deriving the pooled table from current sources gives hourly corr
  0.992–0.993 and **hod corr 0.9997–0.9999**, mean share moving < 0.002. The
  committed pooled CSV was left untouched (rule 23), and the derive gained
  `--family-only` so it cannot be clobbered incidentally.

---

## 5. Promotion — RECOMMENDED and EXECUTED

**Arm B (`2026-08-04-ercot165-unpooled-share`) is the ERCOT keeper.** The
session recommended it; the owner promoted it in-session on the standing
standard. The case is rule 1 structural fidelity, not the fit: the keeper
carries a rule-19 defect (two mechanisms owning the Panhandle, both overnight)
and a share whose diurnal shape is a measured artifact of union saturation;
arm B removes both, at zero new DOF, with every kill gate clear, no criterion
regressed, two criteria marginally improved, and the [3e] criterion it is
judged on improved from 0.124 to 0.083 mean absolute error.

**What the promotion does NOT claim.** The build was authorized to deliver the
mid-afternoon mode and it does not deliver it. The promotion is NOT justified by
the volume gain — that gain is traceable to depth re-centring — and the missed
target is carried verbatim in the bundle's `calibration_attestation.json` and in
the keeper's `market_story`, where the daytime mode is named an OPEN ROOT-CAUSE
ISSUE rather than a calibrated behaviour. Executed: attestation generated
(`n_entries` 10 → 11, `n_residual` UNCHANGED at 6 — the added entry is
measured/published, not residual), `frontend/data/backcast/keepers/ERCOT.json`
set, `scripts/build_status.py --iso ERCOT`, `scripts/audit_keepers.py --iso
ERCOT` PASS (0 failures, 0 warnings), and the `calibration-keeper-auditor` agent
run scoped `--iso ERCOT`. No re-key duty — ERCOT holds no `complete` marker.

**Successor question, named not chartered.** The daytime mode remains
unexplained by any armed mechanism. Phase 0 shows the signal that carries it is
PNHNDL enforcement incidence (2025 wind bite corr +0.729) and the afternoon
nodal minority — but at the two-depth budget their weight cannot reach the
West zone. Closing it needs either a declared identification source for a
per-family weight (an owner decision, explicitly fenced by the ercot-164
charter) or a different object entirely. Do not re-open it as a re-weighting
without that declaration.

---

## 6. Governance attestation

* **Rule 15** — both arms registered on the dashboard in-session, keeper and
  probe alike; retention sweep pruned ercot139 and ercot140.
* **Rule 16** — each arm is one bundle spanning 2023, 2024, 2025.
* **Rule 12** — years sequential within each invocation. Both arms were first
  launched concurrently; **arm A was OOM-killed at ~6 min** on this 15 GB box
  (two ERCOT per-plant solves do not fit), so the arms were serialized and arm
  A was re-run from a cleaned output directory. Recipe unchanged.
* **Rules 22 / R-HOLDOUT** — 2023–2025 only; 2020–2022 NP6-86 archives unread
  by the derive; no holdout year touched.
* **Rule 19** — D-2 attribution done before proposing (ercot-164 §2); the build
  is a reconciliation to ONE Panhandle owner, not a third mechanism.
* **Rule 13/14** — every input is measured SCED binding incidence or
  enforcement structure; the actual-minus-model gap was a DIAGNOSTIC target
  only and no share, threshold or family is fit to it; depths remain the sole
  outcome-anchored scalars.
* **Rule 20 [R-DOF]** — two free scalars, unchanged. Family membership and the
  corridor zone weights are source-data derives.
* **Rules 24 / 25** — both fields in `ScenarioConfig` and `run_config.json`, no
  env-var channel, ERCOT-scoped.
* **Rule 28b/c** — matrix cell `wtx_curtail_unpooled` ERCOT stamped `O` with
  its evidence citation, and the row landed in the same PR as the fields.
* **Scope fence honoured** — item 8 not re-opened; the West/Panhandle TOPOLOGY
  SPLIT stays CLOSED (the families are share-table resolution, sub-zonal by
  construction); no CC commitment-state object, CC re-pricing, storage-offer
  lane, `energy_online_capability_cap`, envelope family, per-hour HSL cap,
  `ercot_shoulder_online_span`, offer-LEVEL program or
  `ercot_ordc_only_scarcity` touched.
* **ERCOT remains NOT-YET.** No frontier or `complete` claim is made.
