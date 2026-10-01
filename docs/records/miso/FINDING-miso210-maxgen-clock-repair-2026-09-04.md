# FINDING miso-210 — THE MAX-GEN CLOCK REPAIR: both armed keeper mechanisms fired one hour late on the model clock; repaired as structure (one constant, mirrored in the deriver, plus the extract it regenerates), adjudicated as a single-delta A/B against a bit-identical control (2026-09-04)

**PREREG `PREREG-miso210-maxgen-clock-repair-2026-09-04.md` pushed blind at
`83e73bf8` with the scorer `_miso210_ab_gates.py`, before any window was
re-placed.** Phase-0 record `_miso210_clock_phase0.json` (`7812291a`);
instrument `scripts/probes/_miso210_clock_phase0.py`. Keeper at open
`2026-09-03-miso-202-unitclip`. Rule 22: 2023–2025 only. Two LPs spent:
control `miso210_control_A`, arm `miso210_clock_B`.

**PROMOTED: MISO keeper → `2026-09-04-miso-210-clock` (bundle
`miso210_clock_B`), ALL TEN A/B GATES PASSING** (S-0 bit-identical, S-1
zero-field delta with commit + extract identity, S-2 exact one-hour shift,
S-3 certificate invariance, K-1..K-6 silent, K-6 REAL). Determination
UNCHANGED at NOT-YET on {C3a-2025 −12.3845} alone, C3c the single ledgered
caveat, C6 attested (ledger 41/2, no new entry). The arm moved exactly one
scored value — C3a-2024 −4.613 → −4.396 (+0.217 pp) — through the
pre-registered channel's OPPOSITE edge (§3), and that move is reported, not
argued from. Scorer `_miso210_ab_gates.py` (`83e73bf8`, blind); record
`_miso210_ab_gates.json`.

---

## 0. Two things found before the repair, neither pre-registered

1. **The M-2 deriver could not run at HEAD at all.** The registry's 2021/2022
   rows (rule-22 intake, 2026-07-31) made `main()` load a DA hub record per
   registry year, and `miso_hub_lmp_2021_da.csv.gz` does not exist (2022 is
   staged as unreadable `_p<NN>.csv` chunks). The committed `-unitroute-`
   extract was never forward-derived: miso-200 built it by RELABELLING the
   2026-07-16 incumbent (`_miso200_relabel_extract.py --maxgen`). Repaired
   in the same commit as the clock: registry years with no DA hub record are
   dropped with a printed notice (uncertifiable; outside the training span).
2. **The forward deriver at the OLD clock reproduces the committed extract to
   one row** (N-1, not in the PREREG but required before any delta could be
   called "the clock"): 2,173 of 2,174 solve-relevant rows identical, total
   41,873 vs 41,874 MW; the missing row is New Ulm (2001) unit 7, ST_CHP,
   **1 MW** on the Jul-24-2025 block (its `(plant, group)` bin is no longer in
   the fleet's capacity map). `plant_capacity_mw` (informational, unread by
   the loader) differs on 16 rows. So the corrected re-derive carries the
   clock and one 1-MW row of fleet drift, and nothing else.

## 1. Phase 0 — measured against the PREREG

### P-1 — the exact hour sets (PREREG §3 table confirmed arithmetically; `exact_one_hour_shift` TRUE on all 9 registry rows in every year)

| block | gained hour (CST) | keeper price / actual / slack / idle thermal | lost hour (CST) | keeper price / actual / slack / idle thermal |
|---|---|---|---|---|
| 2023 Aug 24 step-2 ($1,000) | Aug 24 h11 | $44.9 / $42.5 / 0 / 11.5 GW | Aug 24 h23 | $36.1 / $26.4 / 0 / 19.0 GW |
| 2024 Aug 26 warning ($500) | Aug 26 h12 | **$62.1** / $143.4 / 0 / **4.1 GW** | Aug 26 h19 | $66.2 / $39.1 / **0** / 1.05 GW |
| 2025 Jun 23 step-1 (midwest) | Jun 22 h23 | $37.0 / $35.9 / 0 / 24.9 | Jun 23 h23 | $48.3 / $71.4 / 0 / 17.3 |
| 2025 Jun 24 warning (midwest) | Jun 23 h23 | $48.3 / $71.4 / 0 / 17.3 | Jun 24 h23 | $42.7 / $52.8 / 0 / 20.8 |
| 2025 Jul 24 advisory (M-2 only) | Jul 23 h23 | $37.3 / $28.3 / 0 / 24.0 | Jul 24 h23 | $44.8 / $38.0 / 0 / 12.2 |
| 2025 Jul 28 advisory (M-2 block start) | Jul 28 h11 | $50.8 / $98.3 / 0 / 11.0 | Jul 29 h22 | $47.7 / $41.7 / 0 / 10.8 |
| 2025 Jul 29 warning ($500) | Jul 28 h23 | $42.8 / $43.0 / 0 / 16.5 | Jul 29 h23 | $40.6 / $52.4 / 0 / 19.1 |

