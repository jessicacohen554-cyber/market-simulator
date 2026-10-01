# PRE-REGISTRATION — nyiso-189 (`backcast-calibration` lane, second sitting): the owner-chosen form B2 for the eGRID steam-generator filing artifact — `egrid_steam_collapse_heat_rates`, ONE new field, ONE arm, bars fixed before any solve

**Session:** nyiso-189 (continuation), NYISO backcast-calibration track,
2026-09-05. **Branch:** `claude/nyiso-189-bethlehem-heat-rate-7suj05`, fresh
off `origin/main` at `d9f034f0` (carries PR #4733, the nyiso-189 census and
decision card; PR #4720; every lane merge through 2026-09-05 00:10 UTC).
**Keeper at entry:** `2026-09-04-nyiso-188-combined`
(`results/calibration/nyiso188_combined`) — **CALIBRATED**, grade 7, fails 0,
C3c ledgered; C3a +7.9 / +3.8 / −6.9 %; C1-2024 `CC_REGULAR` +2.05 TWh PASS.
NYISO holds neither `complete` nor `final` (the D56 re-declaration is issued,
not landed); freeze ACTIVE; no marker requested.

**THIS DOCUMENT IS COMMITTED AND PUSHED TO `origin` BEFORE THE MECHANISM IS
BUILT AND BEFORE ANY SOLVE OF THIS SITTING.** At the time of writing NO solve
of this sitting exists — not the control, not the arm. The only LP artifacts
read are the committed keeper's.

---

## §0 — DISCLOSURE: the owner ruling, and what has been measured (no LP)

**The owner ruling (this sitting, 2026-09-05, `AskUserQuestion`, three
questions from `docs/DECISION-CARD-nyiso189-bethlehem-vintage-form-2026-09-04.md`
§3, answered verbatim as offered):**

1. Form: **"B2 identity, record-admitted"** — the CT-heat identity
   `PLHTIAN / Σ GENNTAN(CT) / (1 + ST/CT)`, a vintage admitted when its filed
   steam share departs from the plant's own record.
2. Steam share: **"Plant's own T1-clean median"** (a measured record per
   plant; not the EIA-860 nameplate ratio).
3. The plant-history bound — *"a vintage whose filed ST/CT lies below the
   plant's own minimum over its T1-clean vintages is inadmissible"* —
   **"Yes, authorize"**, as the admissibility rule (a rule choice, no external
   constant, no fitted number).

**Read this sitting:** FINDING-nyiso188 §4 / §5.2, PREREG-nyiso188 §3 (the
Object-3 admissibility rule: zero-parameter, threshold-free, source-internal,
per-vintage, reaching the applied 2023 vintage), PREREG-nyiso189 (the census
pre-registration), the decision card, matrix §5.5, the NYISO shard cells
`egrid_identity_heat_rates` (K), `cc_capacity_reconcile` (K),
`scuc_load_pocket_commitment` (G), CLAUDE.md rules 1, 5, 12–16, 19, 21–25,
27, 28. **Code read:** `scripts/data/process_eia860.py::_join_egrid_heat_rate`
(the fleet's base heat rate is eGRID 2023 `PLHTRT`, `egrid2023_data_rev2.xlsx`
/ `PLNT23`, window 3,000–30,000 Btu/kWh, one vintage for every backcast
year); `fleet/eia860.py::apply_egrid_identity_heat_rates` and its call site in
`load_fleet_from_csv` (the seam: after the eGRID-input seam and the family
construction, after `measured_chp_heat_rates`, before the CHP hand-factor
correction and the binned-fleet cache write); `fleet/assembly.py` (the three
`load_fleet_from_csv` call sites forwarding the identity / family flags);
`scripts/replay_keeper.py --set` (routes a config field through the generic
`prb_overrides` channel, applied by `cfg.with_overrides` in
`solve_and_persist`); `scripts/gen_nyiso188_attestation.py` (the computed
G-check pattern); `scripts/data/derive_egrid_family_heat_rates.py`
(`APPLIED_VINTAGE = 2023`, the join's own vintage).

**Measured this sitting, BEFORE this document (eGRID GEN / PLNT sheets only,
via the committed census record — NO LP):**

* **The census reproduces byte-identically at HEAD** (`scripts/probes/
  nyiso189_gen_collapse_census.py` → both CSVs `cmp`-identical to
  `results/calibration/_nyiso189_gen_collapse_census/`).
* **The literal bound is degenerate and needs an operational form.** Evaluated
  over all 38 plants × 7 vintages of the census: with the vintage under test
  INCLUDED in "its T1-clean vintages", no T1-clean vintage can lie below the
  set's own minimum — the rule collapses to B1 and does NOT reach Bethlehem
  2023 (the card's stated reach). With the vintage EXCLUDED (the card's own
  arithmetic, "0.065 < 0.49"), the minimum-share vintage of EVERY plant lies
  below the others' minimum — it fires at **35 of 38 plants** (one vintage
  each), and at the applied 2023 vintage at four: Bethlehem 2539 (0.065 vs a
  record [0.492, 0.519]) and three noise minima — Indeck Corinth 50458
  (0.573 vs [0.573, 0.573]), Sterling 50744 (0.413 vs [0.413, 0.414]),
  Saranac 54574 (0.471 vs [0.479, 0.546]). A rule that fires at every plant is
  not a test of anything. **The operational form fixed here (before any
  solve): "below the plant's own record" means below the record's minimum BY
  MORE THAN THE RECORD'S OWN RANGE** — `ST/CT(v) < min(R) − (max(R) − min(R))`
  with `R` = the plant's T1-clean vintages other than `v`. The unit is the
  plant's own observed variability; no external constant enters. Over the
  census it fires at SIX plant-vintages — Bethlehem 2023, Castleton 10190
  2019, Bethpage 50292 2022, Cornell 50368 2024, Batavia 54593 2022,
  Caithness 56234 2018 — and at the applied vintage at **exactly one:
  Bethlehem 2023.** The artifact records BOTH tests per row
  (`below_ref_min`, `below_ref_fence`); the mechanism reads the fence. The
  owner may overturn this operationalization; the alternative's extra 2023
  reach is quantified in §3 below as a stated sensitivity (no solve).
* **The CT-side guard (the finding's fact 1, made a test).** The identity is
  valid only when the CT generators' filing is intact — the heat per
  CT-generator MWh `PLHTIAN / Σ GENNTAN(CT)` lies within the plant's own
  reference range `[min, max]` over `R`. Where a plant's filing instead moved
  the steam output INTO the CT row, the heat per CT-MWh drops out of the
  record and `PLHTRT` is already the block rate — Richard M Flynn 7314 is
  that case (2018: CT 421,847 + CA 223,993 MWh at 12.74 per CT-MWh; 2019–2024:
  CA = 0, 8.34–8.70 per CT-MWh, `PLHTRT` flat at 8.3–8.7 — the block rate in
  both regimes). Source-internal, threshold-free.
* **The reference set needs two members** (`|R| ≥ 2`): a range is defined by
  two points. Definitional, not a threshold — with one reference the fence
  and the guard both degenerate to a point.
* **Reach at the applied vintage (2023), computed from the census record:**

  | plant | admitted by | `R` | ref ST/CT [min, max], median | fence | ST/CT 2023 | heat / CT-MWh 2023 (ref range) | `PLHTRT` 2023 → identity |
  |---|---|---|---|---|---|---|---|
  | **Bethlehem 2539** (`CC_REGULAR`, 750 MW, Capital) | fence | 2018–2022 | [0.492, 0.519], **0.4973** | 0.465 | 0.065 | 10.298 (in [10.26, 12.55]) | **9.665 → 6.877** |
  | **World Generation X 54131** (`CC_CHP`, 56 MW) | T1 | 2018–2022, 2024 | [0.370, 0.418], **0.4018** | 0.322 | 0.000 | 9.807 (in [9.73, 12.33]) | **9.807 → 6.996** |
  | Richard M Flynn 7314 | — (`|R|` = 1; guard fails: 8.70 vs [12.74]) | 2018 | — | — | 0.000 | 8.704 | 8.704 (kept) |
  | Ravenswood 2500 | — (`|R|` = 1; mixed-family, `egrid_family_heat_rates` K covers it) | 2018 | — | — | 0.000 | 12.454 | kept |
  | Lederle 10521 | — (`|R|` = 1) | 2018 | — | — | 0.070 | 6.162 | 5.759 (kept) |

  The 2024 vintage's rows (Bethlehem T1 → 6.98; others) are written to the
  artifact as the per-vintage record and are NOT read by the fleet (the join
  is 2023 for every backcast year).

**Not read:** any hourly dispatch, price or criterion of any arm or control
of this sitting.

## §1 — THE OBJECT: ONE new field, ONE arm

**`ScenarioConfig.egrid_steam_collapse_heat_rates: bool = False`** (CLI
`--egrid-steam-collapse-heat-rates`; replay `--set
egrid_steam_collapse_heat_rates=true`), consuming the committed per-ISO
artifact `data/raw/_processed-legacy/egrid_steam_collapse_heat_rates_<ISO>.csv`
written by `scripts/data/derive_egrid_steam_collapse_heat_rates.py`. Rule
28(c): its base row + a cell in every ISO shard land in the same PR. Rule 25:
per-ISO artifact, a no-op for an ISO with none. Rule 24: the artifact is the
derive's output over the ISO's whole population; no plant is named in code.

**The derive (fixed now; every constant a published field or the plant's own
record):**

* Population: every EIA plant the ISO's fleet carries a `CC_REGULAR` or
  `CC_CHP` generator for, that eGRID files ≥ 1 operating `CA` generator AND
  ≥ 1 operating `CT` generator for (the census's population, 38 plants in
  NYISO; single-shaft and steam-less plants excluded and listed).
* Per (plant, vintage) over every on-disk eGRID vintage: `ct_net`, `ca_net`,
  `st_ct = ca_net / ct_net`, `T1` (an operating CA generator at exactly zero
  net generation while `ct_net > 0`), `heat_per_ct = PLHTIAN / ct_net`,
  `plhtrt`; the reference set `R(v)` = the plant's T1-clean vintages ≠ v;
  `ref_n`, `ref_st_ct_min/max/median`, `ref_heat_per_ct_min/max`;
  `below_ref_min` (the literal LOO reading, recorded), `below_ref_fence`
  (the operational bound above), `ct_side_intact` (the guard),
  **`admitted = (T1 or below_ref_fence) and ct_side_intact and ref_n >= 2`**,
  `identity_hr = heat_per_ct / (1 + ref_st_ct_median)` (written for EVERY
  row, admitted or not, so the finding can quote what the rule declines),
  `applied = (vintage == 2023)`.
* `--check` re-derives and byte-compares against the committed artifact.

**The consumer:** `fleet/eia860.py::apply_egrid_steam_collapse_heat_rates`,
called in `load_fleet_from_csv` immediately AFTER
`apply_egrid_identity_heat_rates` (same seam class, same precedence), gated
by the field; every generator of a plant whose `applied & admitted` row
exists takes `identity_hr`, EXCEPT generators already repriced by
`measured_chp_heat_rates` or `egrid_identity_heat_rates` on this load and
plants the family construction covered (rule 19: one measured rate per
plant). Off, the artifact is not read and the fleet is byte-identical.

## §2 — RULE 19 `[R-ONE-MECH]`: what already prices the two reached plants

| plant | today's heat rate and its source | mechanisms that could reach it | verdict |
|---|---|---|---|
| Bethlehem 2539 | 9.665 = eGRID 2023 `PLHTRT` via the plant-grain join | `egrid_identity_heat_rates` (CAMPD-less plants only — 2539 has CEMS), `egrid_family_heat_rates` (multi-family only — single CC family), `_egrid_boundary_hr_repairs` (PLHTRT > 11.5 + co-located sibling — neither), `measured_ct_heat_rates` (CT classes only), `measured_chp_heat_rates` (CHP classes only), the CHP hand factor (NYISO ∉ `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`) | nothing else reaches it; the new field is the ONLY mechanism |
| World Generation X 54131 | 9.8065 = eGRID 2023 `PLHTRT` (credited basis) | `measured_chp_heat_rates` (armed) — its NYISO artifact row carries `flag = above_physical_band` (12.90 vs the class band), so it is NOT applied; the CHP hand factor (NYISO not in the set) | the new field is the ONLY mechanism; the identity stays on eGRID's credited basis (`PLHTIAN`), the same basis the incumbent carries |

Nothing stacks. The arm arms ONE field; every other field of the keeper
recipe is carried verbatim by the replay.

## §3 — MEASUREMENT AND VERDICT RULES (fixed now)

**Control** = `results/calibration/nyiso189_control`: `scripts/replay_keeper.py
results/calibration/nyiso188_combined --out-dir … --years 2023 2024 2025`, the
same-HEAD replay of the keeper recipe on the committed artifacts — an
instrument (the nyiso-188 chain pattern). **Arm** =
`results/calibration/nyiso189_steam_identity`: the same command plus
`--set egrid_steam_collapse_heat_rates=true`. Both solved at this HEAD, years
sequential within each invocation, the two invocations concurrent (rule 12:
two per-plant NYISO LPs on a 15 GB box, the nyiso-188 S2 posture).

**G-CONTROL.** Control vs the committed keeper: hourly zonal P1 prices, all
three years. Bit-identical (max |Δ| = 0) ⇒ the keeper is the baseline; else
the control is the baseline and the drift is named (HEAD has moved through
eleven lane merges since the keeper's basis `8f5cb32c`; a drift here is a
finding about those merges, reported, and does not stop the arm). Either
outcome passes; an un-measured premise does not.

**G-DELTA.** The arm's `scenario_config` differs from the control's on
EXACTLY `{egrid_steam_collapse_heat_rates: false → true}` (absence-normalized
against `ScenarioConfig` defaults as in the nyiso-188 generator); any other
field riding along is a STOP.

**G-INPUTS.** The committed artifact reproduces under `--check`; its T1 count
per plant equals the census's (5 plants: 2539 / 54131 / 7314 / 2500 / 10521,
the same vintages); its `applied & admitted` set is EXACTLY {2539, 54131};
its identity rates are 6.877 / 6.996 (to 3 dp); the arm fleet carries
Bethlehem's generators at 6.877 and World Generation X's at 6.996 while the
control fleet carries 9.665 / 9.8065 (read from the binned-fleet side cache
of each load, or re-loaded in-process with the flag on/off).

**G-DOF.** Zero new DOF entries (the keeper's 13 / 6 verbatim); zero
constants chosen: the fence unit is the plant's own range, the guard is the
plant's own range, `|R| ≥ 2` is definitional, `APPLIED_VINTAGE = 2023` is
the join's own.

**G-ENGAGE.** On the arm's own hourlies: Bethlehem's mean installed `mc`
falls in every year and its annual energy rises in every year (the finding
records the magnitudes); the arm is ENGAGED. (An arm whose Bethlehem energy
does not rise is a finding about Capital-zone merit, reported, not a STOP.)

**Verdict rule (verbatim from the lane charter):** **REJECTED PROBE** iff C2,
C3a, C3b or C8 flips PASS → FAIL against the baseline; else **KEEPER
CANDIDATE** to the owner with EVERY regression at full magnitude (C1 per
class-year, C3a / C3b per year, C3c hours, D-4 rows, `determination`). Under
the owner's standing-disposition formula (delivered at nyiso-187, applied at
nyiso-188), a candidate this session RECOMMENDS is promoted in the same
session with every regression stated; a candidate it does not recommend is
handed to the owner. LOYO: no fitted scalar exists, so leave-one-year-out
reduces to the per-year record — the same direction in every year is
reported, a sign flip across years is named.

**Pre-declared expectations (falsifiable, NOT bars):**

* Bethlehem's variable cost falls by ≈ 2.79 MMBtu/MWh × delivered gas
  (≈ $7–10/MWh at 2023–2025 NY gas), moving it INTO merit in Capital:
  its energy rises materially from the keeper's (2023 loading 0.30 of
  available, nyiso-186 §5.3); the class `CC_REGULAR` total is pinned by the
  gas family, so the energy comes from other CCs (Athens, Cricket Valley,
  Empire) and `ST_GAS`, not from a class-level change.
