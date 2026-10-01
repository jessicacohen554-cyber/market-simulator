# PRECOMMIT — PJM-NEXT-2 card 1: coal over-dispatch 2019-2022 is missing measured outage windows (outage-extract membership repair)

Session PJM-NEXT-2, 2026-09-25. Keeper `2026-09-25-pjm-next-c1` (bundle `results/calibration/pjmnext_c1_span`,
solved at `7f095384`). Written and pushed **before any solve**. Zero-LP phase 0 below; the arm is one gated field,
`unit_outage_membership_repair`, zero free parameters.

## 1. Where the over-dispatch sits (zero LP, keeper's committed payload + bench)

Per-plant model (`runs/<id>.js` `m_ann`) minus EIA-923 (`bench/PJM/<y>.json.gz` `e_ann`), coal classes:

| year | coal model − 923 | plants exiting ≤ Y+3 | survivors |
|---|---|---|---|
| 2019 | +38.9 TWh | **+37.7** | +1.2 |
| 2020 | +29.6 | +19.1 | +10.5 |
| 2021 | +35.3 | +24.5 | +10.8 |
| 2022 | +12.9 | +6.9 | +6.1 |
| 2023-25 | −1.0 / +1.4 / +9.9 | ≈0 | — |

The over-runners are the pre-exit fleet: Morgantown (CF 0.70 model vs 0.16 actual, 2019), Bruce Mansfield, Zimmer,
Sammis, Dickerson, Avon Lake, Waukegan, Cheswick, Conesville, Indian River, Wagner, Chalk Point, Will County, Birchwood.

**Not the cause (measured):** floors — `min_gen` energy on every top plant ≈ 0 (the excess is economic dispatch);
RGGI — MD/DE plants carry ~$5.5/MWh over non-RGGI peers in 2019 (correct); plant fuel price — most merchant PJM
coal has no EIA-923 cost row (withheld) and rides a near-uniform $2.0–2.3/MMBtu, the same as the survivors that fit.

## 2. The cause: those plants have NO measured outage windows

The committed standard extract `data/raw/campd-unit-outages-PJM.csv` (sha `312a11b8…`) carries **zero rows in any
year** for all of the over-runners above, while their own CEMS shows e.g. Morgantown units 1/2 dark 269/210 days in
2019 (longest run 66 d), Zimmer unit 1 165 d, Cheswick 224 d. Two membership defects in the deriver
(`scripts/data/derive_campd_unit_outages.py`), both measured:

- **D1 — partial-plant exits keyed on the surviving class.** Membership is the canonical (2025) EIA-860 fleet +
  canonical whole-plant retirees. Morgantown / Wagner / Indian River resolve to an **empty** class, Waukegan is
  **absent**, Dickerson reads **CT_PEAKER** (the CTs that survived) — so their coal units are never scanned.
  Fix: `--membership-vintage-union` (new, default-off) unions each derived year's own vintage fleet into the
  membership — the outage-extract twin of the keeper's `benchmark_membership_vintage_union`.
- **D2 — COAL-SUB token (latent, found here).** The deriver's qualifying-group test compares the fleet's
  `plant_group` (now `COAL_BIT/PRB/WC`) against `QUALIFYING_PLANT_GROUPS` (artifact token `COAL`), so a HEAD
  re-derive **silently skips every coal-only facility**: 2019 coal outage-days 16,764 → 2,824. Fixed in the
  deriver by translating through `plant_taxonomy.artifact_class` (restores 16,612). This also means **card 4's
  extract overwrite would have been destructive at HEAD** had it run before this fix.

(The whole-plant retirees — Zimmer, Avon Lake, Cheswick, Will County, Conesville, Birchwood, Bruce Mansfield — gain
windows from the D2-fixed re-derive; they are absent from the committed extract because it predates their
membership.)

## 3. The arm (one field, zero DOF)

`unit_outage_membership_repair` selects `data/raw/campd-unit-outages-memberrepair-PJM.csv`
(sha256 `c6883c5146cfa7177abdc568bd81735d88888ca04c8330d0349aeeaaae481f9a`) =
the committed extract **byte-for-byte** (first 10,671 lines identical) + **864 rows for the 21 facilities with no
committed row**, from a D1+D2-fixed re-derive (`scripts/data/build_outage_membership_repair.py`). Existing rows are
never re-derived, so card 4's drift question (CC_REGULAR / ST_GAS / Montour re-routing at HEAD) is untouched. A
separate file, never an overwrite (rule 23 intact: no committed `data/raw` extract is modified).

