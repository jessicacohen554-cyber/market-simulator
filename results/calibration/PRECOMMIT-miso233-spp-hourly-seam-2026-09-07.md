# PRECOMMIT miso-233 — the hourly neighbour anchor extended to MISO's SECOND seam (SPP)

**Written and pushed BEFORE the screen solve.** Every gate, comparator, screen-year
choice, non-claim and the G-DRIFT classification below is fixed here so nothing can be
written to fit a result.

**KEEPER (the control, rule 29(b) form 4): `2026-09-06-miso-232-hourly-seam`**
(`miso232_hourlyseam_K`, git sha `451e6109`), DETERMINATION CALIBRATED, C3c the single
ledgered caveat. Rule 22: **2023–2025 only**; MISO holds no `complete` marker, so no
holdout year is solved, scored or registered. DOF ledger **41/2, unchanged** — the
mechanism adds no free parameter (every `delta_k` is a quantile of a measured series at
a structurally fixed depth grid, derived and frozen under rule 23).

**PROVENANCE CARRIED FORWARD, stated first (rule 1 `[R-STRUCT]`).** The miso-232 keeper's
full span was solved under **OWNER RE-CHARTER**, not under a gate pass: the miso-231 2024
screen was **KILLED on its pre-registered G-1 bar by 0.0183** and the bar was not moved.
Nothing in this session re-reads that as a pass, and the keeper's own non-claims travel
with it.

---

## 1. What phase 0 found — and it FALSIFIES the queue's own hypothesis

**Zero LP.** Both readouts below are computed from the keeper's committed `hourly/`
sidecars and committed measured series. `scripts/probes/_miso233_seam_slope_anatomy_phase0.py`
and `_miso233_allseam_slope_attribution_phase0.py`; JSON beside them.

The MISO lever queue's item 1 asked whether the deep PJM bands (`k = 6-8`, `delta_k` +6
to +30) are the ones under-clearing in MISO's cheap hours and costing the repaired decile
slope its magnitude (miso-232 reached +139 / +111 / +681 MW against a measured
+1,303 / +1,384 / +948). **They are not, and the reconstruction says so from the keeper's
own artifacts.**

The instrument is miso-231's readout B, extended to every seam: `in_merit[k,t]` from the
keeper's committed `MISO_external` P1 price against each seam's own ladder,
`band_mw[k,t] = clip(cap − k·width, 0, width)` on the keeper's own
`miso_seam_envelope_merit_cap=True` waterfall and its own measured `hour_ending_key=True`
envelope. Harness: **corr(reconstructed total, committed imports) = +0.924 / +0.946 /
+0.971**, means 4,458 / 2,961 / 2,520 MW against committed 5,110 / 3,396 / 2,455.

| seam | ladder it clears against | recon slope d1−d10 | MEASURED seam slope |
|---|---|---:|---:|
| **PJM** | HOURLY neighbour, `border(t) + delta_k` (repaired, miso-231/232) | **+2,377 / +2,611 / +2,704** | +1,319 / +1,052 / +815 |
| **SPP** | INCUMBENT fixed MISO-hub Q-Q ladder | **−414 / −481 / −553** | +317 / +466 / −50 |
| **South** | INCUMBENT fixed MISO-hub Q-Q ladder | **−919 / −1,135 / −827** | +72 / +60 / +646 |

- **The PJM seam is already STEEPER than the measured PJM seam in every year.** Its
  cheapest decile loses 194 / 194 / 271 MW to the deliverability envelope and 525 / 637 /
  881 MW to merit, and the exact attribution identity
  (`width = cleared + lost_to_envelope + lost_to_merit + lost_to_both`) puts the deep
  bands' contribution at +1,229 / +597 / +316 MW — positive, not missing. **Item 1's
  hypothesis is falsified; there is no PJM depth repair to make.**
- **What cancels the repair is the two seams the hourly form never covered.** SPP and
  South carry the exact defect miso-226 named: a FIXED ladder cleared against the model's
  OWN price leaves merit when MISO's price falls, which is when MISO actually imports.
  Their slopes are large and wrong-signed against measured seams that are positive or flat.

**This re-routes the lane from queue item 1 to queue item 3, and item 3's stated blocker
is gone.** The queue records SPP/South as riding the incumbent anchor "for want of a
measured hourly price series". Lane **SPP-14 landed one on 2026-09-06** —
`data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet`, SPPNORTH_HUB /
SPPSOUTH_HUB DA + RT hourly, **8,754 of 8,760 hours in each of 2023–2025**, from SPP's own
`portal.spp.org` file-browser API. **South stays excluded and stays a data boundary:**
SOCO and TVA are not organised markets and publish no hub or nodal price.

## 2. The mechanism — one sub-gate, zero new free parameters

