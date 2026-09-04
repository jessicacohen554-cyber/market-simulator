# PRE-DECLARATION — capx D52: the NYISO adequacy-requirement devintage (D45 §5.2.4 items 1–2) A/B + the conditional curve-ON probe

**Written BEFORE any code and pushed before the first solve.** Graded at full
magnitude, misses included, in `FINDING-capx-d52-<date>.md`. Two things are
fixed here that the repair itself cannot move: every prediction below, and the
§6 re-open condition verbatim. The cache keys are appended in §7 AFTER the
fields exist and BEFORE any solve (a key cannot be computed for a field that does
not exist yet; D48 §1 precedent).

**Lane:** capx D52 — NYISO's per-ISO repair lane, the successor D45's §9 close-out
names (`FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md` §5.2.4 items 1–2, §6).
Branch `claude/capx-d52-nyiso-devintage-sl3rj2`, fresh off `origin/main`
(`a35c9f9`). **NOTHING ARMS.** Two `ScenarioConfig` fields land DEFAULT-OFF, the
A/B registers SUFFIXED (`nyiso-t1h-d52-devintage`), the conditional probe (if run)
registers SUFFIXED (`nyiso-t1h-d52-curveon`), the bare `nyiso-t1h` verdict key is
untouched, no keeper / shard / marker, the backcast namespace untouched. Both
arming recommendations return to the owner on their pre-stated conditions.

**Rule 13 / 14 / 21 / 25 discipline (binding).** Every value is a published
NYSRC/NYISO market-design PARAMETER: the NYSRC 2026-27 IRM Study Technical
Appendices, Appendix D §D.1.1 **Table D.2 "New York Control Area ICAP to UCAP
Translation"** (report p.68 = PDF p.86; sha256
`714aeeb9156795108147982f93cf90f885ed110835e0a6f2fa257f809da419d5`, D45 §8 —
re-fetched and hash-matched this session, the rows below re-read from the PDF
text), columns *Forecast Peak Load (MW)*, *Installed Capacity Requirement (%)*
(= the EC-approved IRM), *Derate Factor*, *ICAP Requirement*, *UCAP
Requirement*. The Potomac SOM margins and cleared quantities are validation
observables, never targets. Nothing below was sized by a residual; the sign
readings are D45's (§5.2.4) and where the consistent construction contradicts
D45's restated magnitudes (§2 below) the contradiction is stated here, before
the solve.

---

## 0. What is being measured

Two default-OFF fields, one A/B arm (BOTH on) vs the bare `nyiso-t1h`:

| field | what it does when armed (NYISO only, rule 25) | source rows |
|---|---|---|
| `nyiso_requirement_forecast_peak` | the NYCA requirement is priced on the **NYSRC ICAP-market forecast peak** of the capability year (Table D.2 col. 1) instead of the model's own peak — the D45 item-1 repair | 32,333 / 31,767 / 32,049 / 31,542 / 31,469 MW (2021/22 … 2025/26) |
| `nyiso_requirement_vintage_factors` | the requirement factor is the capability year's **adopted IRM × (1 − derate)** instead of the single-vintage `1.244 × 0.8679 = 1.0797` — the D45 item-2 repair (the D40 axis); hold-last beyond the table as the last published pair (`1.244 × 0.870 = 1.0823`), pre-table falls through | IRM 20.7 / 19.6 / 20.0 / 22.0 / 24.4 %; derate 0.0877 / 0.0978 / 0.1014 / 0.1321 / 0.1300 |

BOTH on ⇒ the in-table requirement IS Table D.2's published UCAP requirement
(35,604 / 34,277 / 34,559 / 33,397 / 34,059 MW), the model's peak dropping out
exactly as it does under the NEISO Net ICR (D40) and PJM FPR paths. Same recipe
otherwise: `run_capacity_hindcast.py --iso NYISO --start-year 2021 --end-year 2025
--vintage 2020 --fuel-variant realized --entry-screen-diagnostics`, the D45-R L2
recipe (bare `nyiso-t1h`, key `91686abe7a744a88`, HEAD `334be8c2`, keeper
`2026-09-04-nyiso-186-astoria-identity`).

