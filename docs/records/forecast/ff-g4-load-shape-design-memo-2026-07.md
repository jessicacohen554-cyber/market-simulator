# FF-G4 — Load-shape evolution design memo (2026-07, WAVE FI, lane L-INP)

**Session.** WAVE FI session **FF-G4** (memo-first, FF-0C pattern — **no code, no
solve, no default moved**; the implementing session is chartered from this memo's
§8 decision boxes). Verified against `origin/main` HEAD `40dde11` (2026-07-20).
Structural template: `docs/handoffs/ff-retirement-rule-redesign-2026-07.md`
(FF-0C); DC-block precedent: `docs/handoffs/cx4-datacenter-load-design-2026-07.md`
(CX-4); currency evidence: `docs/handoffs/ff-inputs-currency-audit-2026-07.md`
(FF-0D) §1.1/§7.3.

**Registration note (FF-G1 patch not on main).** The prompt's two status-row
targets — FF plan §1.2-11 (WAVE FI frontier row) and gap-register §3.11 (FF-G4
row) — do **not exist on `origin/main` at HEAD `40dde11`**: the FF-G1 core-wiring
change that adds them lives only in `docs/handoffs/patches/ff-g1-core-wiring.patch`
(the patch also carries the FF-G1 CHANGELOG entry and the WAVE FI §6 table). Per
the FF-G4 charter ("if absent on main, note it in the memo — do not create them"),
this memo records here what those rows should say once the patch lands: **FF-G4
status `prompt issued` → `MEMO DELIVERED (2026-07-20)` — this file; owner decision
boxes §8 pending.** No plan/gap-register edit is made in this session.

---

## 0. Bottom line first

The forecast's hourly demand is a **frozen weather-year shape × one flat annual
scalar per era**. That construction makes three published, first-order realities
*unexpressible*: (1) peak and energy CAGRs diverging — **in both directions**
(ISO-NE winter peak +2.6 %/yr vs energy +0.9 %/yr; PJM energy +5.3 %/yr vs
summer peak +3.6 %/yr, flat DC load *raising* the load factor), (2) **winter
peak growing faster than summer peak**, with published winter-peaking flips
(ISO-NE winter 2035/36; NYISO baseline ~2039), and (3) **hour-level reshaping**
from electrification (heat-pump winter-morning ridge, EV night charge). The
`DEMAND_GROWTH_RATES["NEISO"]` comment already concedes the defect in-line
("the single flat scalar cannot carry both … a documented limitation").

**Recommendation (§5): Option B — additive end-use layers** (EV + space-heating
electrification blocks, published hourly profiles × published adoption
trajectories, folded in by the **same energy-relocation discipline the CX-4 DC
block already lands on main**), with the ISO's published seasonal peaks used as
**reconciliation context, never fit targets** (rule 13 posture identical to
FC-5). Dual peak/energy scalars (Option A) are graded as an honest fallback for
ISOs without published component data; weather-year blending (Option C) is
**rejected as a structural mechanism** (no historical year contains the future
electrified shape — blending spans weather variability, not structural change).
Default posture: **new gate default-off, backcast/hindcast-coerced off** — every
keeper and every existing forecast byte-identical until the owner flips it
(§8-D2). First ISO: **NEISO** (the winter-flip is the sharpest structural test
and CELT publishes the cleanest decomposition), then PJM (largest MW divergence).
LP impact is nil-to-trivial: demand is **RHS-only** — the `b` vector of the
energy-balance rows changes, no new columns, rows, or matrix structure.

---

## 1. Diagnosis — what the current mechanism can and cannot express

### 1.1 The mechanism at HEAD (verified)

- `runner.py::_scale_demand` (`runner.py:256-271`): `base_demand` — the weather
  year's actual hourly load, default `weather_year=2024` — is multiplied by one
  compound factor `Π (1 + r_y)`. The scalar is flat across all 8760 hours.
- `scenarios.py::resolve_demand_growth_rate` (`scenarios.py:7159`): selects
  `r_y` from `DEMAND_GROWTH_RATES[iso][path][era]` (`constants.py:876`), era =
  `near` (≤ `DEMAND_GROWTH_TRANSITION_YEAR` = 2030, `constants.py:945`) or
  `long`, low/mid/high interpolated at the PB percentile.
- The **data-center block** (`data/datacenter.py::add_datacenter_block`,
  called at `runner.py:760`) is the one existing shape-touching mechanism: it
  *relocates* the DC energy already inside the total growth rate out of the
  peaky shape and back as a **flat** block (energy-invariant at mid;
  deliberately energy-shape-only — it flattens, it cannot add seasonality).
- An **electrification stub exists but is dead**: `data/datacenter.py::
  electrification_shape` returns zeros; the CX-4 §4 `electrification_shape_path`
  config field was never added (verified — no such field in `scenarios.py`).
  The seam FF-G4 needs was designed in CX-4 §4 and deferred pending sources.

### 1.2 Three structural consequences (rule 1 — mechanism errors, not residuals)

1. **Peak-CAGR ≡ energy-CAGR by construction.** A flat scalar preserves the
   load factor forever. Every published forecast above says peak and energy
   diverge — the FF-1C comments already have to *blend* them into one number
   (NEISO mid 1.3 %/yr "blends" 1.0 energy / 2.6 winter peak; the constant's
   own comment flags it).
