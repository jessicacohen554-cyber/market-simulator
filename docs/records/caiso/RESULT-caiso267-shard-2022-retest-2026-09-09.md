# RESULT — caiso-267 shard: the **2022 VALIDATION RE-TEST** of the fossil offer-band ×0.92 arm

**Session caiso-267 (parallel shard), 2026-09-09.** Branch `claude/caiso267-shard-2022`.
Run id **`2026-09-09-caiso-267-fossil92-2022`**, bundle `results/calibration/caiso267_fossil92_2022`.

This shard solved, scored and registered **2022 only**. The parent session solved
2023–2025 concurrently in a separate container (rule 12 `[R-PARALLEL]`); both
invocations read the SAME committed override file,
`results/calibration/_caiso267_fossil92_offer_curve.json`, byte-for-byte.

## §1 — Governance preconditions, verified before the solve

* **Freeze** (`frontend/data/backcast/holdout-freeze.json`): `active: true`, but
  `scope.tiers == ["locked_test"]`. The VALIDATION tier (2020–2022) was lifted from
  the freeze by the 2026-08-26 owner ruling (card 6) and is governed by the
  `complete` marker + `--holdout-authorized` alone. **2022 is not frozen.**
* **Marker** (`frontend/data/backcast/calibration-complete.json`): CAISO holds
  `complete`, declared **2026-09-06**, keeper `2026-09-06-caiso-260-b1-demand`.
* **2019 and H1-2026 were NOT touched.** They are locked test, frozen for every ISO,
  and CAISO has never been granted `final`.

**2022 IS A RE-TEST, NEVER A FIT TARGET** (rule 22 `[R-HOLDOUT]`). 0.92 was fixed
ex ante by the owner ruling recorded in `ADDENDUM-caiso267-fossil-offer-8pct-2026-09-09.md`
§A and pushed before any LP. **It was not resized, swept, or re-proposed by this
shard, and nothing in this document argues for a different factor.**

## §2 — The KNOWN TRAP was already discharged at HEAD; the comparison is like-for-like

The shard was briefed that a CAISO run covering 2022 would rewrite
`frontend/data/backcast/bench/CAISO/2022.json.gz`, activating the load-weighted
`rt_lw` actual basis that caiso-265 §4 landed but left INERT, and that the existing
touchpoint would silently re-score +21.1 % → +13.3 % with no code change in the diff
(the NYISO-148 silent-part failure mode).