**Vintage gate (rule 13, the D42/D44 construction).** A Table D.2 row of
capability year Y/Y+1 is used in model year Y only. Every parameter in that row
is fixed by the market BEFORE the capability year begins (May 1, Y): the IRM is
adopted by the NYSRC Executive Committee in December Y−1 (dates on file in the
committed csv: 2020-12-04 / 2021-12-03 / 2022-12-09 / 2023-12-08 / 2024-12-06),
the forecast peak is the load forecast NYISO adopts for that capability year's
ICAP requirement, and the summer derate factor is posted ahead of the May
capability period. The resolver never reads a later capability year's row for an
earlier model year and the hold-last extends the table's forward edge only
(tests). Forward story: the same construction regenerates every capability year
from the then-current Gold Book forecast + adopted IRM + translation factor.

## 1. A correction to D45 §5.2, stated BEFORE the solve

D45 §5.2.1–5.2.2 read the model's requirement from the ledger field
`adequacy_requirement_mw` (32,612 / 31,300 / 34,395 MW in 2023 / 2024 / 2025) and
the model's entering firm from the reserve-margin identity of the prior ledger
year (36,145 / 34,745 / 35,829). Both readings are off, and in opposite
directions in 2023:

1. **The ledger requirement is not the requirement the screens consumed.** The
   runner computes the CR-1 position, the reliability floor and the backstop on
   the capacity-screen seam's peak — the weather-year (2024) load compounded by
   the demand-growth path to the target year (`_scale_demand`) — while the
   ledger's `adequacy_requirement_mw` (and `peak_demand_mw`) are written later
   from the LP's MEASURED hindcast load. Backed out of the L3 ledger positions
   against the reconstructed entering fleet (class-EFORd reconstruction,
   ±25 MW; the 2024 row reproduces the ledger position exactly): the seam peak
   is ≈ **28,640 / 28,990 / 29,343 MW** (2023 / 2024 / 2025; a 1.22 %/yr growth
   series through the 2024 weather year) and the requirement the screens saw
   ≈ **30,922 / 31,300 / 31,682 MW** — 3.6 / 2.1 / 2.4 GW BELOW the published
   34,559 / 33,397 / 34,059. The 2025 "other way by 0.4 GW" (D45 §5.2.2, the
   P7 falsifier) is an artifact of the ledger's realized 2025 peak (31,857, a
   hot summer); the screens priced 2025 against a 29,343 MW peak and were 2.4 GW
   LOW, the same direction as every other year.
2. **The identity firm for 2023 is the 2021 fleet.** 2022 is bridged (no
   ledger peak), so the identity carries the 2021 post-evolution firm (36,145)
   into 2023; the fleet that entered 2023 had lost Indian Point 3 in the bridge.
   Reconstructed on the ENTERING fleet (`fleet_by_fuel_before` at class EFORd,
   prior-year pools, hydro / storage / tie as the ledger carries them), the
   entering firm is **35,163 / 34,745 / 35,829 MW** — 2023 is 982 MW lower than
   D45 read it; 2024 and 2025 are unchanged.

Consequences for what this lane predicts (all zero-solve; instrument
`docs/handoffs/d52/predecl-positions-2026-09-04.py` computes the published-row
arithmetic; the seam values above are backed out by hand and are themselves a
prediction, P6):

| CY | screens' OFF position (seam) | D45's reading | published | **BOTH position (predicted)** | D45 §5.2.2's "model firm on published req" |
|---|---:|---:|---:|---:|---:|
| 2023 | 35,163 / 30,922 = **1.137** (= the L3 ledger) | 1.108 | 1.043 | 35,163 / 34,559 = **1.0175** (−2.5 pts) | 1.046 |
| 2024 | 34,745 / 31,300 = **1.110** | 1.110 | 1.058 | 34,745 / 33,397 = **1.0404** (−1.8 pts) | 1.040 |
| 2025 | 35,829 / 31,682 = **1.131** | 1.042 | 1.058 | 35,829 / 34,059 = **1.0520** (−0.6 pts) | 1.052 |