* **C3a moves DOWN in every year** (a cheaper 750 MW block on the Capital
  side of the Central-East interface): 2023 +7.9 % and 2024 +3.8 % improve;
  **2025 −6.9 % worsens toward the −10 % band edge — the one route to a
  REJECTED verdict this arm carries, stated now.** No price magnitude is
  claimed.
* C1-2024 `CC_REGULAR` (+2.05 TWh PASS) is not expected to move at the class
  grain (within-class reshuffle); C8 `CC_REGULAR` / `ST_GAS` D-2 shares are
  not expected to flip.
* World Generation X (56 MW `CC_CHP`) is immaterial at the class grain.

**The stated sensitivity (no solve): the literal LOO-min reading.** Had the
mechanism read `below_ref_min` instead of the fence, three more 2023 rows
would be admitted (each passing the CT-side guard at |R| = 6): Indeck
Corinth 50458 `PLHTRT` 7.654 → identity 7.654 (Δ 0.000), Sterling 50744
8.558 → 8.572 (Δ +0.014), Saranac 54574 10.111 → 9.838 (Δ −0.273 on a 250 MW
cogen). Where the filing is intact the identity reproduces `PLHTRT`, which is
why the fence and the literal reading differ only at the noise minima — the
finding reports this; no second arm is solved on it.