`miso_seam_neighbour_hourly_spp` (new `ScenarioConfig` field, **default False**,
byte-identical off — pinned by test). SPP band `k`'s offer becomes

```
pi_k(t) = spp_hub(t) + delta_k          band k clears iff  spread(t) > delta_k
```

against the measured SPP **NORTH** hub DA (`measured_miso_spp_hub_prices`). It is a
**SUB-GATE of `miso_seam_neighbour_hourly_ladder`, never a mechanism beside it** (rule 19
`[R-ONE-MECH]`): the solve path REFUSES it without its parent and the injector applies it
only when the parent actually took, so the two seams are never anchored apart. It rides
the same per-seam `hourly_anchor` mapping the PJM entry already uses — no new seam
machinery. Registered in the matrix under its family's row (`seam_neighbour_hourly_ladder`),
per rule 28(c)'s variant-flag route.

`delta_k` is derived by `derive_miso_seam_ladders.py::derive_spp_neighbour_hourly` —
**byte-for-byte the incumbent estimator** (same `_derive_one`/`qq_import`/`qq_export`
Q-Q duration coupling, same midpoint-depth grid on the same `SEAM_FLOW_TRANCHES`, same
measured EIA-930 flows, same no-wash reconciliation); the ONE degree of freedom exercised
is which measured series the coupling reads, exactly as `derive_pjm_neighbour` and
`derive_pjm_neighbour_hourly` each exercised it once. **Zero fitted parameters; the DOF
ledger stays 41/2.** The registry table is pinned to the derive's output by test, so a
hand-edited or re-tuned offset fails before it can reach a solve (rule 23).

**THE ANCHOR HUB IS `SPPNORTH_HUB`, named on TOPOLOGY before any ladder was derived**
(rule 14 `[R-ACCURATE]` misalignment clause): the seam our reduced network carries is ONE
collapsed link hosted on the `MISO_external` (Midwest) bus — MISO's southern seam has its
own bus and its own SOCO/TVA neighbours — so the MISO-facing counterparty is SPP North.
`SPPSOUTH_HUB` is computed as a sensitivity in the probe and **selects nothing**; choosing
the hub that scored better would be the fitted-mechanism selection rule 1 forbids.