Admissibility (rules 13/14): outage windows are a physical availability event measured in CAMPD, regenerate for any
year with a CAMPD filing, and are already the keeper's mechanism — this corrects which facilities the measurement
covers. Rule 19: the same overlay reads a wider file; no new availability mechanism. `retiree_cems_cap` (armed in the
keeper) is **inert under `eia860_vintage_tracks_solve_year`** — `load_retired_within_window` returns an empty list
in-run for every vintage year (measured: 0 caps in 2019) — reported, not touched here.

## 4. Zero-LP census (fleet-only rebuild, keeper recipe ± the flag)

- 2019: availability moves on **only** the 21 facilities; capacity-hours removed COAL_BIT 34.8 / COAL_PRB 7.3 /
  CC_REGULAR 3.3 / ST_GAS 1.0 TWh (Morgantown 7.4, Zimmer 5.2, Avon Lake 4.5, Dickerson 4.2, Waukegan 4.1, Indian
  River 3.3, Wagner 3.2, Will County 3.1, Cheswick 2.7, Bruce Mansfield 2.3). Fuel/offers byte-identical. Shared
  reliability-floor / net-load-drag limbs (mechanisms 4/6) re-apportion `min_gen` on 22 limb-mate plants, net
  −0.075 TWh — downstream of the same input, disclosed.
- 2024: only Indian River (1.85 TWh) and two CHP sites (0.07) move.
- Off-path: flags off at HEAD is byte-identical to pre-edit (availability, fuel, offers, min_gen, 2024).

## 5. G-DRIFT (rule 29(b)) — form 4 is valid, no control solves

Fleet-only rebuild of the keeper recipe at the keeper SHA `7f095384` (code-only worktree) and at HEAD `c64e69eb`:
unit ids, availability, min_gen, offers (`mc_base`), fuel prices, pmax and demand are **byte-identical** in 2019
and 2024. Commits since `7f095384` on the solve path are other-ISO (SOCO B2, NWPP-NEXT-2, SPP-80/81, MISO-272 —
ISO-gated), default-off fields absent from the keeper recipe (soco-67 `unit_outage_precod_clip`, R-ERCOT-4), or
governance (FR-22, surface-pin declaration). The cache key differs only through the solve-surface fingerprint's
added SOCO/NWPP rows. The keeper's committed bundle is the control.

## 6. Predictions (stated before the solve)

- COAL_BIT and COAL_PRB model energy **fall** in 2019-2022; the COAL_BIT error shrinks in each of 2019-2022.
  Magnitude not predicted beyond: the LP backfills removed coal (pjm-d4-4 measured 87% coal backfill for gas
  windows), so the energy drop will be well below the 42 TWh capacity-hours removed in 2019.
- CC_REGULAR / CT_PEAKER rise in 2019-2022 (2022 CC_REGULAR, already +10.9, may worsen — stated against interest).
- 2023-2025 move only slightly (Indian River, Wagner): the training-span determination is not expected to change.
- C3a/C3b/C3c: direction not predicted.

A regression on any criterion is reported at full magnitude and is not a reason to drop the arm (rule 1).

## 7. Execution (rules 32/34/36)

One shard per year 2019-2025, each `replay_keeper.py results/calibration/pjmnext_c1_span --years <y>
--set unit_outage_membership_repair=true`, pinned to the full SHA of the commit carrying this doc, full bundle
pushed to `claude/pjmnext2-c1-<y>`. Shard hard stops: (a) keeper recipe flags true in `scenario_config`;
(b) `resolved_inputs.campd_unit_outages.path` ends `campd-unit-outages-memberrepair-PJM.csv` and its sha256 starts
`c6883c51`; (d) `unit_outage_membership_repair` true; (g) EIA-923 benchmark total for the year equals the keeper's
(2019 820.811, 2020 805.898, 2021 827.088, 2022 833.192, 2023 823.024, 2024 852.252, 2025 871.628 TWh, ±0.001).
The parent composes, scores against the keeper on the same benchmark, attests (DOF ledger carried, zero entries
added), registers, and asks the promotion question.
