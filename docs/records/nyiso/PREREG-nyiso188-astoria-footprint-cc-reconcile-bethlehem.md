# PRE-REGISTRATION — nyiso-188 (`backcast-calibration` lane): the Astoria routing's REMAINING footprint (ramp envelopes + v2 emission rates), the registered `cc_capacity_reconcile` flag, and Bethlehem 2539's eGRID vintage artifact — three objects, each its own A/B, bars fixed before any arm is solved

**Session:** nyiso-188, NYISO backcast-calibration track, 2026-09-04.
**Branch:** `claude/nyiso-188-backcast-calibration-tex4hz`, fresh off `origin/main`
at `8f5cb32c` (carries PR #4704, the nyiso-187 keeper promotion).
**Keeper at entry:** `2026-09-04-nyiso-187-astoria-routing`
(`results/calibration/nyiso187_astoria_routing`) — NOT-YET, target grade 5,
fail set **{C1-2024 `CC_REGULAR` +3.80 TWh / +3.1 pp, C3a-2025 −10.3 %
(owner-court, NOT touched), C3c}**.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE FIRST ARM
SOLVE OF THIS SESSION.** At the time of writing ONE solve exists: the
same-HEAD control replay of the keeper recipe on the committed artifacts
(`results/calibration/nyiso188_control`, an instrument, 2023–2024 solved,
2025 in progress; NOT yet compared to the keeper). No arm has been solved, no
criterion of any arm has been read.

---

## §0 — DISCLOSURE: what has been measured (no LP), and what has not

**Read this session:** `FINDING-nyiso187` (whole; §2 is the standing
disposition of the 2024 `CC_REGULAR` cell — DO NOT REDO; §3 / §5.2 are this
session's objects), `PREREG-nyiso187`, matrix §5.5 (nyiso-187 queue), the
NYISO shard cells `campd_per_unit_attribution` (K), `scuc_load_pocket_commitment`
(G), `tranche_startup_amortization` (K), `cc_capacity_reconcile` (U),
`cc_capacity_reconcile_path` (K), `egrid_identity_heat_rates` (K);
`FINDING-nyiso186` §2.1–§2.5, §5.3.

**Code read:** `scripts/data/derive_campd_ramp_envelopes.py` (the `(0, bucket)`
class-fraction row = plain median of `delta / pmax_obs` over the well-observed
plants of the bucket, n ≥ 4,000 online hours; the remap is applied per
`(facility, unit)` before the fleet filter); `fleet/campd_bins.build_ramp_groups`
(a `(plant, bucket)` group without a `basis == "plant"` row reads
`class_frac × group pmax`; CT groups get no fallback; groups whose envelope
can never bind are pruned); `scripts/data/curate_emissions_unit_annual.py`
(`_normalize_unit_hourly` keys rows on the raw `facilityId` — it did NOT apply
`campd.CAMPD_UNIT_PLANT_REMAP`, unlike `campd._normalize_campd` and every
other CAMPD-fed derive); `scripts/data/derive_plant_emissions_v2.py` (reads the
`emissions-unit-annual` clean datatype; the default path REWRITES the whole
artifact from `--iso × --years`); `emission_rates.measured_plant_rates`
(backcast: the target year's own rows, pooled to `(plant, fuel_class)`);
`fleet/campd_bins._reconcile_cc_capacity` (a `cap` row bounds `capacity_mw`
at `reconciled_mw`, a `raise` row lifts it; applied in `fleet_to_bins` AFTER
the summer-derate nameplate rescale); `fleet/eia860._reconcile_cc_pmax_to_nameplate`
(the keeper ALREADY reads `campd_p999_mw` from the same table as the trusted
bound `max(nameplate, demonstrated_peak)` — cell `cc_capacity_reconcile_path`
K); `scripts/data/derive_cc_capacity_reconcile.py` (`--mode both`: cap where
model > 1.10 × p99.9, raise where p99.9 > model by ≤ 10 %; CT-only and
CF-infeasible exclusions); `scripts/data/derive_egrid_identity_heat_rates.py`
(pooled ΣPLHTIAN/ΣPLNGENAN with the per-vintage and LOYO record);
`scripts/data/process_eia860.py::_join_egrid_heat_rate` (the fleet's base
heat rate is eGRID **2023** `PLHTRT`, one vintage for every backcast year).

**Measured this session, BEFORE this document (artifact footprints, no
dispatch read):**

* **Ramp envelopes.** The committed `campd_ramp_envelopes_NYISO.csv`
  reproduces BYTE-IDENTICALLY from `derive_campd_ramp_envelopes.py --iso NYISO`
  (default years 2023–2025) with the two Astoria remap entries stripped — the
  committed invocation is established. Re-derived at HEAD (remap armed):
  55375's row 1,252 MW obs / 469 up / 622 dn (26,106 online h) → **626 / 372 /
  449** (25,016 h); **57664 gains its row 626 / 416 / 454** (basis `plant`);
  the CC pool grows 26 → 27 plants and the `(0, CC)` class-fraction row moves
  **0.4907 → 0.5000 (up), 0.5623 → 0.5904 (dn)**; the CT and ST rows are
  byte-identical. **Who reads the `(0, CC)` fallback:** 14 fleet CC groups /
  1,355.3 MW (Selkirk 10725 596.6 MW, the rest ≤ 86 MW each: Allegany 7784,
  Lederle, CH Resources Beaver Falls / Syracuse, Carthage, Cornell, Indeck
  Yerkes / Olean, Sterling, Rensselaer, Massena, Batavia, NYU) — their summed
  up-envelope moves 665.0 → 677.7 MW (+1.9 %), dn 762.1 → 800.2 MW (+5.0 %).
  Six ST groups (2,234 MW) read the `(0, ST)` row, which does not move.
  Record: `results/calibration/_nyiso188_ramp_footprint/`.
* **v2 emission rates.** The committed `plant_emission_rates_v2.parquet`
  carries CT3 / CT4 under `plant_id` 55375 in every year; 57664 has NO row, so
  `apply_plant_emission_rates_v2` leaves it at the fleet default
  `heat_rate × FUEL_CO2_FACTOR_PER_MMBTU["gas_cc"]` = 7.3792 × 0.057 =
  **0.4206 t/MWh** while 55375 prices at the four-unit pooled measured rate
  (0.3778 / 0.3807 / 0.3845 in 2023 / 2024 / 2025). Under the routing the
  plant-grain backcast rates become **55375 (CT1 + CT2) 0.3618 / 0.3639 /
  0.3672** and **57664 (CT3 + CT4) 0.3947 / 0.3981 / 0.4144** t/MWh. NYISO
  parasitic factors are absent from `parasitic_load_factors.parquet` (650
  plants, none in NY / NJ), so net = gross × 1.0 uniformly — the split is the
  only change. Re-curating NY + NJ and re-deriving reproduces every other
  NYISO row to `heat_mmbtu` / `gross_mwh` EXACT and CO2 / NOx / SO2 masses to
  ≤ 1e-3 kg (float summation order; max rel 3.6e-7 on so2, 5.9e-12 on co2);
  2018 rows cannot be re-derived (the 2018 unit-level vintage was stripped at
  BLOAT-S2) and 2022 / 2026 rows sit behind the one-shot holdout-intake guard —
  all three are carried through frozen (declared footprint below).
* **`cc_capacity_reconcile` table.** `derive_cc_capacity_reconcile.py --iso
  NYISO --mode both --years 2023 2024 2025` reproduces the committed 14 rows
  EXACTLY and adds **one row the routing creates: Astoria Energy 55375 `raise`
  595.0 → 610.4** (CT1 + CT2 p99.9 on the corrected boundary). Per-year
  demonstrated peaks (CAMPD net = gross × 0.975) against the caps: Zeltmann
  56196 p99.9 **553.8 / 682.5 / 547.9** vs cap 560.0 — 2024 carries 21 h above
  the cap, 2,268 MWh; Cricket Valley 57185 1,079.8 / 1,067.9 / 1,088.1 vs
  1,086.9 (23 h / 35 MWh above, 2025); Athens 55405 1,054.2 / 1,066.1 /
  1,064.9 vs 1,064.7 (1 / 13 / 9 h; 7.8 / 46.8 / 143.3 MWh); Valley 56940
  692.2 / 696.2 / 697.1 vs 696.1; Flynn 7314 106.5 / 106.5 / 109.2 vs 108.2.
  The keeper's fleet loader already clips Zeltmann's RAW pmax sum 662 → 560 as
  the trusted bound; `fleet_to_bins`' nameplate rescale then lifts the LP
  capacity (nyiso-186 read pmax / p99.9 = 0.891 at a 700 MW gross 2024 peak,
  i.e. ≈ 624 MW).
* **Bethlehem 2539.** Per eGRID vintage (PLNT / UNT / GEN sheets):

  | vintage | CT net (GEN 5/6/7, TWh) | ST net (GEN 8 "CA", TWh) | ST / CT | PLHTIAN / CT net | `PLHTRT` | block HR at the plant's own ST/CT 0.49 |
  |---|---|---|---|---|---|---|
  | 2018 | 3.445 | 1.697 | 0.492 | 10.33 | 6.923 | 6.93 |
  | 2019 | 3.028 | 1.516 | 0.501 | 10.42 | 6.941 | 6.99 |
  | 2020 | 3.332 | 1.644 | 0.494 | 10.26 | 6.868 | 6.88 |
  | 2021 | 3.543 | 1.762 | 0.497 | 10.28 | 6.865 | 6.90 |
  | 2022 | 2.805 | 1.457 | 0.519 | 12.55 | 8.261 | 8.42 |
  | **2023 (applied)** | 4.090 | **0.268** | **0.065** | 10.30 | **9.665** | 6.91 |
  | 2024 | 3.639 | **0.000** | **0.000** | 10.44 | 10.444 | 7.01 |

  The heat per CT-generator MWh is invariant (10.26–10.44) in every vintage
  except 2022 (EIA-923 reports ZERO net generation for February and November
  2022 — a filing gap on the net side); the steam generator's filed net
  generation collapses from a third of the plant to 6 % (2023) and exactly
  zero (2024) while the three CTs report 7,900–8,000 operating hours each.
  CAMPD's unit-level record shows the complementary regime change: 2018–2023
  gross is CT-only (gross / EIA-923 net 0.66–0.96; running-hour HR 10.1–10.5)
  and 2024–2025 gross is the whole block (gross / net 1.53; HR **6.85 /
  6.90**), i.e. the CEMS gross-load convention changed in 2024 and the EIA-923
  generator filing lost the steam turbine in 2023–2024. Three independent
  bases — eGRID 2018–2021 (6.87–6.94), CAMPD 2024–2025 full-block (6.85–6.90),
  and the CT-heat identity at the plant's own steam share (6.88–7.01 in every
  vintage) — put the block at ≈ 6.9–7.0 MMBtu/MWh; the applied 9.665 is
  +40 %. The unit sidecar's EIA-923 comparison for 2539 in 2023–2024 is on the
  same understated basis (nyiso-186 §2.1's −2.275 TWh).

**Not read:** any hourly dispatch, price or criterion of any arm; the control's
comparison to the keeper (measured in §3 G-CONTROL, after this push).

---

## §1 — THE OBJECTS

**Object 1 — the Astoria routing's remaining footprint (one identity, two
artifacts).** Arm 1R: the keeper recipe on the re-derived
`campd_ramp_envelopes_NYISO.csv` (committed invocation, remap armed). Arm 1RE:
Arm 1R plus the re-derived `plant_emission_rates_v2.parquet` (the curate seam
now applies `CAMPD_UNIT_PLANT_REMAP` per `(facility, unit)` — the SAME registry
at the SAME point as the plant-grain normalizer, rule 19; the derive gains a
year-scoped `--merge` so one ISO's rows re-derive without rewriting the rest).
The emission increment is read as 1RE − 1R. ZERO `scenario_config` fields,
ZERO parameters; rule 23: the data change is EIA-860's plant boundary (the
identity nyiso-186 §3 established), applied to the two artifacts nyiso-187
measured and did not carry.

**Object 2 — `cc_capacity_reconcile` (cell U → tested).** Arm 2: the keeper
recipe plus the ONE registered flag (`--cc-capacity-reconcile`, path resolved
per ISO), on the COMMITTED artifacts, with the reconcile table re-derived at
HEAD (the committed 14 rows + the 55375 raise row the routing creates — the
derive's own output under its committed invocation; a hand-trimmed table is
forbidden). Mechanism: per-plant `CC_REGULAR` LP capacity bounded at the
plant's CAMPD demonstrated peak (a measured capability, rule 13) — the
mechanism whose H-B1 (phantom capacity actually run) fired at Zeltmann in
2023 / 2025 (nyiso-186 §2.2).

**Object 3 — Bethlehem 2539's eGRID vintage artifact.** A MEASUREMENT object
with a pre-declared admissibility rule for any repair (§3). The applied 2023
`PLHTRT` is a filing artifact (§0); the question is whether a zero-parameter,
threshold-free, source-field identity reaches the APPLIED vintage. If none
does, the object is adjudicated and handed forward with the instrument fully
specified — NOT solved (S4 below).

## §2 — RULE 19 `[R-ONE-MECH]`: what each artifact already feeds, so nothing stacks

| artifact / flag | consumer in the keeper | what the arm changes | what stays |
|---|---|---|---|
| `campd_ramp_envelopes_NYISO.csv` | `ramp_limits` (K) → `build_ramp_groups` → P1 ramp rows | 55375 / 57664 measured rows; the `(0, CC)` fallback the 14 groups read | CT / ST rows, every other plant row, the loader's gross→net rebasis |
| `plant_emission_rates_v2.parquet` | `use_plant_emission_rates_v2` (K) → `apply_plant_emission_rates_v2` → `mc` carbon term under `state_carbon_pricing` (RGGI) | 55375 / 57664 plant-grain rates; nothing else beyond float noise | every other plant; 2018 / 2022 / 2026 rows frozen |
| `cc_capacity_reconcile_NYISO.csv` | `cc_capacity_reconcile_path` (K): the loader's trusted bound `max(nameplate, p99.9)` on RAW pmax | the FLAG: the final LP `capacity_mw` bounded at `reconciled_mw` after the summer-derate rescale; 12 caps + 3 raises | the trusted-bound guard (same table, same peaks) |
| eGRID 2023 `PLHTRT` (2539) | the fleet's base heat rate; `egrid_identity_heat_rates` / `egrid_family_heat_rates` do not reach a single-family CAMPD-covered plant; `_egrid_boundary_hr_repairs` requires PLHTRT > 11.5 AND a co-located sibling | (measurement only) | — |

No arm stacks a second mechanism on the same phenomenon: the ramp and
emission arms re-derive inputs an ARMED mechanism already reads; Arm 2 arms a
registered flag whose table the keeper already half-reads.

## §3 — MEASUREMENT AND VERDICT RULES (fixed now)

**G-CONTROL.** The same-HEAD control (`nyiso188_control`) vs the committed
keeper: hourly zonal P1 prices, all three years. Bit-identical (max |Δ| = 0)
⇒ the keeper is the baseline; else the control is the baseline and the drift
is named. Either outcome passes; an un-measured premise does not.

**G-DELTA (per arm).** Arm 1R / 1RE: ZERO `scenario_config` fields differ from
the control; artifact diffs confined to (a) ramp: rows keyed 55375 / 57664
AND the `(0, CC)` class-fraction row — declared, the object; any OTHER row
moving is a STOP; (b) v2: rows keyed 55375 / 57664; any other NYISO plant's
plant-grain backcast rate (2023–2025) moving by > 1e-6 t/MWh is a STOP (the
float noise measured in §0 is 6e-12 relative). Arm 2: exactly the two fields
`cc_capacity_reconcile` / `cc_capacity_reconcile_path`; the table is the
derive's committed-invocation output (15 rows, §0).

**Verdict rule (every arm, verbatim from the lane charter):** **REJECTED
PROBE** iff C2, C3a, C3b or C8 flips PASS → FAIL against the baseline; else
**KEEPER CANDIDATE** to the owner with EVERY regression at full magnitude
(C1 per class-year, C3a / C3b per year, D-4 rows, `determination`). A
candidate is promoted only by the owner's ruling. LOYO: no fitted scalar
exists in any arm, so leave-one-year-out reduces to the per-year record — the
same direction in every year is reported, a sign flip across years is named.

**Pre-declared expectations (falsifiable, NOT bars):**
* 1R: the class-level energy moves < 0.1 TWh in every year (envelopes at
  ~50 % of pmax per hour bind rarely); 55375 and 57664 are enveloped
  separately (372 / 449 and 416 / 454 gross, rebased); the 14 fallback
  readers' envelopes loosen by 1.9 % / 5.0 % (no direction claim on them).
* 1RE − 1R: 57664 (0.4206 → 0.398) and 55375 (0.381 → 0.364) each price a few
  tenths of a $/MWh cheaper under RGGI; both gain energy; no class or price
  claim.
* 2: the 2024 `CC_REGULAR` excess SHRINKS (headroom removed at the three
  carriers: Zeltmann ≈ 624 → 560, Cricket Valley 1,312.5 → 1,086.9 — mostly
  its 296.6 MW / 15.78 HR peak band, Athens 1,221.6 → 1,064.7) and moves to
  other CCs / steam within the pinned gas family; Zeltmann's 2024 energy
  falls by ≤ 10 %; the 21 h / 2,268 MWh Zeltmann delivered above 560 MW in
  2024 become infeasible (reported as the cap's cost); no price claim.
* 3: no solve.

**Object 3 admissibility rule (fixed now).** A repair is BUILT only if it is
(a) zero-parameter and threshold-free — every constant a published source
field or one already in `constants.py`; (b) source-internal — decided from
eGRID / EIA-923 / EIA-860 / CAMPD fields, never from a model residual;
(c) regenerating per vintage (the identity derive's posture: pooled rate,
per-vintage and LOYO record); and (d) it REACHES the applied 2023 vintage.
Candidates adjudicated: (i) the identity derive's own rule (pool over ALL
vintages, no choice) applied to 2539 → 7.85, LOYO [7.51, 8.05] — a knowingly
contaminated pool, and a general "pooled-vintage basis for every plant" is a
fleet-wide lever, not a footprint; (ii) a generator-completeness identity
(every EIA-860 operating generator of the block reports `GENNTAN > 0` in the
vintage) — threshold-free, reaches 2024 (CA = 0.0) but NOT 2023 (CA =
267,718); (iii) the CT-heat identity `PLHTIAN / Σ_CT GENNTAN / (1 + ST/CT)`
— reaches 2023 only through a steam share (the plant's own 2018–2022 record
0.49–0.52, or the EIA-860 nameplate ratio 310.2 / 582.9 = 0.532), i.e. a
physical bound that is NOT yet in `constants.py` and needs the owner.
**S4:** if no candidate satisfies (a)–(d), Object 3 is handed forward with
the measurement and the instrument, no solve.

## §4 — FORBIDDEN

F1 no band, anchor, start-cost, min-load, floor or envelope coefficient
moves; F2 no per-plant dict beyond the accepted registry form (the remap
entries already committed; the reconcile table is the derive's output); F3 no
availability haircut, no pin to CEMS, no rescale to a residual; F4 no
re-opening of G (`scuc_load_pocket_commitment`), of the nyiso-96 CT markup
trade, of C3a-2025, of the 2024 `CC_REGULAR` disposition (nyiso-187 §2) — no
CC volume lever, no band move; F5 one delta per arm (1R: ramp; 1RE: + v2;
2: the flag); F6 no edit of any bar after the first arm criterion is read;
F7 no CAISO edits (the remap's CAISO rows, the CAISO reconcile table
untouched); F8 2023–2025 only, no marker requested; F9 no hand edit of any
derived artifact.

## §5 — STOP CONDITIONS

S1 G-DELTA fails on an arm ⇒ that arm is not solved (or, if solved, not
registered as a candidate). S2 memory: at most two concurrent invocations;
a control never runs concurrently with a file-swapped arm; swapped files are
restored before any other solve. S3 every completed non-control solve is
registered THIS session (rule 15). S4 Object 3: no repair satisfying
§3 (a)–(d) ⇒ no solve. S5 the control drifts from the keeper ⇒ the control
is the baseline for every arm and the drift is reported in the finding.