So the task's handed prediction (1.046 / 1.040 / 1.052) is right in 2024 and
2025 and 2.8 pts too high in 2023; the OFF gap is +9.4 / +5.2 / **+7.3** pts, not
+6.5 / +5.2 / −1.6.

## 2. Predictions

**P1 — requirement per year (arm), the ledger `adequacy_requirement_mw`:** 2021
**35,604**; 2022 bridge (no ledger requirement); 2023 **34,559**; 2024
**33,397**; 2025 **34,059** MW — Table D.2's UCAP requirement to within 1 MW,
independent of which model peak the ledger writes (the published peak replaces
both). Δ vs the ledger OFF values: +2,222 / +1,947 / +2,097 / −336; Δ vs the
requirement the screens actually consumed (§1): +3,637 / +2,097 / +2,377.
Decomposition (zero-solve, multiplicative, not additive): peak half alone
34,602 / 34,055 / 33,976; factors half alone 32,572 / 30,696 / 34,478 (on the
ledger peak) — the 2024 factor (22.0 %) is the one year the factor half moves
the requirement DOWN (−604), D45 item 2's stated sign. HIGH.

**P2 — the entering positions (arm), per §1:** **1.0175 / 1.0404 / 1.0520**, i.e.
**−2.5 / −1.8 / −0.6 pts** vs the published 1.043 / 1.058 / 1.058 — **every
scored year inside ±3 pts ⇒ the §6 re-open condition is predicted MET and the
conditional probe RUNS.** The 2023 reading sits 0.5 pt inside the band: a
reconstruction error of > 170 MW in the entering firm would flip it. Observed
through the new ledger observability fields (P6), not the identity. MED.

**P3 — FC-3 in the A/B is byte-identical (an honest "inert on FC-3" read).**
With the curve OFF the capacity term the screens see is the flat
`$110/kW-yr × UCAP fraction` (`104,500 $/MW-yr` on every diagnostics row),
independent of position; every L2 exit is exogenous (IP3 1,036 MW announced;
420 MW of dated 2023 CTs); no economic candidate fails at $110, so the smaller
admission budget (3,533 → 1,586 MW in 2023, 3,445 → 1,348 in 2024, 1,434 →
1,771 in 2025) caps nothing; the backstop does not fire (post-exit firm exceeds
the published requirement in every year — by only **+186 MW in 2023**, the one
reading to watch). Expected: `retire.total_gw` 1.457 (FAIL −14.9 %, the target
move), `false_retire` 0.256 GW (0.176 FAIL), recall 1/1, additions wind / solar
/ gas_cc / gas_ct / storage 1.902 / 1.782 / 2.0 / 0.5 / 0.000, LOYO folds
identical — every number equal to L2's to the decimal. The task's
"requirement UP ⇒ capacity revenue UP ⇒ exits HARDER" sign is the CURVE-ON
consequence and is tested only in P5. Falsifier: any FC-3 row moving in the
A/B means a requirement-consuming channel other than the position, floor and
backstop exists (route it, do not absorb it). HIGH.

**P4 — the rule-22 LOYO on a zero-parameter mechanism is a sign test** (the
D40/D48 construction): per-year |position − published| OFF → ON on the seam
positions, folds over 2023–2025. Expected **9.4 → 2.5 / 5.2 → 1.8 / 7.3 → 0.6
pts — every fold improves, 3/3 PASS**; the training pair arms in every fold and
the held-out year improves in every fold. The capacity-revenue leg (curve at
the position vs the real spot): OFF $7.2 / $6.0 / $33.0 → ON **$63.3 / $48.0 /
$28.7** vs real $49.3 / $41.6 / $51.4 — 2023 and 2024 move from a $0-class
reading to within +28 % / +15 % of the market; **2025 stays at half the real
spot in BOTH arms** (the 2025/26 curve vintage's net-CONE reset to $50.55, and
a published 2025 position D45 §8 flagged as a possible SOM transcription
carry-over) — a curve/records object, not this lever's. MED.