* **P-1a RIGHT** (2023: gained price > lost, idle lower, slack 0 in both).
* **P-1b RIGHT on its line and WRONG on its mechanism.** The 2024 window's
  19,384 MWh of $500 slack sits in h13–h18 CST (2,045 / 3,231 / 3,705 / 4,656 /
  4,420 / 1,327 MWh); **the lost hour h19 carries 0.0 MWh** (predicted ≤ 25 %).
  So the PREREG's named 2024 channel — slack in the lost hour re-priced from
  $500 — **does not exist**. The gained hour h12 is priced $62 in the keeper
  with 4.1 GW of idle thermal; on the corrected clock it takes the 10.2 GW
  M-2 derate AND becomes tier-eligible, which is where any 2024 price move
  must come from (the A/B decides, §3).
* **P-1c RIGHT**: every 2025 gained/lost hour is a 23:00 night hour with
  slack 0 and idle > 12 GW; the one daytime edge (Jul 28 h11, M-2 only) has
  11.0 GW idle against a 7.4 GW block derate.

### P-2 — the extract re-derived on the corrected clock (scratchpad; then reproduced under `data/raw` by the repaired script, §2)

| block (corrected CST) | rows 2,174 → | derate MW → | Δ |
|---|---:|---:|---:|
| 2023-08-24 11:00–23:00 | 474 → 473 | 10,171 → 10,120 | −0.5 % |
| 2024-08-26 12:00–19:00 | 467 → 466 | 10,311 → 10,187 | −1.2 % |
| 2025-06-22 23:00–06-24 23:00 (midwest) | 295 → 295 | 3,066 → 3,067 | +0.03 % |
| 2025-07-23 23:00–07-24 23:00 | 484 → 483 | 10,902 → 10,872 | −0.3 % |
| 2025-07-28 11:00–07-29 23:00 | 454 → 454 | 7,424 → 7,431 | +0.1 % |
| **total** | **2,174 → 2,171** | **41,874 → 41,677** | **−0.47 %** |

**P-2a RIGHT (S-3 PASS): guard 2's `n_cert` is identical on every registry
row on the two clocks** (0 / 5 / 2 / 8 / 9 / 6 / 16 / 7 / 8), the same 8
rows qualify, the same 5 blocks form. **P-2b RIGHT** (every block within
±1.2 % MW, ±0.3 % rows). **P-2c RIGHT** (F3 silent on all five blocks;
guard 4 asserts clean).

### P-3 — static reach, and miso-208's claim re-scored on the corrected clock

**Holds.** Over the corrected 2025 Warning+ hours (72 h) the keeper's min
idle thermal is **2.178 GW** — identical to the armed placement, because the
correction swaps one 23:00 for another in each block — with slack 0 and max
price $141.7. The tier floor stays statically unreachable in 2025 (P-3
RIGHT, 0.85). *(The probe's `demand_minus_capability` column is a whole-
fleet-minus-imports quantity that reads positive in every year including
hours with zero slack; it is not the reach metric and is not used.)*

### Placement verification (V-KEY-LMP)