2. **Seasonal structure frozen at the weather year.** ISO-NE's published
   winter-peaking flip cannot occur in any model year, ever: if 2024 was
   summer-peaking, 2050 is summer-peaking. Winter-risk instruments downstream
   — the FF-1B correlated forced-outage derate (cold-snap-correlated), MISO's
   seasonal capacity construct, winter fuel inventory — all evaluate against a
   winter load that never grows relative to summer.
3. **Hourly structure frozen.** Heat-pump morning ridges and EV evening
   charging move the *within-day* shape. Everything priced off the diurnal
   spread inherits the error: storage value-stack entry (duration-sized
   arbitrage windows, `model/storage.py`), scarcity timing (`hours_ge_*`
   trajectory rows in `full_horizon_summary.json`), net-load-shape-dependent
   ELCC saturation, and the peak-anchored capacity screens
   (`peak_demand` at `runner.py:761` feeds the retirement reliability floor,
   reserve-margin backstop, and CR-1 capacity position).

### 1.3 Blast radius of the error

Because `peak_demand` and hourly `year_demand` feed every capacity screen, the
error is not cosmetic: an ISO whose real risk is migrating to winter mornings
gets a model that retains/builds for summer afternoons, prices storage on a
stale diurnal spread, and reports scarcity hours in the wrong season. FC-2's
scarcity-corridor and I12 reserve-margin gates are all evaluated against the
frozen-shape peak. This is exactly the class of "wrong structure, right-looking
annual numbers" defect rule 1 exists to catch: annual energy can be perfectly
calibrated while every shape-sensitive mechanism sees a wrong world.

---

## 2. Published shape/peak decomposition per ISO (grounding table)

Web research this session (2026-07-20), reusing — not duplicating — the FF-0D
audit's §7.3 manual-download rows (M3–M7, M11–M13). Provenance discipline:
**[F]** = read on a fetched page; **[S]** = search-snippet only, unverified on a
fetched page; **BLOCKED** documents are MANUAL DOWNLOADS (§8-D4) — nothing
transcribed from memory (rule 5). Every number below is **context for scoping
the mechanism, never a fit target** (rule 13).

### 2.1 Peak vs energy CAGRs — the divergence the flat scalar cannot carry

| ISO | Vintage (current?) | Summer peak | Winter peak | Energy | Flip statement |
|---|---|---|---|---|---|
| **ISO-NE** | 2026 CELT, May 2026 (current; = M6/M13) | 25,228 MW 2026, **+0.6 %/yr** [F] | 20,483 MW 2026/27 → 26,411 MW 2035/36, **+2.6 %/yr** (2.9 % colder-weather) [F] | 116,679 → 127,660 GWh, **+0.9 %/yr** [F] | **Winter exceeds summer in winter 2035/36** (50/50); winter peaks migrate to *morning* after 2030 [F/S] |
| **PJM** | 2026 Load Forecast, Jan 2026 (current; = M11) | **+3.6 %/yr** 10-yr (222,106 MW by 2036), +2.4 %/yr 20-yr [F] | **+4.0 %/yr** 10-yr (204,650 MW 2035/36), +2.7 %/yr 20-yr [F/S] | net energy **+5.3 %/yr** 10-yr [F] | No stated flip — winter closes the gap but stays below summer in-window [F] |
| **ERCOT** | 2025 LTLF official + preliminary 2026–2032 LTLF (Apr 2026, explicitly unadopted; = M5) | 10-yr **hourly** forecast published; ~138 GW adjusted peak by 2030 [F] | summer AND winter weather-zone peak tables in the LTLF report [S — report PDF BLOCKED] | energy AAGR ~13.6 % 2025–2031 TSP-adjusted (DC-driven) [S] | None ERCOT-published (third-party literature only) |
| **NYISO** | **2026 Gold Book, Apr 2026 — NEWER than the audit's M4 (2025)** | **~0.8 %/yr** to ~38 GW by 2050 [F] | **~2.8 %/yr** to ~48 GW by 2050 (26 % above summer at 2050) [F] | 30-yr CAGR revised 2.0 → **1.1 %/yr** (~152 → 238 TWh 2050 baseline) [F] | **Baseline crossover ~2039**; higher-demand ~2035; lower-demand mid-2040s [F] |
| **MISO** | **2026 LTLF (workshop summary Apr 2026) — SUPERSEDES the audit's M3 (Sept-2025)** | 121 GW 2025 → ~163 GW 2035 (**~3.0 %/yr**); 124 GW 2026 → 184 GW 2046 mid [F] | no separate winter CAGR in accessible sources; Dec-2024 whitepaper: stays summer-peaking, peaks converge under high electrification [S] | 678 → 1,104 TWh 2026–2046, **~2.0 %/yr** [F] | None published |
| **CAISO/CEC** | CED 2025 / 2025 IEPR, adopted Jan 2026; hourly files posted May 2026 (current; = M7) | ~46.5 GW → 66–74.9 GW by 2045 (low/high, +42–61 %) [S] | no separate winter series; summer-peaking retained | statewide +up to 61 % over 20 yr, EV-driven [F, partial] | None stated |

