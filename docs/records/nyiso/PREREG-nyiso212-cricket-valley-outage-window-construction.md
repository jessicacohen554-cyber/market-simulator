# PREREG nyiso-212 — decompose the **Cricket Valley over-ceiling months** into their construction terms, before either object is levered

**Session:** nyiso-212, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-c7tc79`, off `main` `abdd30c9`. **Date:** 2026-09-07.
**Keeper:** `2026-09-06-nyiso-202-startup-aware` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat. **Committed and pushed BEFORE any plant-grain measurement is read.**

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads CALIBRATED with zero
failing criteria. Nothing in this session is selected because a residual moved (rule 1
`[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`). The target is a **structural defect that C1 currently
PASSES over**: the six plant-months nyiso-211 §5 measured in which the LP's physical ceiling at
Cricket Valley 57185 sits **below the plant's own meter** — a contradiction between two measured
inputs that no offer curve can reach.

**Owner's standing formula, carried verbatim** (this session's opening message): *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper.."* **No candidate exists at pre-registration.** This document
pre-registers a **zero-LP phase-0 measurement** (rule 29 `[R-SCREEN]` step 0). If it returns a
lever, the screen year is named in a **separate, later** pre-registration by the mechanism's own
measured footprint — never by a residual — and only an arm that clears that screen and the full
2023–2025 span becomes a candidate to which the formula and D-5(b) apply.

**Rule 22 `[R-HOLDOUT]`.** Every year read here is **in-sample (2023, 2024, 2025)**. 2022 is
**not read**. 2020, 2021 and the locked test are untouched. No marker byte moves. The CAMPD
unit-level parquets carry 2019–2026; only the 2023–2025 files are opened, and only for plant 57185.

**Five owner rulings pending, none mine** (nyiso-206 floor_pct basis; nyiso-207 identification-vs-
application basis; nyiso-203 §6; DECISION-CARD-nyiso193 §5/§5.1 unit grain; nyiso-208
out-of-training CAMPD read). None is prejudged here.

---

## 1. The object, exactly as handed forward

nyiso-211 (`docs/FINDING-nyiso211-cricket-valley-lineage-attribution-2026-09-07.md` §5, §7) leaves
the Cricket Valley deficit as **two objects**:

* **(A) an OUTAGE-WINDOW CONSTRUCTION defect** — in **Jul/Aug/Sep 2024** and **Jun/Jul/Aug 2025**
  (plus **Jul 2023** on both bases) the keeper's availability puts the LP's physical ceiling below
  the CAMPD meter (`monthly_ratio > 1` in `_nyiso211_overderate_test.json`, target 57185, arm
  basis: 1.0073 · 1.0518 / 1.2184 / 1.1431 · 1.0659 / 1.1839 / 1.1448). 57185 is the only CC_REGULAR
  plant that GAINS an over-ceiling month from `unit_outage_extract_basis_share`.
* **(B) a MERIT/OFFER-POSITION defect** outside those months.

**This session's object is (A) and only (A).** The handoff's binding instruction is to separate the
two before either is levered, and to start with (A) because it is sign-definite and price-free.

## 2. What was read before this document was written (disclosed, not concealed)

Structure and committed records only — **no new plant-grain number was computed**:

1. nyiso-211's FINDING and its committed instruments (`_nyiso211_overderate_test.json` →
   `target.<year>.{keeper,arm}_basis.monthly_ratio / mean_avail / available_gwh / campd_gwh`),
   i.e. exactly the numbers the handoff already quotes. **Bench `c_mon` for 57185 was NOT read**
   (the read errored before printing and was not retried).
2. The committed extract rows for 57185 in every NYISO overlay file. **Only ONE overlay file
   carries the plant**: `campd-unit-outages-perunitmerit-NYISO.csv` (111 rows, 2020–2026;
   `unit_capacity_mw 174.2`, `plant_capacity_mw 522.6`, `capacity_source eia_exact`, 3 units
   U001–U003). Zero rows in the layup, e923, short and partial files. So **no cross-file stacking
   exists at this plant** — the "cross-unit window sums" question the handoff names is confined to
   ONE file. The 2024/2025 windows read, in full: U001 2024-01-05→01-10, 01-12→01-24, 02-27→03-08,
   03-24→03-31, 06-15→06-21, **08-01→08-27**, 10-12→10-29, 12-01→12-09, 12-20→12-31,
   2025-01-01→02-21, 02-21→02-26, 03-15→04-02, 05-07→05-12, …; U002 2024-01-13→01-24, 01-28→02-04,
   02-04→03-19, 04-09→06-07, 12-20→12-27, 2025-01-08→01-13, 01-15→01-22, 01-23→01-31, 05-01→05-12,
   09-17→09-23, …; **U003 2024-06-30→07-13, 2024-07-15→2024-12-31 (169.1 d), 2025-01-01→2025-08-13
   (224.4 d)**, 2025-10-07→10-16. In Aug 2024 the extract therefore has U003 out all month and U001
   out Aug 1–27; in Jun–Aug 2025 U003 out throughout.
3. Code, in full: `outages._unit_outage_factors_from_events` / `_extract_basis_index` (the share
   under the arm basis is `174.2 / 522.6 = 1/3` per unit, day-granular `[start, end + 1 day)`,
   concurrent units SUM, clipped at 1.0); `fleet/arrays.py` (the unit derate MULTIPLIES a
   statistical availability — WEFOR × `wefor_multiplier 0.7`, and under the keeper's
   `cc_nameplate_summer_derate=True` the per-plant summer derate — so a no-window month still has
   availability < 1); `derive_campd_unit_outages.py` (`_unit_year_grid` zero-fills unreported
   hours; CC windows come from `detect_outages_eventbased`: a maximal run of hours with
   `gross/detect_cap < 0.02`, `detect_cap = 174.2` here, so the break threshold is 3.5 MW; then the
   revealed-availability filter and the merit-order guard, which can only DROP windows);
   `campd._read_one` (**facility-first**: NY exists in BOTH `campd-facility-level/` and
   `campd-unit-level/`, so the bench's meter is built from the FACILITY file while the deriver reads
   the UNIT file — two different downloads of one database); `run_calibration_full._campd_hourly_frame`
   + `parasitic_load_factors.parquet` (**57185 has NO parasitic row**, so its bench series is
   facility-level `grossLoad × 1.0` — the meter is GROSS); `cc_capacity_reconcile_NYISO.csv`
   (57185: `current_mw 1312.5`, `campd_p999_mw 1086.9`, `reconciled_mw 1086.9`, mode `cap` — the
   LP pmax is the plant's CAMPD gross p99.9, so pmax and meter are on ONE basis, gross); the
   `extract_basis` field docstring in `scenarios.py` (each block's CAMPD gross reaches 374–380 MW;
   the CTs are U004–U006 at 263.3 MW, the steam turbines U001–U003 at 174.2 MW).
4. Keeper `run_config.json` / `meta.json` flags (configuration, not results).

## 3. The instrument — an exact identity, then a decomposition

For plant 57185, month *m*, on the keeper's recipe (arm basis), define on the **gross** basis:

* **M** — the bench meter, `c_mon[m]` (facility-level CAMPD gross × 1.0).
* **C2** — the LP ceiling actually given: `Σ_h Σ_tranches pmax_tranche × availability[h]` from an
  on-recipe `fleet_only` rebuild of the keeper's `meta.json` (`scripts.lib.bundle_fleet`, the
  same instrument nyiso-196/211 used) — this is nyiso-211's `available_gwh_by_month`.
* **C1** — the window-only ceiling: `Σ_h pmax_plant × ufac[h]`, where `ufac` is the unit-outage
  factor alone (`unit_outage_derate_factors` for `(57185, CC_REGULAR)`), i.e. C2 with the
  statistical WEFOR / summer derate removed.
* **E_u** — unit *u*'s gross energy from the **unit-level** CAMPD file, split into **E_u,in**
  (hours inside one of *u*'s own committed windows, day-granular `[start, end+1d)`) and
  **E_u,out** (the rest). **h_out,u** = hours of *m* outside *u*'s windows.
* **s** = `pmax_plant / 3` = 362.3 MW — one unit's LP share under the arm basis (three equal
  174.2 MW extract units, `1/3` each).

The over-ceiling excess **X = M − C2** then decomposes **exactly**:

    X = T_stat + T_bench + T_in + T_cap
    T_stat  = C1 − C2                          (statistical overlay riding on top of the windows)
    T_bench = M − Σ_u E_u                      (facility-level meter minus unit-level sum)
    T_in    = Σ_u E_u,in                       (energy the "out" units reported INSIDE their windows)
    T_cap   = Σ_u (E_u,out − s × h_out,u)      (running units above/below their 362.3 MW LP share)

(C1 = Σ_u s × h_out,u by construction of the arm-basis share, so the identity is algebraic; I2
below verifies that construction against the loader hour for hour.) Each term names a DIFFERENT
object: T_bench a disagreement between two downloads of one measured source; T_in a window the
unit's own CEMS contradicts (a stale or defective extract); T_cap a per-block capacity basis;
T_stat the statistical overlay. **The whole point is that these four cannot be told apart from
the residual, and CAN be told apart here at zero LP.** The seven months scored are the keeper's
over-ceiling months: **Jul 2023; Jul/Aug/Sep 2024; Jun/Jul/Aug 2025.** The six 2024/2025 months
are the "repair-created" set the handoff names; Jul 2023 (no windows at all in the extract, so
T_in ≡ 0 there) is the **control month** for the timing signature.

Every other month of 2023–2025 is computed and reported in the machine record too, so a sign that
holds only in the over-ceiling months is visible as such.

**Adjudicator, declared in advance:** where T_bench is material, EIA-923 monthly net (`e_mon` in
the bench, a third measured source, ~2.5 % below gross for a CC) decides which CAMPD download is
right: the one whose monthly gross lands within 5 % of `e_mon / 0.975`.

## 4. Identity checks — declared, with their consequences

| id | check | bar | consequence if it FAILS |
|---|---|---|---|
| **I1** instrument | the arm-basis rebuild reproduces nyiso-211's committed `available_gwh_by_month` and `mean_avail` for 57185 (`_nyiso211_overderate_test.json`, `target.<y>.arm_basis`) | every month within 0.5 GWh, `mean_avail` to 4 dp, all 3 years | HEAD drift: G-DRIFT is investigated before anything else and every number below is reported as "this HEAD only", never as the keeper's |
| **I2** windows | `ufac` reconstructed from the committed CSV rows (share 1/3, day-granular `[start, end+1d)`, sum, clip 1.0) equals the loader's factor for `(57185, CC_REGULAR)` hour for hour; and `availability / ufac` (the statistical factor) is identical across the plant's tranches | max abs diff ≤ 1e-9; tranche spread ≤ 1e-9 | the window → LP mapping is misunderstood; only **X** and **T_bench** (which do not depend on it) are quoted, and the T_in / T_cap split is reported as UNVERIFIED |
| **I3** basis | `Σ c_mon = c_ann`; and `c_ann` equals the annual facility-level `grossLoad` sum for 57185 × 1.0 | ±0.01 GWh; within 0.1 % | the "facility gross × 1.0" reading of the meter is wrong; T_bench is reported against the SAME frame the bench actually used, and the discrepancy is stated |
| **I4** deriver | `_unit_year_grid` + `detect_outages_eventbased(cf_peak 0.02, ≥ 5 d)` run on the CURRENT `NY_2024` / `NY_2025` unit-level file for U001–U003 reproduces every committed 57185 window (same start / end day; the in-merit and merit-order filters can only drop windows, so a reproduced superset is a pass) | every committed 2024/2025 window reproduced | the committed extract is STALE against the committed unit-level file — P2 territory — and the stale rows are listed |

## 5. Pre-registered predictions

All on the seven months of §3; "dominates" means ≥ 50 % of X in that month and the largest term.

| id | prediction | bar | outcome family |
|---|---|---|---|
| **P1** — *preferred* | **T_bench dominates**: the facility-level meter carries energy the unit-level file does not, and the gap opens with the U003 window | T_bench dominates in ≥ 4 of the 6 repair-created months; **and** T_bench ≤ 10 % of X in the Jul 2023 control month | two downloads of one database disagree at 57185 from mid-2024 (a unit re-id, a late-posted unit, or a partial pull) |
| **P2** — *the one that HURTS P1* | **T_in dominates**: the units the extract marks OUT reported gross inside their own windows | T_in dominates in ≥ 4 of 6; **and** I4 FAILS on at least one of those windows | the extract is stale / defective against its own source; re-derive under rule 23 citing the source-data change |
| **P3** — *third, disjoint* | **T_cap + T_stat dominate** (windows faithful, downloads agree): the running blocks exceed their 362.3 MW share and/or the statistical overlay carries the excess | (T_cap + T_stat) ≥ 50 % of X in ≥ 4 of 6, with T_bench and T_in each < 25 % | the object is a per-block CAPACITY BASIS (plant-level p99.9 cap ÷ 3 vs a block's 374–380 MW peak), not a window at all |
| **P4** — reported, hurts every "window" story | T_stat is a co-carrier | T_stat ≥ 25 % of X in ≥ 3 of the 7 months | the statistical WEFOR/summer derate stacked on measured windows is itself part of the contradiction |
| **P5** — timing signature | the object begins with the U003 2024-07-15 window | in Jan–Jun 2024, \|T_bench\| ≤ 2 % of M in every month | supports P1 or P2 over P3 |

**Third declared outcome (diffuse):** no term dominates in ≥ 4 of the 6 months → the table is
reported, **no single object is named**, and no lever is proposed. P1, P2 and P3 are mutually
exclusive by their ≥ 50 % bars on the same months.

**A physical bound I can state before measuring, and its honest limit.** One block's gross ceiling
over August is ≤ 380 MW × 744 h ≈ 283 GWh (block peak per the nyiso-196 record). Under the
committed windows the Aug 2024 LP ceiling is ≈ 1,086.9 × (4 d × ⅔ + 27 d × ⅓) × 24 ≈ 304 GWh
× (statistical factor), and the meter exceeds it by 21.8 %. Whether a single running block plus
U001's four days could physically have produced that meter is **close to the bound, not clearly
beyond it** — so P3 is a live outcome, not a straw man, and I do not claim impossibility.

## 6. What this session will and will not do

* **Zero LP.** Rule 29 step 0 only: fleet_only rebuilds, CSV/parquet reads, no solve, no
  dispatch, no prices. No screen bundle, no control solve (rule 29(b): the keeper's committed
  bundle is the control; G-DRIFT validated with `scripts/probes/nyiso196_rebuild_checks.py
  --year 2024` reproducing its committed record).
* **No flag, coefficient, derive script, scorer, marker, keeper or gate moves** in this
  pre-registration's scope. If the measurement names a data repair (P1/P2), the repair itself —
  a re-fetch or re-derive citing the source-data change (rule 14 `[R-ACCURATE]`, rule 23) — and
  any screen it earns are pre-registered separately, with the screen year chosen by the repair's
  own measured footprint.
* **Basis discipline.** GROSS CAMPD on both sides in every year (bench = facility-level gross ×
  1.0 at this plant; pmax = CAMPD gross p99.9). No CAMPD-basis gap is ever quoted as a C1 number
  (C1 scores against bench `classFull`, which sits below the CAMPD plant sum by −0.44 / −2.38 /
  −0.34 TWh in 2023/24/25). The bench keys split plants `<code>:<group>`; 57185 is plain-keyed in
  every source and no key is folded.
* **Rule 28.** NYISO's matrix shard is stamped in this session (`unit_outage_extract_basis_share`
  and `campd_outage_windows` cells — evidence, not verdict letters, unless a verdict is earned);
  the shard's key set is verified identical to `main` before commit.
* **DO NOT RE-DO** (nyiso-211): `unit_outage_per_unit_clip` as the lever (killed, 8.39 GWh/yr);
  reverting/weakening `unit_outage_extract_basis_share` (refused, rule 14); Cricket + CPV as one
  lever; the "persistent over-runners" reading; everything nyiso-210 closed.

## 7. Machine record and reproduction

`results/calibration/_nyiso212_overceiling_decomposition.json` (plant × month × term, all 36
months, the seven scored months flagged, every I-check with its measured value) written by
`scripts/probes/nyiso212_overceiling_decomposition.py`, which reuses nyiso-211's rebuild cache
pattern (`.cache/nyiso212/`). Reproduce:

    uv run python scripts/probes/nyiso212_overceiling_decomposition.py

*(nyiso-212, 2026-09-07. Pre-registered before measurement; if the preferred prediction fails, both
halves are reported and no statistic is repaired into a pass.)*
