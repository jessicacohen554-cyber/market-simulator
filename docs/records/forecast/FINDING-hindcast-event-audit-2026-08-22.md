# FINDING — Cross-ISO audit of hindcast capacity-event channels and scoring actuals (2026-08-22)

Follow-up to the same-day Byron/Dresden (PJM announced-channel false-retire) and
Mystic 8/9 (NEISO actuals-coverage) findings: a systematic sweep of the
forecast/hindcast capacity-event stack for further defects of both classes,
across all six ISOs. Method: the vintage-2020 and vintage-2023 EIA-860
operable/proposed sheets were diffed against the current (2025 Early Release)
sheets, the committed within-window retiree snapshot
(`data/raw/eia-860/eia860_generator_retired_within_window.parquet`), the
confirmed-retirements registries, and each ISO's committed
`capacity_actuals_<iso>.csv` — no solve run. All numbers regenerate from the
committed data.

## F1 — Diablo Canyon false-retires in every committed CAISO hindcast posture (BUG)

The vintage-2020 EIA-860 carries Diablo Canyon 1/2 planned retirements 2024-11 /
2025-08 (the 2016 PG&E settlement schedule), reversed by SB 846 (2022) + CPUC
D.23-12-036 (2023-12-15), which re-dated the exits to 2029/2030. Both units run
today. Two distinct failure modes:

1. **2020-vintage legs (plain hindcast / T1-FF):** the announced non-fossil
   channel executes both stale dates → **2.32 GW nuclear false-retire**, the
   exact Byron/Dresden mechanism. Ex-ante-defensible at V=2020 (SB 846
   post-dates the cutoff) but scored as false retirement. **The new
   `hindcast_verified_announced_exits` flag does NOT cover it**:
   `load_announced_reversal_plants` requires every registry row superseded, and
   Diablo carries *live* SB-846 rows (re-dated, not cancelled), so it is
   excluded from the reversal set by construction.
2. **2023-vintage crossover legs (T1-X): a genuine precedence defect, not an
   information-set artifact.** The vintage-2023 EIA-860 *still* carries unit
   2's 2025 planned date (1,164 MW), SB 846 IS knowable at V=2023-12-31 and the
   registry's live rows load into the confirmed channel — but
   `apply_announced_retirements` honours every within-horizon non-fossil date
   regardless: `confirmed_plant_codes` is consulted only for *beyond-horizon*
   dates. The registry docstring's "its announced date still stands and the
   confirmed channel governs" is not implemented for within-horizon dates, so
   the model retires unit 2 in 2025 *and* would retire it again per the
   confirmed schedule in 2030.

**Proposed fix (two halves, matching the two modes):** (a) channel precedence —
a unit whose plant carries a live, information-gate-admissible confirmed
instrument takes the confirmed schedule and its stale announced date is
suppressed at any horizon (this is a plain bug fix: rule 19, one mechanism per
exit, and it makes V≥2022 legs correct with no posture change); (b) under
`hindcast_verified_announced_exits`, also suppress announced dates for plants
with *any* superseded registry row read un-gated (covers the V=2020 legs the
same way the Byron/Dresden fix does). Both scorer-visible via the existing
§c.5-1 lane.

## F2 — Systemic actuals hole: exits during 2023–2024 are missing from every ISO's scoring target (BUG, data)

`build_capacity_actuals` unions the retired sheets of the current release and
every vintage — but `vintage_2023/` and `vintage_2024/` were intaken **without
retired sheets**, and the 2025 Early Release retired sheet drops many
2023–2024 exits outright (the Mystic pattern; EIA also dropped whole plant
codes). Cross-checking the within-window retiree snapshot (built from the
2024-release retired sheet) against each committed actuals CSV, after applying
the builder's own vintage-status gate (units inactive at the 2020 vintage —
the J T Deely "papered exit" class — are correctly out of scope):