Two readings matter for mechanism choice. First, the divergence runs in **both
directions**: ISO-NE/NYISO winter peaks grow ~2–4× energy (electrification —
shape *sharpens* in winter), while PJM **energy grows faster than either peak**
(5.3 vs 3.6/4.0 %/yr — flat DC load *raises the load factor*), and MISO
publishes the same load-factor rise (~63 % → 68 %). A single peak-morph scalar
(Option A) has no way to express the PJM/MISO direction at all without going
*negative* on the morph — additional evidence the divergence is
component-driven, not a shape knob. Second, the two ISOs with published flips
(ISO-NE 2035/36, NYISO ~2039 baseline with scenario spread 2035→mid-2040s)
both attribute them to **named end-use components with published MW**:

### 2.2 Published end-use components (the Option-B layer anchors)

- **ISO-NE 2026 CELT**: heating electrification (HEF) 7,165 GWh/yr and
  **5,533 MW of the 2035/36 50/50 winter peak**; transportation (TEF)
  7,074 GWh/yr, 594 MW summer / **1,509 MW winter** peak. Named standing
  documents: *Final 2026 Heat Pump Forecast* (`heatfx2026final.pdf`), *Final
  2026 Electric Vehicle Forecast* (`transfx2026final.pdf`). Since the 2025
  cycle ISO-NE models the whole forecast **hourly** [S]; the public CELT
  workbooks appear annual/seasonal/monthly — whether an 8760 file is
  downloadable is unverified (D4 item). [F/S]
- **NYISO 2026 Gold Book** (2050 baseline): heat pumps **+19 GW winter /
  +2 GW summer** peak; EV winter contribution ≈1.4× summer (charging
  concentrated 22:00–03:00, peaking ~01:00); data centers plateau ~2.6 GW with
  near-flat profiles; hydrogen electrolysis removed from the 2026 vintage. No
  public long-term 8760 policy-case shape files found. [F]
- **CEC CED 2025**: **downloadable 8760 hourly demand forecast files**
  (1-in-2) for CAISO/PGE/SCE/SDGE/VEA × three scenarios, plus a peak-forecast
  workbook and a data-center load-profile analysis — the one ISO where the
  planner itself publishes the future *hourly* shape. [F]
- **MISO 2026 LTLF**: DC 1.2 GW/9.6 TWh (2026) → 20.5 GW (2030) → 33.5 GW/
  266 TWh (2046); EVs 62 TWh of the 426 TWh 20-yr energy growth; load factor
  ~63 % → 68 %. [F]
- **PJM 2026**: zone-level large-load adjustments (14 of 15 zones DC-related);
  component attribution of the 2026 revision (large loads −0.7 %, economics
  −0.5 %, EV −0.1 % on summer peak). Report PDF BLOCKED — the component
  MW-by-year tables are a manual pull (M11). [S]
- **ERCOT**: large-load additions embedded in the downloadable TSP-provided /
  ERCOT-adjusted **hourly** forecast files (~46 MB each, 10-yr horizon) —
  ERCOT publishes future hourly shapes but not an end-use decomposition. [F]

### 2.3 M-row currency re-verification (charter item)

| Audit row | Status 2026-07-20 |
|---|---|
| M3 MISO Sept-2025 LTLF | **STALE — supersede with the 2026 LTLF** (Apr-2026 workshop summary + whitepaper) |
| M4 NYISO 2025 Gold Book | **STALE — supersede with the 2026 Gold Book** (Apr 29, 2026; major downward revision: energy 2.0 → 1.1 %/yr, winter-peak growth ~halved, hydrogen removed) |
| M5 ERCOT LTLF | Current (2025 official; Apr-2026 preliminary exists but is explicitly unadopted — treat 367,790 MW-by-2032 as unofficial) |
| M6 / M13 ISO-NE 2026 CELT | Current; M13's winter-flip rows confirmed (flip 2035/36) |
| M7 CAISO CED workbook | Current (adopted Jan 2026; hourly files posted May 2026) |
| M11 PJM 2026 Load Forecast | Current (Jan 2026; PDF still bot-walled) |
| M12 NYISO Gold Book corridor row | Points at the 2026 edition now (same supersession as M4) |

---

## 3. Field practice (plan §4 mandatory survey) — adopted / rejected

Same provenance tags as §2 ([F] fetched / [S] snippet-only / BLOCKED). The
survey question: how do long-horizon capacity-expansion and production-cost
models evolve the hourly demand shape, vs scaling a frozen weather-year shape?

### 3.1 NREL EFS / dsgrid / ReEDS — **ADOPTED (the profile source + the layering precedent)**

- The **EFS Load Profiles** dataset publishes hourly end-use demand profiles
  aggregated to state/sector/subsector for 3 electrification levels ×
  3 technology-advancement speeds, at snapshot years 2018/2020/2024/2030/2040/
  2050; generated by EnergyPATHWAYS and "further calibrated for use in the
  ReEDS capacity expansion model" [F, OEDI submission 8199
  (data.openei.org/submissions/8199); canonical data.nrel.gov/submissions/126
  BLOCKED (DNS); 7.5 GB archival mirror on Zenodo (record 14782874) [F]].
  EFS is a *completed* (archival) study; its live successor is **dsgrid**
  (ResStock + ComStock + TEMPO county-hourly bottom-up, "time-synchronized
  with solar and wind data sets") [F, dsgrid page mirror; S for the
  ResStock/ComStock v2021 profiles scaled by AEO-2021 annual growth].
- **ReEDS** consumes exogenous hourly demand trajectories: current docs carry a
  menu of **EER (Evolved Energy Research) hourly load profiles each with its
  own 2050 load level and CAGR** [S — fy26osti/93617.pdf fetched but
  binary-unextractable]; historical regional load from EIA-930 [F, ReEDS-2.0
  repo docs; note the GitHub repo was archived read-only 2026-04-22 [F]].
