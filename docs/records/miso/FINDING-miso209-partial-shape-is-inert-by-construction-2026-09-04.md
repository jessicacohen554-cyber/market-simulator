# FINDING miso-209 — the unit-grain partial-derate shape is INERT BY CONSTRUCTION: the production deriver detects MISO's coal plateaus and drops every one at the revealed-availability filter, because a partially-derated unit is a RUNNING unit; measured on a diagnostic extract with that filter off, the frozen form carries 0.27 GW of the shoulder's coal-side object — REFUSED; the coal-side object itself survives re-scoring (2026-09-04)

**Keeper unchanged: `2026-09-03-miso-202-unitclip`.** NO LP, NO KEEPER MOVE, NO
MECHANISM ARMED, NO FIELD, NO RUN REGISTERED, NO CELL VERDICT MOVED. PREREG
`PREREG-miso209-partial-derate-phase0-2026-09-04.md` pushed blind at `b7ed8e21`
BEFORE the extract was derived; record `_miso209_partial_derate_phase0.json`;
instrument `scripts/probes/_miso209_partial_derate_phase0.py`. Rule 22:
2023–2025 only.

---

## 1. W1 — the production extract is EMPTY, and the reason is structural

`scripts/data/derive_campd_unit_outages.py --partial-windows --iso MISO --years
2023 2024 2025` (defaults; sidecar `campd-partial-outages-MISO.meta.json`)
wrote **0 rows**. That is not "MISO has no coal plateaus": running the
deriver's OWN functions stage by stage on twelve coal units (Petersburg 994,
Alcoa/Warrick 6705, Campbell 1710, Baldwin 889, Merom 6213, Sherco 6090,
Milton Young 2823, Coyote 8222) for 2025:

| stage | result |
|---|---|
| coal identification (`primaryFuelInfo`) | coal, all 12 |
| capability (`unit_capacity_mw`, EIA-860 exact / digits / observed peak) | 167–939 MW |
| when-operable CF guard (≥ 0.55) | **PASS, all 12** (0.63–0.89) |
| frozen plateau detector (`_partial_plateau_windows`) | **17 plateaus**, factors 0.48–0.73, 5–31 days |
| revealed-availability filter (`outage_detect.filter_revealed_outages`) | **kept 0 of 17** |

The filter's first clause drops a span in which the unit RAN (cf ≥ 0.05) for
≥ 24 of its high-net-load hours; its second keeps a span only if the unit was
DOWN (cf < 0.05) through ≥ 24 high hours; its third keeps a full stop (span
CF < 0.02, ≥ 5 days). **A partial plateau is a unit running at 35–70 % of its
ceiling, so it runs through every high-load hour it spans**: in the trace
(record `w1_filter_trace_2025`) `ran_high == high_hours` in 14 of 17 plateaus
and within 6 hours in the other three; spans with ≥ 24 high hours die on
clause 1, the rest fail clauses 2 and 3. The partial window shape therefore
cannot emit a row through the production chain for ANY ISO whose EIA-930
net-load file exists (the filter is a no-op only when `high_load_mask`
returns `None`). This is the same-source explanation for the zeros recorded
at ERCOT (calibration-log ercot.md:1983), CAISO (caiso-136), NEISO
(neiso-69: "0 partial windows") and now MISO — each read as "the phenomenon
is absent"; NYISO's zero is genuine (no coal). PJM's committed
`campd-partial-outages-PJM.csv` (76 rows) predates or bypasses the clause:
re-derived through the current chain into the session scratchpad (`--partial-windows --iso PJM --years 2023 2024 2025`, defaults) it returns **0 rows** — the committed file is not reproducible at HEAD, which is the base-row's cross-ISO question for the director, not this lane's.

**Consequence, named not repaired (the deriver is shared by six ISOs, rule
25):** the revealed-availability test that is RIGHT for a full-stop detector
(a unit that ran through the tight hours was available) is the WRONG test
for a plateau detector, whose object is a unit that ran BELOW its ceiling
through the tight hours. The admissible repair is a plateau-specific clause
(kept iff the span's high-load hours show `cf < derate_factor × ref`, i.e.
the unit stayed capped through the tight hours) — a change to
`scripts/lib/outage_detect.py` / the deriver with its own cross-ISO A/B.