**THE CASE IS RULE 14, NOT A STATISTIC — and the statistic is stated against my own
interest.** The miso-231 admissibility reading does **NOT** transfer:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| corr(measured SPP seam flow, MISO DA) — what the model clears on | −0.216 | −0.377 | +0.082 |
| corr(measured SPP seam flow, MISO DA − SPP North DA) — the arm's basis | **+0.041** | **−0.020** | **+0.050** |
| *(PJM's, for contrast — miso-231 §1)* | *+0.240* | *+0.265* | *+0.194* |

**The spread is UNINFORMATIVE about this seam's hourly flow.** What it does is REMOVE the
wrong-signed response rather than supply a right-signed one: simulated-vs-measured flow
correlation moves −0.213 / −0.289 / +0.065 → +0.011 / −0.107 / +0.050. The mechanism is
proposed because rule 14 says to prefer the measured neighbour price over an estimate
standing in for it, and rule 1 says a structurally-correct mechanism is not judged by the
residual — **not** because the correlation argues for it. It does not.

## 3. The screen — ONE year, named on the mechanism's OWN measured footprint

**SCREEN YEAR: 2023.** Named on the footprint measure miso-231 declared and used,
unchanged — the **band-hours on which the hourly and incumbent SPP ladders disagree about
merit**, at the keeper's own committed prices, computed on the REGISTRY offsets a solve
will read:

| year | band-hours disagree | % of band-hours | hours with any disagreement | \|ΔMW\| mean | TWh moved |
|---|---:|---:|---:|---:|---:|
| **2023** | **5,279** | **7.53 %** | **54.5 %** | **234** | **2.0476** |
| 2024 | 5,010 | 7.15 % | 51.5 % | 214 | 1.8776 |
| 2025 | 4,469 | 6.38 % | 48.6 % | 229 | 2.0088 |

2023 is the maximum on the primary measure and on every secondary one. It is **not** the
year with the largest residual (2024's slope gap is larger), which is the choice rule 29
forbids.

```
MARKET_SIM_HIGHS_THREADS=4 python3 scripts/replay_keeper.py \
  results/calibration/miso232_hourlyseam_K --years 2023 \
  --out-dir results/calibration/_miso233_spp_screen \
  --set miso_seam_neighbour_hourly_spp=true \
  --note "miso-233 SCREEN: hourly neighbour anchor extended to the SPP seam"
```

## 4. THE GATES — pre-registered, STRUCTURAL, STOP-ONLY, and NONE of them is the target residual

Rule 29: the screen asks whether the mechanism does what its own arithmetic says. **It may
kill this arm; it may never promote it.** The decile slope — the thing this lane wants to
move — is **REPORTED, NEVER GATED**: a screen that read "did the slope improve" would be
the fitted-mechanism selection rule 1 forbids, done one year at a time. That is exactly
the discipline miso-231 §2 was reaching for and it binds here.

| gate | bar (fixed here, before any arm number exists) | why it is structural |
|---|---|---|
| **G-1 CONFINEMENT** | 2023 slack ≤ the keeper's own 2023 slack (**0.0000 TWh**) and dump = 0.0000 TWh; wind + solar + nuclear + hydro annual energy each within **0.05 TWh** of the keeper | the mechanism claims to re-time ONE seam; it must not force unserved energy or move the must-take base |
| **G-2 FOOTPRINT SCALE** | \|Δ annual gross imports\| ≤ **1.5 TWh** vs the keeper's 2023 **48.305 TWh** | the SPP seam's ENTIRE reconstructed annual throughput is ~2 TWh; a larger move means the mechanism reached beyond the rows it claims |
| **G-3 DIRECTION** | `corr(imports, own model hub price)` does not RISE by more than **+0.05** above the keeper's 2023 **+0.1754** | the mechanism's arithmetic REMOVES wrong-signed responsiveness; a rise is the opposite of what it asserts |
| **G-4 NO COLLATERAL FLIP** | `scripts/screen_collateral_gate.py --bundle <screen> --keeper-run-id 2026-09-06-miso-232-hourly-seam`: **zero PASS→FAIL flips** on C1 / C2 / C3a / C3b / C6 (C3c excluded), against the keeper's committed verdict | the real scorer, in memory, on the committed bench parts; nothing registered |

**A gate that fails kills the arm**, the remaining years are never spent, the kill is
reported as this session's result, and the bar is **not renegotiated** — the miso-231
precedent binds. Anything else the screen shows is reported and gates nothing.

**Full span only if all four clear**: one `--year 2023 2024 2025` invocation, one bundle
(rule 16 `[R-ALLYEARS]`), years sequential (rule 12), scored by
`scripts/calibration_verdict.py` on the registered run. Promotion rule (miso-227's,
unchanged): **promote on CALIBRATED / CALIBRATED-WITH-CAVEATS; on a LOAD-BEARING NOT-YET,
report and escalate to the owner rather than decertifying the ISO.**

## 5. G-DRIFT (rule 29(b)) — `451e6109..b7ff89ca`. **ALL INERT. Form 4 holds. NO control solve.**

```
git diff --stat 451e6109 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source \
    data/raw/reference
```
= 36 files, +27,692 / −26,341 — a large drift, and **every hunk on the MISO backcast path
is classified below** rather than waved through. The bulk is one thing: `main` registered
**SPP as the seventh ISO** (lane SPP-20) between the keeper and this session.

| changed area | class | reason |
|---|---|---|
| `config/{constants,capacity_market,fuel_trajectories}.py`, `data/{campd,renewables,transmission_expansion}.py`, `data/eia930/frames.py`, `data/fleet/models.py` | **INERT** | pure `"SPP": …` additions of new keys to per-ISO registry dicts (`BA_CODE_TO_ISO` gains `SWPP`); no MISO entry is touched |
| `data/zone_assignment.py` (+73) | **INERT** | `_SPP_STATE_ZONES` / `_spp_zone` / `"SPP": "SWPP"` / `"SPP": "SPP-North"` — a new ISO's branch; MISO's mapping unchanged |
| `data/eia930/{demand,envelopes,__init__}.py` | **INERT** | `_load_spp_hourly_demand`, `spp_net_interchange`, an `_SCALAR_INTERCHANGE_ISOS["SPP"]` entry and one docstring; MISO's demand and envelope readers unchanged |
| `data/neighbor_price.py` (+38) | **INERT** | comments plus a new import-time assertion (`_assert_hr_gas_elastic_keys_unique`) that fails only if a key names two ISOs' neighbours; every `_HR_GAS_ELASTIC` VALUE is unchanged and the guard passes |
| `model/interchange/{spec,registry}.py` | **INERT** | SPP's own `INTERFACE_NEIGHBORS` block and an `INTERCHANGE_INJECTIONS["SPP"]` entry that self-gates on `reference_price_interface` (default-off for SPP); MISO's registries untouched |
| `config/iso_configs.py` (+142) | **INERT** | `_spp_config()` — a new ISO's topology builder |
| `config/solve_surface.py` (+17) | **INERT** | `SURFACE_ISOS` appends `"SPP"` LAST and no surface name carries an SPP token |
| `pipeline/backcast_config.py` (+46) | **INERT** | `pjm_interface_feed_admissibility_gate=(iso == "PJM")` — another ISO's branch (pjm-169) |
| `results/scarcity.py` | **INERT** | docstring only (ercot-252) |
| `scripts/run_calibration.py` `_renewable_bound_is_delivered_pinned` | **INERT** | re-added by ercot-251/252; **both call sites verified at HEAD to sit inside `if getattr(config, "ercot_gtc_limits_measured"/"ercot_wtx_curtailment_driver", False) and iso == "ERCOT"`** — another ISO's branch (rule 25) |
| `scripts/run_calibration{,_full}.py` `gas_offer_margin_anchor_vintage` | **INERT** | a new opt-in CLI/kwarg defaulting `False` and read only under `if gas_offer_margin_anchor_vintage:`; the keeper's recorded config does not carry it and `replay_keeper` does not pass it |
| `scripts/lib/{confirmed_retirements,load_forecast,nuclear_license_status,transmission_expansion}/spp.py`, `mech_matrix.py` | **INERT** | new SPP modules + a matrix-helper touch; no backcast solve path |
| `data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet` | **INERT at the keeper; LIVE only under this arm** | the new measured series; read only when `miso_seam_neighbour_hourly_spp` is armed |
| `data/raw/caiso-supply-consistent-demand/*` | **INERT** | another ISO's demand vintage |

**Measured, not asserted:** `surface_stamp("MISO", ScenarioConfig(iso="MISO",
mode="backcast"))` at HEAD `b7ff89ca` reads **`moved: {}`, `epochs: []`** — MISO's
solve-surface fingerprint and cache key are byte-identical to the keeper's.

**Conclusion: the keeper's committed bundle IS the control (form 4). No control solve is
spent.** Recorded before the arm is solved.

## 6. Pre-committed NON-CLAIMS — carried onto the determination basis if it promotes

1. **This does NOT close the slope-magnitude gap; at most it removes one of the two
   cancelling seams.** The static instrument predicts the SPP seam's own 2023 slope moves
   −346 → −103 MW (+243), against a South seam left at −919 and a measured total gap of
   ~1,164 MW. **South is untouched and stays the larger contributor.**
2. **The admissibility statistic does not support this arm** (§2). It is a rule-14
   accuracy repair on a structurally-correct, owner-ruled seam form, and it says so.
3. **The `SPPNORTH_HUB` choice is a rule-14 reconciliation of a collapsed link**, not a
   measurement: the real boundary is two paths and our topology carries one.
4. **C3c is UNTOUCHED.** No scarcity claim of any kind; C3c stays the designated frontier
   (2026-07-20), opened only by a NEW admissible measured identification under its own
   charter.
5. **The keeper's own provenance travels forward**: its span was solved under owner
   re-charter after the miso-231 screen was killed on G-1 by 0.0183.

## 7. Already settled — not re-opened here (rule 28(a) DO-NOT-REDO)

The coal D-1 regression (attributed and closed, miso-231); `ct_mustrun_per_plant`
(refused, rule 13); the CT_PEAKER offer level (closed by `ct_netload_drag`, window
`[10,21)` frozen); the **PJM** `delta_k` ladder (derived and frozen — never re-derived,
re-tuned or swept, and this session does not touch it); C3c (frontier, no LP spent here).

## 8. Governance

Rule 1 `[R-STRUCT]`: structure first — the arm is proposed on rule 14 and the owner-ruled
seam form, the gates are structural and STOP-only, and the target residual is not gated.
Rule 13 `[R-MEASURED]`: the SPP hub DA is a published market price with the same forward
analogue the PJM border price already carries. Rule 14 `[R-ACCURATE]`: the measured
neighbour price replaces an estimate; the collapsed-link misalignment is declared, not
buried. Rule 15: registered on the dashboard in this session if it reaches a span; the
screen bundle is **never registered** and is **DELETED before merge** (rule 29(c)) — every
number this session will cite from it lives in this document and its FINDING. Rule 16: the
span, if reached, is one invocation and one bundle. Rule 19 `[R-ONE-MECH]`: a sub-gate of
the hourly family, refused without its parent, displacing the incumbent SPP ladder and
never stacked on it. Rule 21 `[R-DOF]`: 41/2, no free parameter added. Rule 22: 2023–2025;
MISO holds no `complete` marker and no holdout year is touched. Rule 23
`[R-FROZEN-DERIVE]`: the SPP derive runs because its SOURCE DATA LANDED (SPP-14,
2026-09-06), never because a residual moved; the PJM ladder is not re-derived. Rule 24
`[R-REGISTRY]`: one registered `ScenarioConfig` field, in `run_config.json`, in the cache
key. Rule 25 `[R-ISO-SCOPE]`: MISO only; no other ISO's default or shard moves. Rule 27
`[R-PUSH]`: every pushed blob verified against local. Rule 28(b): the
`seam_neighbour_hourly_ladder` MISO cell is updated in this session, promotion or kill
alike. Rule 29 `[R-SCREEN]`: phase 0 first, one screen year named on the mechanism's own
footprint, gates fixed above before the solve, keeper as control, no control solve.