- **Take:** the field's reference implementation of shape evolution is
  precisely Option B's architecture — bottom-up end-use hourly layers whose
  adoption trajectories move the shape. EFS profiles (state-aggregable to our
  ISOs, scenario-graded low/mid/high) are the natural profile source where an
  ISO publishes none. Snapshot-year granularity (interpolate between 2030/
  2040/2050) is compatible with our anchor-interpolation convention.

### 3.2 EPA IPM — **ADAPTED (dual targeting confirmed) / REJECTED (LDC form)**

IPM derives **seasonal load-duration curves per run year per region** from AEO
peak + total-demand forecasts on FERC-714/ISO hourly shapes — the LDC morphs
each run year because peak and energy are targeted separately — and adds an
explicit **EV demand layer** (OTAQ-provided) onto the non-EV AEO baseline
[S — 2023 Reference Case PDF fetched but text-unextractable; doc-structure
page [F] confirms the LDC attachment tables]. **Adapted:** even a
duration-space model refuses peak≡energy; that is independent confirmation the
single-scalar construction is behind practice. **Rejected:** the LDC form
itself — this model is chronological full-8760 by non-negotiable rule 8.

### 3.3 Commercial practice (Modo / Energy Exemplar / CPUC RESOLVE-SERVM) — **ADOPTED (the layering + targeting template)**

- **Modo Energy** (Jan-2026 Eastern Interconnection docs — the clearest public
  "load layering" statement): one base weather year (2022) regressed on
  HDD/CDD; **five additive segments** — base, BTM solar (negative), EV
  charging, building electrification (heat-pump winter seasonality), and
  node-specific large-load/DC increments — each **stretched to the published
  seasonal peak and annual energy targets** (NYISO Gold Book), with
  alternative weather years as scenario overlays [F,
  docs.modoenergy.com/pages/jan-2026/eastern-interconnection/demand/].
- **CPUC IRP (E3 RESOLVE + Astrapé SERVM)** — the reference regulatory
  implementation: hourly consumption from **23 weather years (1998–2020)**;
  the IEPR forecast decomposed into an underlying shape plus **explicitly
  modeled "demand modifier" component layers** (EV by vehicle class, BTM
  PV/storage, AAEE efficiency, fuel-switching/electrification) [F, CPUC
  unified RA/IRP datasets page]; each weather-year realization of a study year
  "scaled and stretched" to that year's IEPR **annual peak and energy** [S].
- **Energy Exemplar (PLEXOS/Aurora)** ships hourly demand shapes sourced from
  FERC-714/ISO history with vendor growth forecasts; Aurora dispatches
  chronological hourly demand [F, energyexemplar.com].
- **Take:** the commercial state of the art = base historical shape +
  **additive end-use layers** + a **peak-and-energy dual-target stretch**,
  with weather-year multiplicity reserved for adequacy/uncertainty — i.e.
  Option B primary, Option A as the calibration step, Option C as an
  uncertainty overlay (exactly our §4 grading; the stretch step's treatment
  here is §4.4).

### 3.4 EPRI (Load Shape Library / US-REGEN) — **ADOPTED (corroboration) / REJECTED (LSL as profile source)**

**US-REGEN** builds demand bottom-up from an end-use model (space
heating/cooling, vehicle charging, industrial processes mapped to hourly
profiles from equipment stock + meteorology, one representative weather year)
and its published deep-decarbonization runs **flip regions to winter-peaking by
2050** (e.g. Ontario net-zero winter peak +43 % vs baseline) [F, IOP
Environ. Res. Lett. 10.1088/1748-9326/ac2197] — independent model evidence
that the winter flip is an end-use-layer *consequence*, exactly what Option B
produces. The public **EPRI Load Shape Library** (loadshape.epri.com) offers
end-use shapes but on legacy NERC regions as seasonal *typical-day* profiles,
not continuous 8760s [F] — **rejected** as a profile source (stale geography,
wrong granularity); EFS/dsgrid supersedes it.

### 3.5 Peak-and-energy targeting algorithm — **RECORDED (the frozen morph form, if Option A is ever invoked)**

A published closed-form exists for morphing a reference shape to independent
peak and load-factor targets: rank-ordered multipliers `m_i = 1 − (i−1)β` on
the load-duration curve with `β` solved analytically from the target load
factor (linear variant; logistic variant for an S-shaped adjustment), mapped
back to chronology [F, rstudio-pubs-static.s3.amazonaws.com/902387_….html].
If the owner ever selects Option A (or its §4.4 stretch step), this is the
citable frozen functional form — the placement is still a rank-based
assumption rather than a driver, which is why A stays a fallback.

### 3.6 Survey verdict

| Practice | Mechanism | Our disposition |
|---|---|---|
| NREL EFS → dsgrid → ReEDS/EER | end-use hourly layers × adoption scenarios | **Adopt** (architecture + profile source) |
| EPA IPM | per-run-year LDC from AEO peak+energy; EV layer | Adapt (dual targeting evidence); reject LDC form (rule 8) |
| Modo / CPUC-SERVM / E3 | layers + dual-target stretch + weather-year overlays | Adopt layering; stretch step deferred (§4.4); weather years stay the uncertainty axis |
| EPRI US-REGEN | endogenous end-use model; winter flips emerge | Adopt as corroboration |
| EPRI LSL | legacy typical-day end-use shapes | Reject (granularity/vintage) |
| Rank-multiplier morph | closed-form peak/energy targeting | Record as Option A's frozen form only |