## §4 — FORBIDDEN

F1 no band, anchor, start-cost, min-load, floor, envelope, share or
threshold moves; the share is the plant's own reference median, never a
typed number; F2 no per-plant dict or carve — the derive runs over the
population and the consumer reads only the artifact; F3 no availability
haircut, no pin to CEMS, no rescale to a residual; F4 no re-opening of G
(`scuc_load_pocket_commitment`), of the nyiso-96 CT markup trade, of
C3a-2025 (DECISION-CARD-nyiso148 Q1), of the 2024 `CC_REGULAR` disposition
(nyiso-187 §2), of Zeltmann's pooled cap; F5 one delta in the arm (the
field); F6 no edit of any bar after the first arm criterion is read; F7 no
CAISO / other-ISO edits beyond the rule-28(c) `U` cell lines; F8 2023–2025
only, no marker requested; F9 no hand edit of the derived artifact; F10 the
2024 rows and the non-applied vintages are record only — nothing reads them.

## §5 — STOP CONDITIONS

S1 G-DELTA or G-INPUTS fails ⇒ the arm is not registered as a candidate (it
is still registered as a probe, rule 15). S2 memory: at most two concurrent
invocations; no file-swapped arm (there is none — the artifact is committed
before the arm solves and the control does not read it). S3 every completed
non-control solve is registered THIS sitting (rule 15); the control registers
nothing if bit-identical (slim files committed as the instrument), else it
is registered as the baseline. S4 the control drifts from the keeper ⇒ the
control is the baseline for the arm and the drift is reported. S5 a REJECTED
verdict ⇒ the field stays default-off, the NYISO cell reads `R` with the
flip named, the artifact and derive stay committed as the record.