| ISO | genuinely missing | headline units |
|---|---|---|
| PJM | **2.14 GW** | W H Sammis 5-7 (1,694 MW coal, 2023), AES Warrior Run (229 MW, 2024), Southeast Chicago GTs (~407 MW, 2024), Parlin |
| NYISO | **0.50 GW** | Astoria Gas Turbines 2/3/4 (12×41.9 MW, 2023) |
| NEISO | **0.34 GW** (beyond the fixed 1.74 GW Mystic) | Tanner Street CC, South Meadow 11-14, Androscoggin Mill |
| MISO | 0.09 GW | Grand Tower 1/3 (units 2/4's 2021 exits ARE covered), Freedom CT1 |
| ERCOT | 0.03 GW | (J T Deely's 932 MW is inactive-at-vintage — correctly excluded) |

Effect: every hindcast leg's retirement recall is understated and false-retire
overstated by these amounts — PJM's coal recall miss (actual 6.9 GW, model 0)
is partly this. **Proposed class fix:** union
`eia860_generator_retired_within_window.parquet` into
`build_capacity_actuals::build_retirements` (same downstream BA/window/status
gates, so papered exits stay excluded) instead of accreting per-plant sidecar
rows; the sidecar remains for the dropped-plant-code class the snapshot cannot
see (Indian Point). Alternative: intake the 2023/2024-release retired sheets
into their vintage dirs.

## F3 — CAISO has no capacity-events scoring target at all (GAP)

There is no `capacity_actuals_caiso.csv`, and no committed CAISO hindcast
bundle carries a `score.json` — CAISO legs have only crossover dispatch-skill
scores. CAISO's retirement/addition channels (including F1) have never been
graded. Fix: `build_capacity_actuals.py --iso CAISO` (BA code `CISO`), then
score the existing bundles.

## F4 — Stale small-hydro/biomass announced dates, MISO (same class, immaterial MW)

~60 MW of MISO non-fossil (Cornell, Apple River, Saxon Falls, Superior Falls,
Trego, White River hydro; French Island biomass 2×15 MW) carries executed
announced dates 2023–2025 in the vintage-2020 sheet but still runs today. No
counter-instrument exists (dates simply slipped), so no registry row can ever
cover them — only a realized-record check (unit still operable in the current
vintage) would. Immaterial for scoring; documents why verification ultimately
wants the current-operable test rather than registry membership alone.

## F5 — Palisades restart is unrepresented on both sides (NOTE, deliberate)

MISO actuals carry Palisades' 2022 exit (RD-5 sidecar) and no 2025 restart
addition; the model has no un-retirement channel. Both sides of the 2025 fleet
comparison are consistently 812 MW short, per the sidecar's documented
treatment. Open convention question for the scoring owner, not a defect.

## F6 — Additions pipeline is clean (NO ACTION)

The vintage-2020 construction-committed (U/V/TS) thermal pipeline with COD
2021–2025 was realized almost in full: the only never-built unit across all
six ISOs is 2.6 MW (NYU Central Plant GR1, NYISO). The phantom-additions
mirror of Byron/Dresden does not exist. (Fossil announced *retirement* dates
are likewise protected by design — `forecast_fossil_retirement_economic`
makes the 25 GW of announced-but-still-running fossil a no-op in the announced
channel; its over-retirement lives in the economic screen, tracked separately.)

## Scan provenance

Class-A scan (announced 2021-25, still operable): 263 units / 51.0 GW
announced, 83 / 25.0 GW surviving, of which non-fossil (the channel that
executes): Byron/Dresden (fixed), Diablo (F1), Palisades (correct-then-restart,
F5), ~60 MW MISO small hydro/biomass (F4). Class-B scan: within-window
retirees vs actuals keyed on (plant_id, generator_id), split by
vintage-2020 status. Class-C scan: vintage-2020 proposed U/V/TS thermal vs
current operable + all retired sheets. Vintage-2023 rescan confirms F1 mode 2
(CAISO 1.166 GW; every other ISO ≤ 0.15 GW, all small).