---

## 4. Candidate mechanisms, graded

Grading axes per the charter: rule-1 structural fidelity; **rule-13
admissibility, test stated verbatim: "could this same quantity be produced for a
forward year from forward drivers, and would it respond to changed conditions?"**;
LP impact; data requirements; backcast byte-identity strategy; DC-block
interaction (no double-count).

### 4.1 Option A — era-keyed dual scalars (peak-CAGR vs energy-CAGR) + shape morph

**Design.** Add per-ISO `DEMAND_PEAK_GROWTH_RATES` (same
`{iso: {path: {era: rate}}}` grammar; optionally split summer/winter) beside the
existing energy-interpreted `DEMAND_GROWTH_RATES`. Each forecast year applies a
**shape-morphing rule** that hits both targets: scale all hours by the energy
factor, then reshape so the annual (or seasonal) maximum grows at the peak
factor while total energy is preserved. The classic utility-IRP construction is
a load-rank-weighted adjustment ("peak-and-energy targeting"): with `E_f` the
energy factor and `P_f` the peak factor,
`h' = E_f·h + (P_f − E_f)·peak·g(h/peak)` where `g` is a monotone weighting
concentrating the extra growth in high-load hours, renormalized to conserve
energy.

- **Rule 1 (structural fidelity): weak-to-medium.** The morph is a
  *mathematical* device, not a market/physical mechanism. It reproduces the two
  published moments (peak, energy) but invents everything between them: which
  hours the divergence lands in is chosen by `g`, not by any driver (a citable
  frozen closed form for `g` exists — §3.5 — which bounds but does not cure
  this). Crucially,
  an annual-peak morph **cannot produce the ISO-NE winter flip** unless
  extended to per-season peak targets — at which point it needs the same
  seasonal decomposition data Option B uses, while still guessing the
  within-season hourly placement.
