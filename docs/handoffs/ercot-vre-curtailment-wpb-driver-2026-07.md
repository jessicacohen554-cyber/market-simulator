# ERCOT VRE under-curtailment — WP-B derived curtailment-share driver (2026-07-07)

**Scope.** Builds the sanctioned WP-B fix for the ERCOT West/Panhandle wind (and
solar) under-curtailment that displaces gas and drove C2 to FAIL
(`docs/handoffs/ercot-vre-curtailment-topology-scope-2026-07.md`). Steps 1–2
ruled out measured GTC limits, negative-price dumping, storage timing, and
must-run; the lever is the sub-zonal Permian/CREZ **nodal** congestion the 8-zone
reduction collapses into one wide West→North pipe. WP-A (zone split) is deferred
(the binding elements are *internal* to the West zone — see §4). This is WP-B: a
forward-admissible, net-load-indexed curtailment-share driver anchored to
**measured** transmission-binding frequency.

## 1. The new unlock — an authoritative station→zone crosswalk

The nodal identification the scope doc called for needed a station→area
crosswalk. Two data intakes make it defensible (both committed under the
data-intake contract):

- **ERCOT Settlement Points List & Electrical Buses Mapping (NP4-160-SG)** —
  `data/raw/ercot-settlement-points/`. Its `SUBSTATION` code matches the NP6-86
  `FromStation`/`ToStation` codes **exactly**, covering **93.3%** of West-corridor
  binding-interval weight (2023–2025), and carries each station's
  `SETTLEMENT_LOAD_ZONE`. No fuzzy matching.
- **HIFLD Electric Substations (TX)** — `data/raw/hifld-substations/`. Independent
  coordinate source used only to *validate* the crosswalk: LZ_WEST has
  **precision 1.00** against `zone_assignment._ercot_zone` geography for the West
  Texas Export / Permian / CREZ region. Every top West binder (ODEHV, VEALMOOR,
  KNAPP, SCRCV, RILEY, …) → LZ_WEST; every top South-Texas binder (RIOHONDO,
  LAREDO, CATARINA, DILLEY, MAVERICK, …) → LZ_SOUTH and is correctly excluded.

Two earlier attributions were tried and **rejected** as insufficiently clean:
co-binding-with-interface (mislabels Coast/South as West via system-stress
correlation) and HIFLD fuzzy name-matching (~24% coverage, false positives like
LMESA→El Paso). The ERCOT SPL is the authoritative, exact, high-coverage source.

## 2. The measured signal — `ercot-wtx-congestion` (new curated datatype)

`scripts/curate_ercot_wtx_congestion.py` → `data/clean/ercot-wtx-congestion`
(schema `data/dictionary/schema/ercot-wtx-congestion.schema.yaml`). Per local
clock hour: the fraction of SCED executions with ≥1 **West-corridor** constraint
binding, where "West-corridor" is the **structural** set (not a top-N cutoff):
any 138/345 kV binding constraint with a LZ_WEST endpoint, plus the WESTEX/PNHNDL
export GTCs. Reads only measured NP6-86 SCED incidence + the SP crosswalk — never
the reported curtailment volume.

Measured West-corridor congestion fraction rises with VRE build-out:
**0.42 / 0.54 / 0.64** (2023/24/25), congested in **62% / 70% / 76%** of hours —
matching reported wind curtailment "active in 66–90% of hours." Concentration is
stable: the two interface GTCs cover ~30–42% of congested hours, then ~10–15
distinct *internal* Permian/CREZ 138/345 kV lines reach 80–95%.

## 3. The driver — SHAPE (measured) + LEVEL (single coefficient)

`scripts/derive_ercot_wtx_curtailment_share.py` →
`data/raw/reference/ercot_wtx_curtailment_share.csv`; consumed at solve time by
`market_sim.data.curtailment_share`, gated on
`ScenarioConfig.ercot_wtx_curtailment_driver` (default off).

```
wind_ceiling[z,t] = wind_cf[z,t]·cap · (1 − depth_wind · congestion_share(cell(t)))   z ∈ {West, Panhandle}
cell(t) = (net_load_percentile_decile(t), hour_of_day(t), season(t))
```

- **SHAPE** `congestion_share` — the measured West-corridor binding fraction binned
  by within-year net-load decile × hour × season, pooled over in-sample years.
  Measured-only; a function of the model's OWN net-load, so it regenerates forward
  (more West VRE → deeper net-load troughs → higher share). Reproduces the
  measured binding-frequency distribution leave-one-year-out (rule #23 / the
  anti-residual gate); it is NEVER fit to the [3e] curtailment volume or a price
  residual.