To measure W2–W6 as pre-registered, the extract was re-derived with the
deriver's own documented `--no-inmerit-filter` switch, written to the
session scratchpad (never under `data/raw`, never consumable by a solve):
**157 rows, all COAL, 56 units at 34 plants, 55 / 58 / 44 rows in
2023 / 2024 / 2025; `derate_factor` mean 0.546 (p25 0.49, p75 0.61);
duration mean 9.5 days (p50 7, max 48).** W1 predicted 80–300 rows, all
coal, ≥ 25 units, factor 0.35–0.60 — RIGHT on the diagnostic extract, and
the production extract's 0 is the pre-registered "inert by construction"
branch, on a different ground than NYISO's.

## 2. W2–W6 on the diagnostic extract, through the production accumulator

**N-2.** The production accumulator (`outages._unit_outage_factors_from_events`,
keeper flags: fleet-status scope, steam capacity basis, per-unit clip) was
applied to the diagnostic frame and every W2–W6 quantity reads ITS factors.
The probe's own unit-hour accumulation agrees with it on the AGGREGATE
(nominal shoulder-day removal 0.293 vs 0.290 GW) and disagrees per bin by up
to 0.17–0.39 of a bin — the accumulator's plant capacity is the fleet bin's
`pmax` (net summer, status-scoped) while the extract's `plant_capacity_mw` is
the CAMPD-matched nameplate sum; the pre-registered fallback (read the
loader) is what the numbers below are. 2025, mean over the population's
hours, GW:

| | SHOULDER (52 d) | TAIL (7 d) | other Jun–Jul daytime | p75–90 / p90–95 / p95–99 |
|---|---:|---:|---:|---|
| **W2 removed, effective** (× the bin's armed availability) | **0.265** (max 1.11) | 0.075 | 0.255 | 0.23 / 0.36 / 0.27 |
| W2 removed, nominal | 0.290 | 0.083 | | |
| active coal bins per hour | 1.28 | 0.73 | | |
| Central share | 61.5 % | 100 % | | |
| coal removed by the ARMED window layers (std + short + maxgen) | **8.25** | 9.05 | | |
| coal removed by the statistical layer (envelope minus windows) | **1.77** | 1.72 | | |
| model coal capability / nameplate | 32.78 / 42.79 | 32.02 | | |

**W2 lands at 0.27 GW against a bracket of [3.4, 7.05] — 8 % of the bracket
floor.** The frozen form (deep plateaus, ≥ 5 days, < 0.65 × ceiling) is two
orders of magnitude short of the object even with its filter disabled; it
never touches MISO-South. **W3:** plateau unit-hours inside the unit's own
armed windows 3.9 % (9.4 % in the shoulder hours) — disjoint enough; but the
statistical coal layer (1.77 GW) is **6.7× the partial layer**, so even in
bracket the form would have been a rule-19 stack on a statistical layer that
already removes more than it does. **W4:** lift $0.38 mean, **share 0.009**
shoulder / 0.002 tail. **W5:** 2023 / 2024 shoulder-day removal 0.168 /
0.103 GW (0.6× / 0.4× of 2025's) — small everywhere, not a 2025 object.
**W6:** 5 violation days on the 52 (Jun 23, Jun 24, Jul 24, Jul 28, Jul 29),
**0 layer-caused** — the five days where the keeper's OWN envelope already sits
below MISO's metered coal+gas output (miso-208 §2), unchanged by a 0.27 GW
layer.

**W2b — the shallow sub-ceiling running the deep form cannot see** (97 coal
boiler units, 75 qualifying at CF ≥ 0.55; Σ max(0, ref − daily max) × unit
capability, EXCLUDING days inside any armed window or plateau): **1.63 GW**
shoulder / 0.65 tail / 2.16 other daytime; raw (no exclusions) 9.0 GW — the
raw figure is the whole revealed non-delivery (full outages included) and is
already 8.25 GW carried by the windows. The shallow residual (1.63) is the
SAME size as the statistical coal layer (1.77): **in aggregate the armed
envelope's statistical component is right-sized for the shallow sub-ceiling
running on the shoulder days**, so a measured shallow-derate layer would be a
substitution for the statistical layer, not an addition — and would move the
envelope by ~0.1 GW net. The successor named at miso-208 §6 does not exist as
an additive object.

## 3. R-208 — miso-208's coal-side excess, re-scored as a claim

Predicted to survive at ≥ +2.0 GW net of the layer and of gross/net. Measured
on the shoulder days (2025), the model's coal capability minus the partial
layer is **32.51 GW** against:

| basis | measured coal | excess of model capability | excess of model DISPATCH |
|---|---:|---:|---:|
| EIA-930 `COL` | 28.60 | +3.92 | **+3.43** |
| CAMPD, net-ADJUSTED (15 plants measured net; 31 gross-only × 0.93) | 30.69 | **+1.83** | +1.34 |
| CAMPD gross | 33.23 | −0.72 | −1.21 |

**The claim survives on every net basis and FAILS its own ≥ +2.0 line on the
CAMPD-net basis (+1.83; +1.34 on dispatch).** The coal-side surplus is
+1.3 to +3.4 GW depending on whether MISO's coal output is read from EIA-930
or from CAMPD with a parasitic adjustment that 31 of 46 plants lack a measured
value for — the basis spread (2 GW) is as large as the low estimate. In the
tail the CAMPD-net basis reads −0.7 (the model's coal is BELOW measured) and
the 930 basis +1.75. The other-daytime hours read +1.2 to +3.1: the coal-side
surplus is a Jun–Jul LEVEL property of this keeper, not a shoulder-specific
one (miso-208 §1: chronic, all three years).

**Reach ceiling of the whole coal-side object (post-hoc, disclosed; record
`_miso209_coal_side_reach_ceiling.json`).** A UNIFORM removal of X GW re-priced
up the keeper's idle census (miso-208's engine), X = the coal-side excess on
each basis:

| X (GW) | basis | shoulder lift / share | tail lift / share |
|---:|---|---:|---:|
| 1.34 | dispatch vs CAMPD net-adjusted | $3.8 / **0.086** | $20 / 0.031 |
| 1.83 | capability vs CAMPD net-adjusted | $5.7 / **0.131** | $30 / 0.047 |
| 3.43 | dispatch vs EIA-930 | $15.0 / **0.343** | $83 / 0.131 |
| 4.94 | MOM record, feasibility-clipped | $26.2 / **0.599** | $139 / 0.218 |

Even if EVERY GW of the coal-side surplus were removed by a perfect measured
layer, the shoulder would move by 13 % (CAMPD-net basis) to 34 % (EIA-930
basis) of its gap and the tail by 5–13 %. The coal-side object is real and
bounded: it clears the 25 % line in the SHOULDER only on the 930 basis, and
never in the tail — so it fails the charter's both-populations licensing on
every basis, and the basis question (31 of 46 CAMPD coal plants carry no
measured parasitic factor) decides whether it is worth 13 % or 34 % of the
shoulder.

## 4. Verdict

**REFUSED at W2, as pre-registered (P9 RIGHT); nothing chartered; no solve.**
Three things are settled:

1. **The registered partial shape is inert by construction** (§1) — not
   "MISO has no plateaus" but "the deriver's revealed-availability filter
   deletes plateaus by definition". Its MISO cell stays with the row's K (the
   SHORT shape is what is armed); the partial shape's status is recorded as
   INERT-BY-CONSTRUCTION in the row's evidence, and the cross-ISO defect is
   named for the director (rule 25: no other ISO's cell is touched).
2. **Even with the filter off, the frozen form carries 0.27 GW of a 1.3–3.4 GW
   object** (0.9 % of the shoulder gap), and the shallow residual it cannot see
   (1.63 GW) is already the size of the statistical coal layer (1.77). The
   coal/steam availability lane has no additive measured form left: the
   windows carry 8.25 GW, the statistical layer 1.77, and MISO's metered coal
   output sits 1.3–3.4 GW below the model's dispatch on the shoulder days.
3. **The whole coal-side object's price reach is bounded** (a uniform removal of the coal-side excess re-priced up the keeper's own census lifts the shoulder by 13 % (5.7 $/MWh at 1.83 GW) to 34 % (3.43 GW) of its gap, the tail by 5–13 %):
   it clears the 25 % line in the shoulder only on the EIA-930 basis and never
   in the tail, so it fails the both-populations licensing on every basis. The
   shoulder's −$43.7 is at most a third closable from the coal side, and only
   if the 930 basis is the right one; miso-208's reading stands — same dispatch, different price,
   with the residual in conduct the hourly LP does not carry (commitment state,
   RT dynamics) or in the RDT wheel the LP does not bind (miso-208 §4).

**Successor, named not built:** none on the coal-availability side. What
remains open for the shoulder: (a) the max-gen clock repair
(`maxgen_events.MODEL_TZ_BY_ISO['MISO']`, one hour late; its own A/B); (b) the
RDT South→North binding state (50 % of shoulder hours) vs the LP's non-binding
2,500 MW link — a deliverability object bounded at 4.8 % by stranding; (c)
the deriver's plateau-specific revealed-availability clause (cross-ISO,
director's queue). None reaches 25 % of the shoulder on the numbers here.

## 5. My prior, scored against interest

| # | prediction | conf. | measured | verdict |
|---|---|---:|---|---|
| W1 | 80–300 rows, all coal, ≥ 25 units, factor 0.35–0.60 | 0.6 | production **0**; diagnostic 157, coal, 56 units, 0.55 | RIGHT on the diagnostic; the production 0 is the pre-registered inert branch on a NEW ground |
| W2 | 0.5–2.0 GW, below bracket; Central ≥ 50 % | 0.65 / 0.55 | **0.27**, below the low end too; Central 61.5 % | RIGHT (direction), magnitude over-predicted 2× |
| W2b | shallow gap 3–6 GW | 0.5 | **1.63** | **WRONG** — the object has no shallow-derate half of that size |
| W3 | overlap ≤ 10 %; statistical layer 4–7 GW > partial | 0.7 / 0.6 | 3.9 %; **1.77** > 0.27 | RIGHT / half (statistical smaller than predicted; windows carry 8.25) |
| W4 | share < 0.10 / < 0.02 | 0.7 | 0.009 / 0.002 | RIGHT |
| W5 | 2023/2024 within 0.5–1.5× | 0.6 | 0.63× / 0.39× | half (2024 below) |
| W6 | 0–2 violation days | 0.6 | 5 pre-existing, **0 layer-caused** | RIGHT on the layer's own account |
| R-208 | coal excess survives ≥ +2.0 GW net-adjusted | 0.6 | **+1.83** (capability), +1.34 (dispatch); +3.43 on 930 | **WRONG on its own line**: survives positive, smaller, basis-bound |
| P9 | refused at W2, nothing chartered | 0.7 | as stated | RIGHT |
| N-2 | own accumulation reproduces the consumer ≤ 1 % per bin | — | aggregate 0.293 vs 0.290; per bin up to 0.39 (capacity basis) | FAILED per bin, cause identified, loader read |

Read honestly: the form was predicted to fail and failed harder; the
measurement that mattered was the one line predicting the object's REMAINING
half (W2b) — wrong, and its wrongness closes the lane: there is no shallow
coal-derate residual for a better detector to find. Ninth consecutive MISO
session whose most useful output came from the part of the prior that was
wrong.


## 9. Governance

Rule 15: zero-solve, nothing registered. Rule 28(a): no R/I/G cell re-tested;
`unit_outage_short_windows` (the row carrying the partial shape) and
`campd_outage_windows` carry appended evidence, no verdict moves; §5.4 stamp.
Rule 28(c): no field. Rule 25: MISO's shard only; the cross-ISO filter defect
is NAMED in the base row's terms for the director, not stamped into another
ISO's cell. Rule 23: no constant touched; the diagnostic extract used an
existing documented switch. Rule 13: the extract is a measured availability
input read as a diagnostic. Rule 27: blob-verify after push.

**Records:** this file; `PREREG-miso209-partial-derate-phase0-2026-09-04.md`
@ `b7ed8e21`; `_miso209_partial_derate_phase0.json`;
`scripts/probes/_miso209_partial_derate_phase0.py`; the production extract
`data/raw/campd-partial-outages-MISO.csv` (0 rows) + `.meta.json`.

Next shorthand: **miso-210**.