**P5 — the conditional probe (`--capacity-market-clearing` + BOTH), if P2
holds.** Read off the L3 ledger's own failed rows re-tested at the BOTH
positions (D45 §3(a) counterfactual; instrument stdout committed):
- **2023 screen: NO economic exit.** At 1.0175 the 2023/24 curve pays
  **$63.3/kW-yr**; the gas_st cohort's capacity leg is `0.93 × 63.3 = $58.9`
  against a $35.0 bar with ≈ $0.1 of energy margin — all 21 decided rows
  (3,496 MW) and all 27 admission-capped rows (5,871 MW) PASS, as do the
  capped gas_cc (7,338 MW: $60 + $10.7 vs $30) and gas_ct (3,075 MW: $59.5 +
  $1.1 vs $21). L3's 3.5 GW downstate-steam wave does not form.
- **2024 screen: no economic exit** (1.040 → $48.0; gas_st leg $44.7 > $35).
- **2025 screen: a gas_st failure is PREDICTED.** At 1.052 the 2025/26 vintage
  pays **$28.7**; the gas_st leg `0.93 × 28.7 = $26.6` + $0.4 of energy margin
  is $8 SHORT of the $35 bar, so gas_st fails, is decided with `decided_year
  2024` and executes in **2025** (1-yr lag — IN the scored window), sized by
  the 2025 admission budget ≈ 1,770 MW firm ≈ **1.8–1.9 GW nameplate**.
  Central: `retire.total_gw` ≈ **3.3 GW (+90 %)**, gas_st ≈ 1.9 GW in 2025,
  `false_retire` ≈ 0.55–0.60, recall 1/1. It would NOT fire if the 2025
  entering position lands ≤ 1.032 (curve ≥ $37.2): that needs ≥ 690 MW less
  entering firm than L2's 2025 fleet, which the probe's reduced 2024 gas
  entry cannot supply (the 2024-landed 1,000 MW gas_cc was decided in the
  2022 bridge in BOTH L2 and L3). Falsifier stated.
- **Entry:** the capacity term falls from $104.5k to ≈ $60k / $45.6k / $27k
  per MW-yr (2023 / 2024 / 2025); expect gas entry BELOW L2 (gas_cc 2.0 → ≤ 1.0,
  gas_ct 0.5 → 0–0.5 GW), storage exactly 0.000 (the D37-class shut channel).
- **P9 (a)/(b)/(c) verbatim, predicted:** (a) `retire.total_gw` within ±10 % —
  **NO** (+90 % central; even without the 2025 wave it inherits L2's −14.9 %
  target move); (b) `false_retire` in band — **NO**; (c) entering positions
  within ±3 pts every scored year — **YES** (1.0175 / 1.040 / 1.052). **One of
  three ⇒ the curve-ON recommendation stays DO NOT ARM**, but for a DIFFERENT
  and pre-stated reason than D45's: the position artifact is closed (c), and
  what remains is (i) the 2025/26 curve vintage paying half the real spot at
  the published position and (ii) the NYCA-wide representation paying
  downstate steam the NYCA price where Zone J clears at 3–4× (§5.2.4 item 3,
  NOT built here). The curve-attributable delta (probe − A/B) is reported
  beside the verbatim grade. MED.

**P6 — ledger observability (new, additive, cache-key-neutral):** the runner
gains `screen_peak_demand_mw`, `screen_adequacy_requirement_mw`,
`screen_entering_firm_mw` and `screen_reserve_position` — the seam peak, the
requirement the three screens consumed, the entering accredited firm and their
ratio, written whether or not the clearing gate is on. Predicted in the arm:
seam peak **28,640 / 28,990 / 29,343** (±30 MW), screen requirement = P1,
entering firm **35,163 / 34,745 / 35,829** (±60 MW), position = P2. The same
fields in an OFF replay would read requirement 30,922 / 31,300 / 31,682 and
position 1.137 / 1.110 / 1.131 (§1) — recorded as the prediction for whoever
replays the control. HIGH on the peak, MED on the firm.

