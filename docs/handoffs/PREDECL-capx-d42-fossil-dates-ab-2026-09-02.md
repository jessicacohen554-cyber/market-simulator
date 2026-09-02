# PRE-DECLARATION — capx D42: the fossil announced-date posture A/B (D32 R1)

**Pushed BEFORE the arm legs solve.** Graded at full magnitude, misses
included, in `FINDING-capx-d42-fossil-dates-ab-2026-09-02.md` §6.

**Lane:** capx D42 — owner ruling Q29 on D32's R1
(`FINDING-capx-d32-floor-retention-2026-09-02.md` §7): MEASURE the posture in
which a fossil unit's owner-filed EIA-860 Schedule-3 planned retirement date is
honored as an exogenous step-1 input, against the shipped posture that no-ops
it (`forecast_fossil_retirement_economic=True`). **Nothing arms.** The gate
(`ScenarioConfig.fossil_announced_exits_enabled`) ships DEFAULT-OFF, both legs
register SUFFIXED, the bare `miso-t1h` verdict key is untouched, and the
decision line of the finding reads: THE OWNER ARMS OR DECLINES; this lane did
neither.

**Rule 14 / rule 21 sign discipline (binding).** Nothing below was sized,
tuned or sequenced by what it does to the exit residual. The channel has
**zero free parameters**: its content is the vintage's own filed dates, its
reconciliation with the screen and the floor is a design (§2), and the
deferral class is countered ONLY by a published per-unit re-filing (the later
EIA-860 vintage's Schedule 3) or a registry counter-instrument — never a fitted
filter. Where no instrument exists the false positive stands at full magnitude.
The pre-declared magnitudes in §3 are D32's, restated verbatim, plus the
loader's own data census (§1) — data, not solve output.

---

## 0. What is being measured

`ScenarioConfig.fossil_announced_exits_enabled=True` (arm) vs `False` (control,
the shipped posture replayed at HEAD). Armed, the run reads every OPERABLE
fossil unit's planned retirement year/month from the run's ACTIVE EIA-860
vintage (vintage 2020 here — the rule-13 vintage gate: a date is admissible in
year Y only because it was on file at the cutoff, the same information gate
step 0 applies to `instrument_date`; the identical construction regenerates
for a forecast year from the then-current 860) and applies the rows at step 1
of the capacity evolution through step 0's own matcher/derate machinery
(`apply_confirmed_exits`: a unit-grain row drops the unit, a plant-binned row
derates the plant's tranches, first-half months carry a completion leg; the
first simulated year takes the pre-start backlog in `build_base_fleet`).

Under the harness-default **verified posture** (`hindcast_verified_announced_
exits`, the 2026-08-22 ex-ante-purity-vs-verified-fleet trade, already recorded
per leg) the vintage set is checked per unit against the later in-repo vintages
(2021–2024 + the canonical 2025 snapshot): a re-filed LATER date is a filed
deferral and is honored as the later vintage's information; a dropped date is
a withdrawn plan (a sale with continued operation); an absent unit exited and
its vintage date stands; a re-filed EARLIER date is recorded but the vintage
date stands (the posture may defer or cancel a vintage exit, **never inject or
advance one**); a reversal-registry plant (J H Campbell under DOE §202(c)) is
dropped. Every disposition is persisted on the first ledger year
(`announced_fossil_schedule`) so the ex-ante and verified sets are reported
side by side.

## 1. The data census (loader output on the committed vintage_2020, no solve)

MISO, BA = MISO, status OP, fossil by `_map_fuel_type`, dated rows with
`Planned Retirement Year ≤ 2025` (nameplate MW, GW):

| set | rows | coal | gas_st | gas_ct | oil | gas_cc | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ex-ante** (2020-vintage dates as filed) | 83 | 18.451 | 2.355 | 0.577 | 0.443 | 0.022 | **21.849** |
| **verified** (later-vintage re-filings honored; never advanced) | 57 | 10.756 | 1.059 | 0.194 | 0.285 | 0.022 | **12.317** |

Dispositions of the 112 dated fossil rows (all years): deferred 57, exited 22,
advanced 22 (date stands), cancelled 10, kept 1. **The deferral class D32 named
is countered, per unit, by a published re-filing:** Baldwin 1–2 (889) → 2027,
Coal Creek 1–2 (6030) withdrawn (sold to Rainbow Energy), Merom 1–2 (6213)
withdrawn (sold to Hallador), Columbia 1–2 (8023) → 2029, Schahfer 17/18
(6085) → 2026, Edgewater 5 (4050) withdrawn, R D Green 1–2 (6639) withdrawn,
Lake Catherine 4 (170) → 2027, Sherburne 1 (6090) → 2026, J H Campbell 1–3
(1710) → 2026 (and reversed by the registry). The ex-ante − verified gap,
**9.53 GW**, is the false-positive class an ex-ante 2020 forecast would have
carried at full magnitude; the finding reports it at that magnitude and
grades, per plant, whether the re-filing was KNOWABLE before the vintage
date's effective year (`first_change_vintage` < effective year — the
rolling-vintage counterfactual).