- **LEVEL** `depth` — one per-tech coefficient (`ScenarioConfig.ercot_wtx_curtail_
  depth_wind`/`_solar`) converting congestion incidence into curtailed fraction,
  centred on the measured curtailment MW quantity exactly like the RTOLCAP-forward
  `deliv` coefficient (`docs/handoffs/ercot-as-coopt-plan-2026-07.md`). A stable
  structural constant of the West Texas network: **0.0998 (wind)**, LOYO
  0.0998/0.0996/0.0984; **0.1633 (solar)**, looser. `depth = 0` is the
  zero-forcing ablation.

**LOYO validation** (train two years, predict the third):

| hold | wind pred / actual | shape corr |
|---|---|---|
| 2023 | 0.063 / 0.047 | +0.34 |
| 2024 | 0.059 / 0.060 | +0.37 |
| 2025 | 0.055 / 0.071 | +0.34 |

Wind level generalizes to within ~1.5 pp with a mild congestion-trend
compression (the within-year-percentile axis normalizes away the absolute
year-over-year congestion rise). Solar is secondary (looser depth; its
midday-oversupply component differs from the wind-oriented corridor signal) — it
is exposed with its own coefficient but is not load-bearing for the C2 gas story.

## 4. Why WP-B and not the zone split / flowgates

The concentration curve (§2) shows the West curtailment rides on ~10–15 distinct
138/345 kV lines that are **internal to the West zone** (both endpoints in the
Permian/CREZ). A 1–2 zone split makes only the ~35% export-boundary component
bind (the measured WESTEX ≈ the model's existing West→North limit — the
copper-plate no-op that reverted the Far_West split). True PLEXOS-style flowgates
on intra-zonal lines need the nodal PTDFs the repo has no network model for. The
reduced-form net-load-indexed share is the standard stand-in for exactly this
"many small internal pockets below zonal resolution" situation.

## 5. Results — ercot42 probe vs zero-forcing ablation

Reproduced on the `ercot34-stage4-overlay-off` keeper (measured GTC on) via
`scripts/replay_keeper.py`, single-delta `--set ercot_wtx_curtailment_driver=true`.

- **Probe** `ercot42_wtx_curtail_probe` (depth wind 0.0998 / solar 0.1633).
- **Ablation twin** `ercot42_wtx_curtail_ablation` (driver wired, depth 0.0 —
  must reproduce the keeper byte-faithfully, isolating the depth from the wiring).

<!-- RESULTS: filled after the solves complete -->
| criterion | ercot34 keeper | ercot42 probe | Δ |
|---|---|---|---|
| C2 system volume (gas) | FAIL | _tbd_ | |
| C3a | PASS | _tbd_ | |
| C5c | PASS | _tbd_ | |
| [3e] wind curt % (2023/24/25) | 2.2 / 2.5 / 2.7 | _tbd_ | reported 4.7 / 6.0 / 7.1 |

## 6. DOF ledger (rule #21)

| free parameter | value | identification source | forward-admissible? |
|---|---|---|---|
| `congestion_share(decile,hour,season)` | measured table | NP6-86 SCED West-corridor binding frequency, geo-attributed via ERCOT SP/bus mapping (NP4-160); LOYO-reproduces the binding-frequency distribution | yes — f(model net-load) |
| `ercot_wtx_curtail_depth_wind` | 0.0998 | centred on measured curtailment MW quantity (HSL−delivered), RTOLCAP-`deliv` precedent; LOYO-stable 0.098–0.100 | structural constant |
| `ercot_wtx_curtail_depth_solar` | 0.1633 | same; looser (secondary) | structural constant |

**Zero-forcing ablation twin registered alongside** (`depth = 0`).

## 7. Guardrail attestation

- No HSL pin, no residual-tuned curtailment adder/haircut (rules #1/#13). The
  ceiling multiplies the uncurtailed CF potential; the SHAPE is measured congestion
  frequency, never the [3e] volume.
- The one coefficient touching the reported-curtailment aggregate is the per-tech
  `depth`, treated as the RTOLCAP-`deliv`-style level scalar centred on a measured
  MW quantity — LOYO-stable, in `ScenarioConfig`/`run_config.json` (rule #24), with
  the zero-forcing ablation twin (rule #21). Owner-approved path (2026-07-07).
- Applied only where the year carries measured HSL potential (no
  double-curtailment); off by default; ERCOT-only tuned curve (rules #25/#26).
- Holdouts 2022 / H1-2026 untouched — no solve on them (rule #22). Derive frozen
  against residuals; re-derive only on a new NP6-86 year or rebuilt HSL (rule #23).
- All three in-sample years in one bundle (rule #16).

## References
- `docs/handoffs/ercot-vre-undercurtailment-2026-07.md`, `…-step2-2026-07.md`,
  `…-curtailment-topology-scope-2026-07.md` — the diagnosis chain.
- `scripts/curate_ercot_wtx_congestion.py`, `scripts/derive_ercot_wtx_curtailment_share.py`,
  `src/market_sim/data/curtailment_share.py`.
- `data/raw/ercot-settlement-points/README.md`, `data/raw/hifld-substations/README.md`.