**P7 — byte-inertness and keys:** both fields registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at `"False"`; the bare `nyiso-t1h` recipe key at
this branch's HEAD is measured after the build (§7) — if it still reads
`91686abe7a744a88` the D45-R L2 IS the control and no control solve is run; if
HEAD has moved it, the control is replayed at HEAD first (D48 §0 Phase-0 rule)
and the A/B is like-for-like at one HEAD. The pinned global default key is
unmoved. Other ISOs inert with the flags armed (test). HIGH.

**P8 — wall / memory:** ~12 min / ~3.5 GB per NYISO T1-H leg (D45-R measured);
the A/B and the probe run SEQUENTIALLY by design (the probe is conditional on
the A/B's positions), years sequential inside each (rule 12).

## 3. FC rows expected to move, and which way

| row | A/B (curve OFF) | probe (curve ON), if run |
|---|---|---|
| ledger `adequacy_requirement_mw` | +1.9 … +2.2 GW (2021–2024), −0.3 GW (2025) | same |
| new `screen_adequacy_requirement_mw` | +3.6 / +2.1 / +2.4 GW vs the seam OFF values | same |
| new `screen_reserve_position` | 1.137 / 1.110 / 1.131 → 1.0175 / 1.040 / 1.052 | same entering 2023; then per P5 |
| FC-3 `retire.*`, `false_retire`, recall, `add.by_tech` | **byte-identical** to L2 | gas_st 0 → ≈ 1.9 GW (2025); total 1.457 → ≈ 3.3; gas entry DOWN |
| capacity term seen by the screens | 104,500 $/MW-yr, unchanged | $0 → ≈ $60k (2023), $68.6k → $45.6k (2024), $38.6k → $27k (2025) |
| backstop | 0 MW | 0 MW (2025 post-wave firm ≈ 34,590 vs 34,059 — +0.5 GW; a fire here would be the falsifier of the budget arithmetic) |
| determination (`forecast_verdict --tier t1h`) | HOLD, unchanged (FC-7 as the bare key) | HOLD |

## 4. Registration plan (rule 15) and matrix duties (rule 28)

A/B → `nyiso-2021-2025-realized-t1h-d52-devintage`, `VERDICT_MAP` key
**`nyiso-t1h-d52-devintage`**; probe (if run) →
`nyiso-2021-2025-realized-t1h-d52-curveon`, key **`nyiso-t1h-d52-curveon`**.
Neither takes the bare key. Slim committed set per the D45-R / D48 template
(`meta.json`, `run_config.json`, `forecast_verdict.json`, the five
`evolution_<year>.json`, `score.json`, the two `screen_signal_diag_*.npz`).
Matrix: two base rows + a cell in all six shards in the same PR; the NYISO
cells re-stamped with the measured verdict after the solve.

## 5. Sign discipline and what would make this lane STOP

- Nothing is sized by a residual: the identification is Table D.2, full stop.
- STOP conditions: a realized key ≠ its §7 pre-declared value; any FC-3 row
  moving in the A/B (P3's falsifier); a backstop build in the A/B; a
  backcast-namespace key moving (the fields are coerced to default in a plain
  backcast and dropped from the hash at their default — measured, not assumed).

## 6. The re-open condition, verbatim (D45 §6)

> "the curve question re-opens only after the position lands within the
> ±3-point condition it was written to test."

**The curve-ON probe re-runs ONLY if the repaired L2 positions sit within ±3
points of the published NYCA positions in every scored year.** Evaluated on the
A/B's `screen_reserve_position` (2023 / 2024 / 2025) against 1.043 / 1.058 /
1.058. If any year fails, the probe is NOT run, the failing year and its gap
are stated, and the lane routes to §5.2.4 item 3 (the locality half), which
this lane does NOT build.

## 7. Cache keys — appended after the build, before any solve

*(filled in §7 of this file by the same lane once the fields exist; nothing
below this line was written before the code.)*