## 2. The rule-19 reconciliation (design, stated before the solve)

Two mechanisms would otherwise decide a fossil unit's exit (the filed date and
the screen). The reconciliation — implemented WITH the gate, tested in
`tests/unit/model/test_capacity.py::TestFossilAnnouncedExits`:

* **(a) The screen runs on the RESIDUAL fleet.** A plant carrying a pending
  admissible date is EXOGENOUS to the economic screen (`exempt_unit_ids` via
  `dated_plant_unit_ids`): unit-grain generators by their own generator ID,
  plant-binned generators by the plant. The owner's filed plan IS the exit
  decision for that plant; the screen decides only undated plants, and no
  unit's exit is decided twice. When the last row of a plant has completed,
  its survivors re-enter the screen as an undated residual plant. (Contrast
  the confirmed-exit precedent, where the screen may pre-empt a LEGAL
  latest-exit ceiling: an owner's own filed plan is not a ceiling on the
  owner's decision, it is the decision.)
* **(b) The floor's retention pool sees the dated units as exogenous.** The
  R-NEW admission cap's counterfactual fleet nets every dated exit due by the
  cap horizon (`apply_confirmed_exits` applied year by year to `cap_year`), so
  the floor can neither retain a dated unit (never in `eligible`) nor
  over-admit undated candidates against capacity that is leaving anyway.
  The realized-year execution floor tests the post-step-1 fleet, unchanged.
* **(c) The ledger never double-counts.** A dated exit is recorded once,
  as `announced` (unit drop) or `announced_derates` (binned derate); a unit
  dropped at step 1 is pruned from the pipeline state (existing behaviour), so
  no `executed` row can follow it.

Open item declared, not closed: the admission counterfactual nets DATED rows
only, not the confirmed registry's future rows (a pre-existing gap of the cap,
negligible in MISO's window).

## 3. Pre-declared outcomes (graded in the finding §6)

The three legs, run **sequentially** on this 15 GB box (a MISO year ≈ 8 GB;
rule 12's ~2-concurrent cap is a memory ceiling here), every year sequential
within a leg:

```
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized --out-dir results/hindcast/miso-2021-2025-realized-t1h-d42-control
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized --fossil-announced-exits \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d42-dates
uv run python scripts/run_capacity_hindcast.py --iso MISO --start-year 2021 --end-year 2025 \
  --vintage 2020 --fuel-variant realized --fossil-announced-exits --no-verified-announced-exits \
  --out-dir results/hindcast/miso-2021-2025-realized-t1h-d42-dates-exante
```

**P0 — control = D33 replayed, value-identical.** `retire.total_gw` 4.469
(−74.3 %), coal 3.684, recall 5/19, the 23-tranche 2022 coal release. The
cache key will NOT equal D33's `40173304213d39cd`: the default `ScenarioConfig`
key at HEAD is `cedadc285f8603b9` (moved by merges since D33's `603c2498bf71d21d`,
none of them MISO-solve-affecting) — declared so a key mismatch is not read as
a behaviour change. The new field is cache-neutral off (registration guard +
pin tests pass).

**P1 — the channel opens the non-coal composition (D32 R1, verbatim).** Exits
carried by the channel: coal +9.7 GW, gas_st +1.1, oil +0.3, gas_ct +0.2 (the
loader's verified census reads coal 10.76 / gas_st 1.06 / gas_ct 0.19 / oil
0.29 through 2025 — the December-dated rows fall to 2026 under the
majority-of-year rule, so the in-window MW is bounded by these). Every fuel
that reads exactly 0.0 in the control (gas_st, oil, gas_ct, gas_cc) reads > 0
in the arm.

**P2 — recall 5/19 → ≥ 13/19** (D32 R1). Of the 19 reachable ≥300 MW target
units, 15 carry a 2020-vintage date (Palisades via the non-fossil channel
already); the four that do not (Rush Island 1–2, Big Cajun 2, Teche) stay
missed unless the residual screen reaches them.

**P3 — `retire.total_gw` under-retirement shrinks; direction only.** Arm
total ≈ the verified channel (≤ 12.3 GW) plus the residual economic release,
which the netted admission cap should REDUCE below the control's 3.684 GW
(the floor now sees ~12 GW of scheduled exogenous exits in its counterfactual).
Declared range for the verified arm: `err_frac` in **[−35 %, +5 %]** vs
actual 17.369 GW (band ±10 % — a PASS is NOT predicted). The ex-ante arm
over-retires: **[+10 %, +30 %]**.

**P4 — false positives.** Verified arm: `false_retire` (per-fuel EXCESS grain)
stays PASS (every fuel's channel MW < actual). Plant-grain false positives are
reported at full magnitude from the ledger: the dated plants that did not
exit 2021–2025 (the residue the re-filings did not counter). Ex-ante arm: the
9.53 GW deferral/sale class lands — coal per-fuel excess ≈ 6 GW → `false_retire`
FAIL. Both are reported; neither is fitted away.

**P5 — the economic screen's own release falls.** `pipeline_events`
`decided`/`executed` MW in the arm ≤ the control's 3,684 MW (23 coal tranches);
the released set is a subset of undated plants (White Bluff / Independence /
Michigan City class), never a dated plant.

**P6 — T-R10 a/b PASS in every leg** (economic channel only; the channel's
rows are `announced`, never first-mover economic exits).

**P7 — LOYO (rule 22):** recall-PASS (≥ 0.70) holds in ≥ 2 of 3 folds for the
verified arm; the control holds in 0 of 3.

**P8 — additions: direction unknown, declared not predicted.** Exogenous exits
tighten the stack, so the entry screen may build more; the D33 solar ceiling
(the growth ladder) is untouched by this lane.

**P9 — verdict rows.** FC-3 stays FAIL on the additions half in every leg
(P8's ceiling); the retirement rows are the object. Determination HOLD on
every leg. No `miso-t1h` edit; two (three) suffixed verdict keys added.

## 4. Registration plan (declared now so the artifact trail is fixed)

* Bundles under `results/hindcast/miso-2021-2025-realized-t1h-d42-{control,dates,dates-exante}` —
  slim set + evolution ledgers (the D27/D31/D33 `.gitignore` carve-out precedent).
* Sidecars via `scripts/register_forecast_run.py --bundle <dir>` (the single
  registration path); `VERDICT_MAP` gains the suffixed keys
  `miso-t1h-d42-control`, `miso-t1h-d42-dates`, `miso-t1h-d42-dates-exante`;
  `ff-verdicts.json` gains those keys and **nothing else** — `miso-t1h` is not
  taken. `program-status.json` untouched.
* Matrix (rule 28): base row `fossil_announced_exits` + a cell in all six
  shards in the mechanism commit (MISO `O` with the evidence; the other five
  `U`).
* Scoring: `score_capacity_hindcast.py` reads the new `announced_derates`
  ledger rows (the announced-channel twin of `confirmed_derates`) and treats
  the D-24 economic-evidence exclusion as not applicable when the gate is on
  (the announced route is live for fossil) — fail-closed, same as the
  `forecast_fossil_retirement_economic=False` posture already is.