**That had already happened before this shard started.** caiso-265 re-solved and
re-registered the 2022 rung on the like-for-like basis in commit `9f6b8864`
("caiso-265: re-solve and re-register the 2022 rung on the like-for-like price
basis"), so the committed part at `b5dcda32` already carried `rt_lw 84.49` /
`da_lw 92.14`. Measured here:

* The incumbent touchpoint `2026-09-07-caiso-262-2022-touchpoint` scores **+13.3 %**
  at HEAD *before* this shard solved anything — i.e. the −7.8 pp basis move is
  already in the committed record, not in this run's diff.
* `frontend/data/backcast/bench/CAISO/2022.json.gz` is **md5 `2b759f44db006df50d47a14d57b60de7`
  before the solve and byte-identical after both the solve and the registration.**

**So this run contributes ZERO of the basis change, and its +8.1 % is directly
comparable to the +13.3 % like-for-like baseline.** Neither number is ever compared
against the retired +21.1 %.

## §3 — Result: 2022, arm vs like-for-like baseline (same bench part, byte-identical)

| criterion | baseline `caiso-262` touchpoint | **arm ×0.92** | move |
|---|---|---|---|
| C1 fuel-mix by class | PASS (6/6) | **FAIL** — CC_REGULAR +7.33 TWh, share +2.8pp | **PASS → FAIL** |
| C2 system volume | PASS | PASS | — |
| **C3a mean LMP** | FAIL **+13.3 %** (model 95.73 vs RT-lw 84.49) | **PASS +8.1 %** (model **91.34** vs RT-lw **84.49**) | **FAIL → PASS** |
| **C3b price duration/shape** | FAIL **NRMSE 0.242** | **PASS NRMSE 0.174** | **FAIL → PASS** |
| C3c price tail / scarcity (RT) | PASS | PASS — model 572 h vs actual RT 510 h (ratio 1.122, band [0.5×, 2.0×]) | — |
| C4 dispatch correlation | PASS | PASS | — |
| C6 governance | PASS | PASS | — |
| C8 forced-energy share | PASS | PASS | — |
| **DETERMINATION** | **NOT-YET** | **NOT-YET** | unchanged — **different cause** |

Reported-only: C5a CO2 vs eGRID −6.4 % → **−1.1 %**. D-A diurnal amplitude
91.7 % → 87.9 % of measured; hod r +0.963 both.

**Δλ = 91.34 − 95.73 = −4.39 $/MWh** on the system load-weighted mean.

**The C1 flip is the mechanism working through the merit order, reported at full
magnitude, not explained away.** A uniform fossil offer cut moves fossil against
non-fossil, so fossil energy rises: CC_REGULAR **55.19 → 58.93 TWh** (actual 51.61)
and CT_PEAKER **3.10 → 3.79 TWh** (actual 4.48). CT_PEAKER moves *toward* its actual;
CC_REGULAR moves *away* and crosses the C1 band. The addendum §G disclosed this
exposure before the solve ("C1 is a class-volume criterion and fossil volume moves by
construction; a C1 cell flip is a real possibility and is gated").

**DID 2022 GET WORSE? MIXED, AND STATED PLAINLY:** the two price criteria improved
decisively and both crossed **into** tolerance; the volume criterion degraded and
crossed **out of** tolerance. The determination is **NOT-YET in both cases**, so the
rung's headline does not move. Per rule 30 (c) `[R-TOUCHPOINT-FOLD]`, a held-out year
never certifies or decertifies the ISO either way.

## §4 — Two deviations from the shard brief, declared

Both are recorded because the brief said to leave the generated artifacts alone, and
both changes were forced by the generator being written for the parent's span.

1. **`governance.authorized_price_tuning.years_held` was corrected `[2023, 2024, 2025]`
   → `[2022]`.** The brief said to leave the block exactly as generated; as generated it
   made **C6 FAIL outright** — `calibration_verdict._authorized_tuning_finding` tests
   rule 1 (b) by **exact set equality** against the RUN's own scored years, and
   `scripts/gen_caiso267_attestation.py` hardcodes `YEARS = (2023, 2024, 2025)`, which is
   a statement about a different bundle. **Only that one factual field changed**; channel,
   ruling, value/scalar 0.92, `set_ex_ante`, `not_swept`, identification, prereg and
   disclosure are byte-for-byte as generated, and a `years_held_note` records the
   correction in place. **Rule 1 (b)'s substance is untouched and is the point:** ONE
   config — the single ex-ante constant 0.92 over the same 40 bands — held identically
   across 2022 AND 2023–2025. **No per-year value exists.**
2. **The C3c ledger entry was re-pointed from 2024 to 2022 and re-measured**, as the
   brief directed. The generator emitted a 2024 row reading `model ? h` (its
   `_tail_counts` found no 2023–2025 parquet in a 2022-only bundle). It is replaced by a
   2022 row measured from this bundle's own `hourly/system_2022.parquet` — **572 h** at
   P1 max-zonal dual > $200/MWh vs **510 h** actual RT (`tail/actual_tail.json`
   `CAISO.2022.rt_gt`). **The band is MET, so C3c does not miss in 2022 and the entry
   spends no ledger slot** — it is carried for lineage and for the magnitude the
   generator owes, explicitly flagged `spent: false`. No `price_mean` exception was
   invented for 2022; C3a's baseline miss stood undocumented and its pass here is
   likewise unledgered.

Additionally, per addendum §C(e) the DOF ledger carries the one declared free parameter
**`fossil_offer_band_scale = 0.92`**, identification *"price residual, authorized channel
(rules 1/13 amendment 2026-09-05); owner ruling 2026-09-09"* — added by hand after
`build_dof_ledger.py`, which derives entries from the config and does not emit it
(9 → 10 entries, 6 → 7 residual).

## §5 — Rule 30 `[R-TOUCHPOINT-FOLD]`: deliberately NOT stamped

This run is **NOT** stamped to the caiso-260 keeper with
`scripts/stamp_touchpoint_holdout.py`. Rule 30 folds a touchpoint into a keeper because
"a touchpoint IS the designated keeper's frozen recipe replayed on a held-out year —
same config, different year". **This is not that recipe**: it is a different config (the
×0.92 arm), so folding it onto `2026-09-06-caiso-260-b1-demand` would put a config the
keeper does not have inside the keeper's own card. The stamp becomes owed — to the
**arm**, not to caiso-260 — only if the owner promotes the arm to keeper, at which point
the promoting session owns rule 30 (a)/(b)/(c) for it.

## §6 — Rule 31 `[R-RETAIN]`: nothing was deleted

The full bundle (including the gitignored ~98 MB `dispatch/`, `unit_hourly_2022.parquet`
and `network_2022.parquet`) is **intact on local disk**. The fat parts are gitignored by
the repo's standing rules, which is what discharges the delete-before-merge duty — `rm`
does not, and no `rm` was run. **This container is ephemeral and the gitignored parts do
not survive its reclamation**; the committed slim bundle + sidecar + payload do.