INDIANA.HUB RT from the HE (EST) file placed at EST_TO_MODEL = −1 vs the
committed zonal `rt`: **r = 1.000, max |Δ| 0.00 in 2023 and 2025**; 2024
r = 0.9996 with 23 differing hours, ALL on Jan 1 and the Feb 28/29 leap
boundary (the committed series' leap-day handling) and **0.00 on Aug 26**.
The key holds on every window day, so the corrected window set is exactly
the model hours whose EST labels lie inside the declared window.

### S-2 — placement liveness off the production functions

`tier_slack_cost_from_registry` on the two registries: the corrected cost
array equals the armed array shifted by exactly −1 h in every year
(12 / 12 / 22 differing zone-hour cells; 72 / 42 / 384 below-VOLL cells on
both; external buses untouched). `unit_outage_maxgen_derate_factors` on
the committed vs re-derived extract: the union derate hour set shifts by
exactly −1 h in every year (12 / 7 / 108 hours), 196 / 195 / 195 of 196
bins shift exactly per bin (the remainder are the 1-MW row and the
best-hour-credit rows the re-derive added/dropped).

## 2. The repair (P-4 — what it is and is not)

Landed at `a9b67b53` (PR #4719), exactly as pre-registered in §2 of the
PREREG, plus the one un-pre-registered fix §0.1 forced:

* `src/market_sim/data/maxgen_events.py`: `MODEL_TZ_BY_ISO["MISO"]`
  `"Etc/GMT+5"` → **`"Etc/GMT+6"`**; the conversion factored into a pure
  `registry_to_model_clock(ev, iso)` so the placement is unit-testable.
* `scripts/data/derive_campd_maxgen_outages.py`: reads the SHARED loader and
  constant (`MODEL_TZ = MODEL_TZ_BY_ISO["MISO"]`, `load_registry_model_clock`
  → `load_maxgen_registry_model_clock`) so the two consumers can never
  drift apart again; `DA_HUB_EST_TO_MODEL_HOURS = −1` applied in a pure
  `da_hub_long_to_wide`; registry years with no DA hub record dropped with
  notice (§0.1); columns `start_est`/`end_est_excl` → `start_model`/
  `end_model_excl`.
* `tests/unit/data/test_maxgen_model_clock.py` (7 tests): the CST constant,
  the deriver sharing it, 13:00–20:00 EST → model 12..18, the day-precision
  ceil, the DA-hub shift, and certificate invariance to the shift. 45
  maxgen-family tests pass.
* Both MISO M-2 extracts re-derived by the production script; the
  `-unitroute-` file is **byte-identical** to the phase-0 scratchpad
  prediction (sha `de7e4f77…`), which is what S-1 checks.
* The registry, its README, schema and curation parser: **unchanged**.
  `docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md` §1 annotated;
  `_miso208_find_the_supply.py` annotated (its `window_masks` would
  double-shift on a re-run).

**No `ScenarioConfig` field, no mechanism, no matrix row, no ledger entry.**
The repair changes WHERE two armed mechanisms fire, not what they do; the
constant is a measured property of the model's own hour index and could not
have been chosen differently once measured.

## 3. The A/B

Control `2026-09-04-miso-210-control` (bundle `miso210_control_A`, HEAD
`7812291a` = the keeper's code state, old constant, committed extract) vs
arm `2026-09-04-miso-210-clock` (bundle `miso210_clock_B`, `a9b67b53`),
both the miso-202 keeper recipe via `--replay-bundle`, MISO 2023+2024+2025
in one invocation each, years sequential, in-session, control first and the
arm only after the control had finished (its per-year extract reads must
never see the re-derived file).

| gate | result |
|---|---|
| **S-0** control integrity | **PASS — BIT-IDENTICAL**, 9 sidecars, `max_abs_diff` 0.0; D1/D2/D4 diagnostics byte-identical to the keeper's |
| **S-1** single delta (restated) | **PASS** — 783 config fields, zero diffs; legs at `7812291a` / `a9b67b53`; arm extract sha = phase-0 prediction |
| **S-2** placement liveness | **PASS** — tier cost and M-2 hour set shift by exactly −1 h, every year |
| **S-3** certificate invariance | **PASS** — `n_cert` identical on all 9 rows |
| **K-1** C1 band ±8.00 | **PASS** — no band exit; largest class-year move **0.002 TWh** (CC_REGULAR-2024 +6.942 → +6.940; ST_GAS-2024 −7.487 → −7.486; ST_GAS-2025 −6.684 → −6.686) |
| **K-2** C3b | PASS — 0.081 / 0.109 / 0.182 → 0.081 / 0.111 / 0.182 |
| **K-3** D-4 | PASS — 57 rows both legs, zero new, zero cleared |
| **K-4** D-1 | PASS — ST_GAS profile_r / cv_ratio identical |
| **K-5** status flips | PASS — status map IDENTICAL |
| **K-6** DOF | **PASS, REAL** — 41 entries / 2 residual on both legs, no new entry |

**C3a, at full magnitude, never the justification:**

| year | control | arm | Δ pp | PREREG band | inside |
|---|---:|---:|---:|---|---|
| 2023 | +0.1218 | +0.1218 | **0.000** | [−0.05, +0.10] | yes |
| 2024 | −4.6130 | **−4.3963** | **+0.217** | [0, +1.5] | yes |
| 2025 | −12.3845 | −12.3845 | **0.000** | [−0.05, +0.10] | yes |

**Where the 2024 move comes from — the PREREG's mechanism was WRONG, its
sign was right.** The PREREG named the LOST hour (19:00 CST) — "$500 slack
re-priced to the supply above $500 or VOLL". Phase 0 measured that hour at
**0.0 MWh** of the window's 19,384 MWh (§1, P-1b). The move is the GAINED
hour: 12:00 CST Aug 26 2024, the Warning's declared first hour, now takes the
10.2 GW M-2 derate AND the $500 floor, and prices at **$447.5 with 570 MWh
of slack** against the control's $62.1 and none; 19:00 CST falls $66.2 →
$49.2 as its misplaced derate is removed; the six middle hours are within
±$0.1. Window slack 19,384 → 19,567 MWh. That is the corrected mechanism
doing what the declared instrument says: the Warning's first hour was
scarce and the model now prices it as such. In 2023 the edges move 11:00 CST
Aug 24 $44.9 → $53.7 and 23:00 $36.1 → $33.7 (load-weighted annual mean
−0.0005 $/MWh); in 2025, 11:00 CST Jul 28 $50.8 → $58.5 (+0.0008 $/MWh);
the INDIANA.HUB comparator is unmoved in both years.

**C8** ST_GAS forced share 0.1553 / 0.1529 / 0.2714 → 0.1552 / 0.1529 /
0.2714 (|Δ| ≤ 0.00006 vs the 0.0005 epsilon).

**miso-208's claim, re-scored on the corrected clock: HOLDS.** The tier
floor is silent in every corrected 2025 Warning+ hour (72 h, slack 0, max
$141.7, min idle thermal 2.178 GW). The 2025 tail is untouched by every
edge, which is why C3a-2025 is unchanged to the decimal.

## 4. Verdict

**PROMOTE, on the PREREG's own rule (§4): structural repair, single delta,
all ten gates passing.** The keeper moves to `2026-09-04-miso-210-clock`;
the determination does not move (NOT-YET on {C3a-2025} alone, C3c ledgered,
C6 attested). The justification is §0–§2 — a mechanism firing in the wrong
hours is a rule-1 / rule-17 defect at any magnitude — and would be the same
had C3a-2024 moved the other way.

**Reported against the promotion.** (a) The arm is small: 0.002 TWh at most
on any C1 cell and one scored price move of +0.22 pp. (b) The 2024 move is
favourable AND comes from a channel the PREREG did not name — a right sign
for the wrong reason, which is disclosed rather than counted. (c) The arm
carries 1 MW of fleet drift (§0.2) with the clock. (d) The plant-local CAMPD
clock skew moves from the CST majority to the EST minority; a per-state
CAMPD placement would be a second delta and is named for the deriver's
cross-ISO owner, not built. (e) The 2025 object (shoulder −43.7 / tail
−636.9) is exactly as it was: the corrected windows contain the same tail
hours as the misplaced ones did, so this repair was never a C3a-2025 lever
and the lane's remaining named items — the RDT S→N binding state (4.8 % by
stranding), the deriver's plateau clause (director) — stand.

## 5. My prior, scored against interest

| # | prediction | conf. | measured | verdict |
|---|---|---:|---|---|
| P-1a | 2023 gained price > lost; idle lower; slack 0 | 0.8 | $44.9 > $36.1; 11.5 < 19.0 GW; 0 / 0 | RIGHT |
| P-1b | 2024 lost hour ≤ 25 % of window slack; gained hour < $500 | 0.65 / 0.7 | **0.0 %**; $62.1 | RIGHT — and the named channel is EMPTY |
| P-1c | 2025 edges: night hours, slack 0, idle > 5 GW | 0.9 | all 23:00 edges slack 0, idle 12–25 GW; Jul 28 h11 (M-2) 11.0 GW | RIGHT |
| P-2a | certificate identical, 5 blocks | 0.9 | identical on 9 rows, 8 qualify, 5 blocks | RIGHT |
| P-2b | rows ±3 %, MW ±5 % per block | 0.7 | ≤ 0.3 % / ≤ 1.2 % | RIGHT |
| P-2c | F3 silent; guard 4 clean | 0.8 | silent ×5; clean | RIGHT |
| P-3 | 2025 tier unreachable; min idle ≥ 2.0 GW | 0.85 | 2.178 GW, slack 0 | RIGHT (the miso-208 claim holds) |
| S-0 | bit-identical | 0.9 | 0.0 on 9 sidecars | RIGHT |
| K-1 | silent; max move ≤ 0.05 TWh | 0.95 / 0.9 | silent; 0.002 | RIGHT |
| K-2..K-5 | silent | 0.75–0.85 | silent | RIGHT |
| K-6 | real, 41 → 41 | — | 41 / 2 both legs | RIGHT |
| C3a-2023 | [−0.05, +0.10] | 0.7 | 0.000 | RIGHT |
| C3a-2024 | UP, [0, +1.5], via the LOST hour's slack | 0.65 | **+0.217, via the GAINED hour** | RIGHT on sign and band, **WRONG on mechanism** |
| C3a-2025 | [−0.05, +0.10] | 0.75 | 0.000 | RIGHT |
| C8 | \|Δ\| < 0.0005 | 0.85 | ≤ 0.00006 | RIGHT |
| verdict | KILLS SILENT + MOVED → promote | 0.65 | as stated | RIGHT |
| N-1 (not pre-registered) | — | forward deriver at the old clock reproduces to 1 row / 1 MW; deriver unrunnable at HEAD | found, disclosed |

Read honestly: the arithmetic was predictable and was predicted; the one
mechanism the PREREG committed to for the only year that could move (the
lost-hour slack) was wrong, and the measurement that showed it (0.0 MWh in
19:00 CST) was in phase 0 before the solve. Tenth consecutive MISO session
whose most useful output came from the part of the prior that was wrong —
this time the wrong part changes nothing about the verdict, because the
repair was never justified by the number.

## 6. Governance

Rule 15: BOTH runs registered (`2026-09-04-miso-210-control`,
`2026-09-04-miso-210-clock`; payloads over `git push`; retention pruned
`miso-190-ppexit` and `miso-191-bexit`), `legitimacy_diagnostics.json` and
`calibration_attestation.json` on both. Rule 28(b): `maxgen_emergency_tier_
pricing` and `unit_outage_short_windows` (the row carrying
`unit_outage_maxgen_events`) re-stamped K with this evidence in MISO's shard;
header keeper/gates stamps; §5.4 stamp. Rule 28(c): no field. Rule 25:
MISO's shard only. Rule 22: 2023–2025 only. Rule 23: the deriver re-ran
because ITS CLOCK was repaired, not because a residual moved; the commit
cites the miso-208 witnesses. Rule 27: `maxgen_events.py` (283 lines) and the
deriver (689 lines) edited locally with the Edit tool and blob-verified
after push (line count + sha256 equal). Rule 13: a measured clock. Rule 1:
justified as structure. `keepers/MISO.json` → `2026-09-04-miso-210-clock`,
`build_status.py --iso MISO`, `audit_keepers --iso MISO`.

**Records:** this file; `PREREG-miso210-maxgen-clock-repair-2026-09-04.md`
@ `83e73bf8`; `_miso210_clock_phase0.json` @ `7812291a`;
`_miso210_ab_gates.json`; `scripts/probes/_miso210_clock_phase0.py`,
`scripts/probes/_miso210_ab_gates.py`, `scripts/gen_miso210_attestation.py`;
repair commit `a9b67b53`.

Next shorthand: **miso-211**.