- **Rule 13:** *the rates* pass the verbatim test cleanly (published forecast
  vintages regenerate forward and respond to conditions — same admissibility as
  today's energy rates). *The morph function `g`* does not correspond to any
  forward driver; it is a structural assumption that must be frozen (one
  documented functional form, never tuned — a tunable `g` would be an
  off-registry shape knob, rule 24 hazard).
- **LP impact:** nil (RHS-only).
- **Data:** minimal — the §2 CAGR table alone (all six ISOs publish peak and
  energy separately; seasonal split published for NEISO/MISO/NYISO at least).
- **Backcast identity:** trivial — peak table absent/equal ⇒ factor identical.
- **DC interaction:** hazardous. The DC relocation *already* moves the
  peak/energy relationship (flattens peak at constant energy). A peak-CAGR
  target taken from the ISO's *total* forecast double-counts the flattening the
  DC block performs: the published peak CAGR *includes* flat DC load, so
  morphing to it *after* relocation re-peakifies what the block just
  flattened. Composing A with the DC block requires an organic-ex-DC peak
  target — which no ISO publishes directly. This composition problem is the
  strongest argument against A as the primary mechanism.

**Verdict: viable fallback where component data is absent; not the primary
mechanism** (invented hourly placement; seasonal flip needs per-season targets;
composes badly with the landed DC relocation).

### 4.2 Option B — additive end-use layers (EV + heat-pump/space-heating blocks) — RECOMMENDED

**Design.** Extend the CX-4 pattern from one flat layer (DC) to a small set of
**shape-bearing layers**: per-ISO, per-layer normalized hourly profiles (8760,
weather-year-aligned) × an annual energy/MW adoption trajectory:

```
ELECTRIFICATION_LAYERS[iso][layer][path] = {year: TWh (or MW)}   # adoption
+ a per-ISO, per-layer normalized hourly profile (published / EFS-derived)
```

folded into `year_demand` at the **same seam** as the DC block
(`runner.py:760`), under the **same relocation discipline**
(`add_datacenter_block`'s relocate/tail regimes generalized): because the
FF-1C `DEMAND_GROWTH_RATES` are TOTAL (electrification-inclusive — the CAISO
comment says "CAISO growth is mostly electrification"), each layer's energy is
*relocated* out of the peaky-grown total and re-added on the layer's own shape,
energy-invariant at mid. The layer set is deliberately small and sourced:

- **`ev`** — light-duty + fleet charging profile; evening-weighted, mild
  seasonality.
- **`heat_pump`** (space-heating electrification) — strongly winter-peaked,
  temperature-correlated, morning/evening ridged. **This is the layer that
  produces the ISO-NE winter flip endogenously**: as its trajectory grows, the
  winter residual peak overtakes summer in whatever year the arithmetic says —
  the flip *emerges* from a driver instead of being painted on.
- (DC stays its own existing layer; no new mechanism — rule 19.)

Profiles come from published sources only (§3; NREL EFS/dsgrid hourly end-use
profiles state-aggregated to ISO, or the ISO's own published electrification
forecast shapes where they exist — ISO-NE HEF/TEF, CAISO IEPR hourly, NYISO
Gold Book policy case). **No published profile ⇒ the layer ships empty `{}` for
that ISO** (the CX-4 §2.2 "no source ⇒ ship 0" rule verbatim) — the flat-scalar
status quo persists there, honestly documented.

- **Rule 1: strong.** Each layer is a real end-use with a real physical shape
  and a real adoption driver. The seasonal flip and the diurnal reshaping are
  *consequences* of drivers, not targets. This is the same structural argument
  that justified the DC block, extended to the shape dimension.
- **Rule 13, test verbatim:** *could this same quantity be produced for a
  forward year from forward drivers, and would it respond to changed
  conditions?* **Yes on both halves, per component:** adoption trajectories are
  published forward forecasts (Gold Book/CELT/IEPR/LTLF electrification and EV
  components; state EV mandates) that regenerate each vintage and respond to
  policy/uptake changes; hourly profiles are physics/end-use simulations (EFS,
  ResStock-derived) that regenerate under changed weather-year and technology
  (e.g. cold-climate-HP performance) assumptions. Nothing is a realized outcome
  fed back; nothing can be tuned to a residual without violating the frozen
  profile/citation discipline (rule 23 analogue: profiles re-derive only on
  source update).
- **LP impact:** nil (RHS-only; layers are added to `year_demand` before
  `peak_demand` is taken, so every capacity screen sees them for free — the
  CX-4 §3.4 free-rider property, verbatim).
- **Data:** the real cost. Per ISO: one adoption trajectory per layer (the §2
  M-row documents carry these) + one normalized profile per layer (EFS download
  or ISO publication). This is a bounded, per-ISO, incremental intake — an ISO
  ships layers only as its sources land.
- **Backcast identity:** the FF-1F/CX-4 pattern verbatim — a single gate
  (`load_shape_evolution` or per-layer paths), default **off**,
  `__post_init__`-coerced off in backcast/hindcast mode, validated like
  `validate_datacenter_config`; keepers and hindcast legs byte-identical by
  construction.
- **DC interaction: clean by design.** The DC block *is already* layer #1 of
  this architecture — same seam, same relocation algebra, same path/percentile
  grammar. The no-double-count argument extends verbatim: each layer relocates
  its own energy out of the total-inclusive growth rate exactly once; layers
  are disjoint end-uses (DC ≠ EV ≠ space heating), so no energy is relocated
  twice. The one discipline point: the *sum* of relocated layer energies must
  stay below the grown total (the generalized relocate-regime guard, already
  present as the DC tail-regime branch) — an assertion, not a judgment call.

**Verdict: recommended.** It is the only candidate whose seasonal flip and
hourly reshaping are *driver-caused*; it has an on-main precedent for every
piece of machinery (resolver, relocation, gating, validation, tests); and it
degrades honestly (unsourced ISO ⇒ empty layer ⇒ status quo).

### 4.3 Option C — weather-year shape blending / re-weighting

**Design.** Blend `base_demand` across the `WEATHER_YEAR_POOL`
(`constants.py:5474`, 2023–2025) with year-dependent weights tilting toward
"more electrified-shape" pool years as the horizon advances.

- **Rule 1: fails for this phenomenon.** Every pool year is a
  ~2023–2025-vintage shape: none contains 2040 heat-pump saturation. Blending
  historical years spans **weather variability**, not **structural shape
  evolution** — a convex combination of summer-peaked years cannot become
  winter-peaked. The mechanism answers a different (real) question — weather
  uncertainty — which the pool already serves (`weather_year` axis, PB
  machinery).
- **Rule 13:** the blend weights have no forward driver to key on; any weight
  trajectory chosen to "look electrified" is an untethered shape knob (rule 24
  hazard, same class as Option A's `g` but worse — it can't even hit published
  peak targets except by accident).
- **Everything else:** cheap (RHS-only), no new data — but irrelevant given the
  structural failure.

**Verdict: rejected as a shape-evolution mechanism.** Keep the weather pool for
what it is (weather uncertainty). One legitimate residue: once Option B layers
exist, their *profiles* should be aligned to the run's weather year (a cold
weather year should stress the HP layer coherently) — that is a layer-profile
property (temperature-correlated profile families, EFS publishes by weather
regime), not a blending mechanism.

### 4.4 Hybrid (B primary + A as reconciliation check) — the recommended posture, precisely

Field practice (§3.3) runs layers **plus** a final peak-and-energy stretch to
the published forecast (Modo to Gold Book; CPUC/SERVM to IEPR; IPM to AEO).
That stretch is rule-13-*admissible* as a forward input — a published forecast
peak is a forward driver, the same admissibility class as `DEMAND_GROWTH_RATES`
itself, not a measured outcome — but this memo recommends **deferring it**, for
two model-specific reasons: (a) the composition hazard with the landed DC
relocation (§4.1 — the published seasonal peaks are DC-inclusive, and no ISO
publishes the organic-ex-DC seasonal targets a post-relocation stretch would
need), and (b) it would overwrite the one measurement we want from the first
implementation wave — *how close driver-caused layers alone land to the
published seasonal path* (if they land close, the stretch is unnecessary
complexity; if far, the gap tells us which layer/anchor is wrong).

So the initial posture: after layer fold-in, **report** modeled summer/winter
peak CAGRs beside the §2 published ones (the §6 context rows); a divergence
gets an explanation, never a nudge (FC-5 discipline). Option A's dual-scalar
machinery is **not** implemented as a second live mechanism (rule 19 — one
mechanism per phenomenon); it remains (i) the documented fallback for an ISO
whose component data proves unobtainable (then implemented *for that ISO only*
with an organic-ex-DC peak-target derivation and the §3.5 frozen morph form),
and (ii) the owner-gated "seasonal stretch" follow-up if the first wave's
measured layer-vs-published gaps justify it (§8-D1 Option D records this).

---

## 5. Recommended architecture (for the implementing session — design, not code)

1. **Config surface (rule 24).** `load_shape_evolution: str = "off"` master
   gate (+ per-layer `{layer}_path` selectors mirroring
   `datacenter_load_path`/`datacenter_percentile` only if the owner wants
   per-layer scenario axes on day one — recommendation: master gate + one
   `electrification_path` off/low/mid/high shared by EV+HP initially, splitting
   later if a scenario needs them decoupled). All fields echo to
   `run_config.json`; backcast coercion + validator per the DC pattern.
2. **Constants.** `ELECTRIFICATION_LAYERS` adoption tables (cited per §2
   sources, low/mid/high anchors) + per-ISO profile registry resolving through
   `config/paths.py` to a curated profiles datatype (`data/clean/`), schema
   under `data/dictionary/` (data-intake skill applies). Profiles are
   **frozen against residuals** (rule 23): re-derived only on source update.
3. **Fold-in.** Generalize `add_datacenter_block` into a layer iterator at the
   same runner seam (one function, ordered layers, shared relocate/tail
   algebra, single sum-of-layers guard). The DC block becomes the first layer —
   **no behavior change at current defaults** (a refactor with a byte-identity
   test), rule 19 kept: one fold-in mechanism for all additive load layers.
4. **Profile-weather alignment.** Layer profiles keyed to the run's
   `weather_year` where the source publishes weather-conditioned variants;
   else the single published normalized profile, documented.
5. **Rollout order (§8-D3):** NEISO → PJM → NYISO → CAISO → MISO → ERCOT.
   NEISO first: sharpest structural test (published winter flip), cleanest
   published decomposition, cheapest solve (~85 s/yr T0). PJM second: largest
   absolute MW divergence. ERCOT last: its growth is DC-dominated (organic
   ex-DC ≈ 0.6 %/yr, `constants.py:880`) so the existing DC block already
   carries most of its shape story.

---

## 6. Scoring & validation design (T1-F / FC-2 / hindcast / new invariant)

**How a wrong shape mechanism would be caught:**

- **FC-2 scarcity corridor (T1-F).** `full_horizon_summary.json` already
  records per-year `hours_ge_*` counts. A shape mechanism that over-sharpens
  peaks shows up as scarcity-hour counts drifting outside the
  ORDC-design-plausible corridor; one that mis-seasons them shows up in the
  seasonal placement of those hours. **Add to the trajectory rows: per-season
  peak MW and per-season scarcity-hour counts** (summer/winter split) so FC-2
  review can see season migration at all — today the summary is season-blind.
- **New invariant (proposed I15 — "load-shape integrity", report-level R/WARN
  initially).** Three checks, all closed-form, no LP: (a) post-fold-in
  `year_demand` ≥ 0 every hour/zone and energy-invariance holds in the
  relocate regime (`Σ layers relocated ⇒ annual energy unchanged` to 1e-6);
  (b) monotone plausibility: the winter/summer peak ratio trajectory moves
  monotonically (no sawtooth) and crosses 1.0 at most once; (c) **seasonal-peak
  context row**: modeled summer/winter peak CAGR reported beside the ISO's
  published values with the divergence — explicitly a context row, PASS/WARN
  only, **never FAIL on divergence from the benchmark** (rule 13; the FC-5
  divergence-explanation discipline).
- **Crossover (T1-X).** Forward years 2026–2027 run with the gate at its
  default; if the owner flips it on, the crossover's forward-year invariants
  exercise the fold-in at POC cost. No scoring change needed (≥2026 stays
  invariants-only by construction).
- **Hindcast tier: structurally silent, by design.** Backcast/hindcast pins
  measured load and the gate coerces off — so the hindcast can never detect a
  wrong shape mechanism, and equally can never be contaminated by one. The
  construction-level validation is therefore the CX-4 §6 pattern: unit/analytic
  tests (off-path byte-identity hash; per-layer additivity closed-form; profile
  normalization; adoption-anchor interpolation) plus a no-LP historical
  plausibility confrontation of adoption anchors against 2023–2025 realized
  electrification where published (context check on the *input path*, never a
  tune; rule 22 untouched — no 2022/≤2021/2019/H1-2026 contact).
- **Driver battery (FC-6).** One new Tier-1 monotonicity row:
  `electrification_path` low→high must not decrease the winter/summer peak
  ratio in any forecast year (sign-only, no threshold to tune).

---

## 7. DOF ledger sketch (rule 21 — what the implementing session must pin)

| Parameter | Identification source | Open DOF? |
|---|---|---|
| Layer adoption anchors (per ISO/path/year) | published ISO forecast components (§2) + state policy trajectories | No — cited, re-derived on vintage only |
| Layer hourly profiles | NREL EFS/dsgrid or ISO-published shapes; frozen files with sha256 | No — frozen against residuals (rule 23) |
| Relocation algebra | inherited from `add_datacenter_block` (already on main) | No |
| `electrification_path` default | owner posture decision (§8-D2) | Owner |
| Profile-weather alignment choice | source availability per ISO | Documented per ISO |
| (Option A only) morph form `g` + peak tables | would be a frozen structural choice + published peaks | **Yes — the unidentified hourly placement; a reason A is not recommended** |

No parameter anywhere in Option B is identified from a model residual; a shape
residual that survives sourced layers is an open finding routed to L-INP, never
a profile edit (rules 1/11/13/14).

---

## 8. Owner-decision boxes

**D1 — mechanism choice** *(gates the implementing session; nothing lands
without this call)*:

- **Option A — dual peak/energy scalars + frozen morph.** Cheap, all-ISO
  coverage from the §2 table alone; invents hourly placement; cannot express
  the winter flip without seasonal targets; composes badly with the landed DC
  relocation (§4.1). Fallback only.
- **Option B — additive end-use layers (EV + heat-pump), RECOMMENDED** (§4.2,
  architecture §5). Driver-caused shape evolution; every machinery piece has an
  on-main precedent; per-ISO incremental data cost; unsourced ISOs keep the
  status quo honestly.
- **Option C — weather-year blending.** REJECTED for this phenomenon (§4.3).
- **Option D — B with A as a per-ISO fallback where the owner declines B's
  data intake** (§4.4; A then needs its own organic-ex-DC peak derivation memo
  row before implementation).

**Recommendation: B** (D-form only if a specific ISO's sources prove
unobtainable after the D4 intakes are attempted).

**D2 — default posture**: gate ships **default-off** (backcast/hindcast-coerced
off regardless); flip-to-on is a §2.1a-style posture decision taken per ISO
after a T0 before/after and the §6 context rows exist — the
`datacenter_load_path` precedent (landed off, owner-flipped to `mid` in FF-1F
after evidence). Recommendation: **off until NEISO's T0 evidence is on the
table**, then decide NEISO first.

**D3 — first-ISO order**: NEISO → PJM → NYISO → CAISO → MISO → ERCOT (§5.5
rationale). Recommendation: charter NEISO+PJM in the first implementing
session; the rest ride subsequent intakes.

**D4 — data intakes to authorize** (all forward-looking forecast documents —
no rule-22 quarantine contact; each lands per the data-intake skill with
sha256-pinned sources; rows marked ⬇ are bot-walled manual downloads):

1. ⬇ **ISO-NE 2026 CELT forecast-data workbook + *Final 2026 Heat Pump
   Forecast* (`heatfx2026final.pdf`) + *Final 2026 Electric Vehicle Forecast*
   (`transfx2026final.pdf`)** — the NEISO layer anchors (HEF 5,533 MW winter
   2035/36; TEF 1,509 MW winter) and, if the CELT hourly modeling is exposed
   in any download, the NEISO profiles. Extends the audit's M6/M13 pull.
2. ⬇ **PJM 2026 Load Forecast Report PDF/XLSX** (M11) — winter/summer/energy
   MW-by-year + the zone-level large-load component tables.
3. **NYISO 2026 Gold Book** (supersedes M4/M12 — 2025 edition is stale): the
   baseline + scenario energy/peak tables and the heat-pump/EV/DC component
   MW; XLSX is normally fetchable from nyiso.com.
4. **CEC CED 2025 hourly demand forecast files** (M7 refresh) — the published
   8760s for CAISO/PGE/SCE/SDGE/VEA × 3 scenarios; directly usable as the
   CAISO future-shape benchmark AND as a profile source.
5. ⬇ **MISO 2026 LTLF results summary + whitepaper** (supersedes M3 — Sept-2025
   is stale): peak/energy/DC/EV component tables.
6. **ERCOT 2025 LTLF hourly forecast files** (M5-adjacent; ~46 MB each) —
   optional, lowest priority (ERCOT rides the DC block; §5.5).
7. **NREL EFS Load Profiles** (OEDI submission 8199; Zenodo archival mirror
   record 14782874 if OEDI/data.nrel.gov stay DNS-blocked) — the Option-B
   profile source where the ISO publishes none: hourly end-use profiles by
   state/sector, Reference/Medium/High × Slow/Moderate/Rapid, snapshot years
   2030/2040/2050 (§3.1). dsgrid ResStock/ComStock/TEMPO products are the
   refresh channel if a newer vintage is wanted. sha256-pinned into a new
   `data/raw/load-shape-benchmarks/` (or extending `benchmark-corridor`)
   datatype at implementation, not in this session.

---

## 9. Scope attestation

- **No code, no solve, no default, no dashboard touch.** Deliverables: this
  memo + a CHANGELOG entry (shipped as
  `docs/handoffs/patches/ff-g4-memo-changelog.patch` — CHANGELOG.md is 4.5 k
  lines, not safely API-transportable whole; same byte-verified-patch
  precedent as the 2026-07-19 costs session, commit `ae6bf68`).
  `constants.py` untouched (per charter: anything
  that would have needed it is written here instead).
- **Rule 13/22 held.** No number here is a fit target; no out-of-training year
  was solved, scored, or intaken; every figure in §2 carries its source and
  fetch status; nothing was transcribed from memory (rule 5) — bot-walled
  documents are MANUAL DOWNLOADS NEEDED rows (§2/§8-D4).
- **Plan/gap-register rows:** not edited — absent on main (see the
  registration note at top); their post-patch status line is recorded there.

*Produced 2026-07-20 (FF-G4, memo-only session). Gates the load-shape
implementing session on §8 owner sign-off.*
