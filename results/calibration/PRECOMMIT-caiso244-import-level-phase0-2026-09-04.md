# PRECOMMIT — caiso-244: the `IMPORT_TRANCHES[CAISO]` LEVEL object, Phase 0 — MEASURE, DO NOT ARM. Pushed BEFORE the object is measured and BEFORE any LP.

**Session caiso-244, 2026-09-04. Branch `claude/caiso-244-backcast-calibration-jag23e`
(off `main` `8f5cb32c`).** Keeper at open: **`2026-09-04-caiso-243-b1-f923`**
(`results/calibration/caiso243_b1_f923_fallback_guard`, `git_sha b053e3b8`),
**NOT-YET**, ONE load-bearing FAIL — C3a **+3.9 / +12.3 / +14.4 %** (2023
PASSES; required move to the ±10 % band +3.297 / −0.805 / −1.498 $/MWh); C1 12/12
free 8/8; C2 / C3b / C4 PASS; C3c the single ledgered caveat (non-downgrading);
C6 attested; C8 PASS; `audit_keepers --iso CAISO` PASS 0/0; DOF ledger 9 entries
/ 6 residual. CAISO holds **no `complete` and no `final` marker**; the holdout
spend freeze is **ACTIVE**; every read and every rebuild below stays inside
**2023–2025**.

---

## §0 — WHAT THIS SESSION IS

### §0.1 — Two instrument repairs came first, and are DONE (this branch, commit `58327a62`)

The handoff owed two repairs before any new measurement; both are on this
branch ahead of this file:

1. **The by-name recipe pattern is RETIRED structurally.**
   `scripts/replay_keeper.run_year_kwargs` is now the ONE sanctioned
   `meta.json → run_year(fleet_only=True)` reconstruction: it goes through the
   strict, remapping `build_kwargs` and keeps exactly the subset
   `solve_and_persist` hands `run_year`, under the names `solve_and_persist`
   uses in its own call (`commitment → commitment_enabled`,
   `screen_coal → commitment_screen_coal`). `run_year_unreachable` discloses
   the recorded non-default solve kwargs a fleet-only rebuild cannot carry
   (post-LP overlays, `btm_backfill_year`, `strict_demand_profile`).
   `scripts/lib/bundle_fleet.full_run_year_kwargs` — the pjm-124 helper the
   CAISO lane never used — now delegates to it. **Measured before the switch,
   on all six designated keepers (zero LP):** the by-name pattern drops
   `prb_overrides` on EVERY ISO (36 / 50 / 18 / 42 / 35 / 5 flags on CAISO /
   ERCOT / PJM / MISO / NYISO / NEISO) plus `coal_bit_sigmoid` and
   `bit_overrides`; the pjm-124 helper and the strict path agree on every
   recorded key up to `None` vs `{}` on empty override dicts, which `run_year`
   treats identically. The caiso-243 probes' inline helper is a thin wrapper;
   caiso-242's four probes are rewired and write `_caiso244_*_onrecipe.json`
   (the `_caiso242_*.json` artifacts stay frozen as the record).
   `tests/regression/test_run_year_kwargs_recipe.py` pins the remaps, the
   agreement, the disclosure, and confines the retired pattern to an explicit
   frozen-record allowlist of nine pre-caiso-244 probes — a tenth fails CI.
2. **caiso-242's four probes are re-running on-recipe** against the caiso-243
   keeper as this is written (three of four complete). The one result already
   read is disclosed in §0.2 because it conditions nothing below.

### §0.2 — FULL DISCLOSURE: everything already read or measured before this push

**Read:** caiso-243 finding + precommit + addendum; caiso-242 §2–§10;
caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9 (DO-NOT-REDO, in full);
the caiso.md tail caiso-232 → caiso-243 (caiso-232 defect 2, caiso-233/234/235
— the depth lane's three refused estimators and its CLOSURE); caiso-188 §1–§4
(the six-scalar census on the built fleet, the ceiling stack, the 7,500 MW seam
pin); caiso-229's "inert by construction" row; the CAISO matrix shard's
`import_hub_pricing` cell; `keepers/CAISO.json`; the keeper's `meta.json`,
`run_config.json`, `metrics.json`, `legitimacy_diagnostics.json`,
`calibration_attestation.json` (DOF ledger) and `hourly/` sidecars;
`model/interchange/{spec,caiso,import_nodes}.py`, `data/eia930/envelopes.py`,
`scripts/data/derive_caiso_import_tranches.py`, `config/iso_configs.py` (CAISO
links / interface), the `ScenarioConfig` docs of every `caiso_*import*` /
`caiso_per_hub*` / `caiso_corridor*` field.

**Measured (zero LP, incidental to reading, NOT this object's instrument):**

| quantity | value | source |
|---|---|--:|
| keeper `class_hourly` `import` klass, annual | **37.27 / 40.02 / 41.24 TWh** (2023/24/25); hourly min 0.0, max 9,631 / 9,169 / 10,546 MW | committed sidecar |
| keeper D-2 `firm_import` forced energy | **17.94 / 22.68 / 22.49 TWh** (50.4 / 55.5 / 56.3 % of a D-2 class total of 35.56 / 40.88 / 39.98 TWh) | committed `legitimacy_diagnostics.json` |
| EIA-930 CISO net interchange by DIBA, summed over the 11 corridor DIBAs, RAW local-time year (NOT the model clock) | ≈ **28.9 / 31.4 / 35.9 TWh** net import; PNW corridor (BPAT+PACW+BANC+TIDC) ≈ **−0.55 / +2.06 / +4.72**, DSW (AZPS+SRP+WALC+NEVP+IID+LDWP+CEN) ≈ **29.4 / 29.4 / 31.2** | `data/raw/eia-930-interchange/CISO interchange hourly.parquet` |
| the same raw print also showed the 2019–2022 and H1-2026 annual DIBA sums | **read incidentally, quoted nowhere, used for nothing.** No model output exists for those years; nothing is scored. Disclosed because the rule is that the SCORE is held out, and an annual sum of a measured input is not a score — but it was seen. | — |
| on-recipe caiso-242 §3 re-measurement (instrument repair 2, first probe) | ratio model-gas ÷ derive-citygate **1.078 / 1.223 / 1.192** (voided: 1.298 / 1.310 / 1.327); diff **+0.41 / +0.55 / +0.59 $/MMBtu** | `_caiso244_gas_basis_identity_onrecipe.json` |

**Not yet measured, and therefore the subject of §3's predictions:** the
model's import by CORRIDOR and by ROW (tranche), its hourly location, the
forced-vs-economic split of the excess, the price relationships of the
economic slice, the export legs' energy, the import-marginal hour count, the
December-2025 anatomy, and the measured corridor series ON THE MODEL CLOCK.

### §0.3 — Why this object, from the queue, and why PHASE 0 ONLY

Handoff item A. caiso-243 P-5's falsified leg — the repaired 2.4 GW of domestic
gas displaced **0.473 TWh of imports against a 0.442 TWh CC_REGULAR rise** — is
the first measurement of the displacement caiso-242 §2.4 predicted, and it
lands on the standing `IMPORT_TRANCHES[CAISO]` residual, not on a repair.
caiso-238 fixed the shape of any funded work: **the LEVEL object; the depth
lane is CLOSED** (caiso-233/234/235: three pre-registered estimators refused,
`spot_capacity` CLOSED AS NOT IDENTIFIABLE from EIA-930 seam flow on a
2022/2023 regime break). caiso-188 measured the six scalars' LIVENESS and the
corridor CEILING stack; **no session has measured where the model's import
ENERGY sits relative to the measured corridor flows, row by row and hour by
hour.** That is the level question, and it is answerable with ZERO LP from the
committed keeper (§2). Phase 0 measures and locates; it arms nothing, solves
nothing, registers nothing (rule 15 does not attach — no run is produced).

### §0.4 — HARD STOPS

No LP. No `ScenarioConfig` field. No arm. No value chosen. Training window
only; no `calibration-complete.json` / `holdout-freeze.json` / other-ISO shard
or bundle touched. Rule 25: every number is CAISO's; the shared helper of §0.1
is ISO-generic infrastructure that changes no ISO's recipe (measured, §0.1).
**The depth lane is not re-opened** — no estimator for the four spot capacities
is run, proposed or scored; DO-NOT-REDO caiso-233 §F, caiso-234, caiso-235 §6
are honoured in full. **The seven `R`/`I`/`G` CAISO cells are not re-tested.**

### §0.5 — THE HAZARD, STATED BEFORE MEASURING

This is a measurement; it moves no gate. But if §3 P-3 holds, the repair it
would motivate (less FORCED cheap import) raises the domestic gas share in the
displaced hours and moves λ **UP** — **ADVERSE to C3a**, the sole failing gate,
in a lane whose last three repairs each moved C3a favourably. Stated now so
that the direction can be neither an argument for nor an argument against
whatever the owner later decides (rule 1 `[R-STRUCT]`); the caiso-151 clip was
E1-ADVERSE ex ante and was promoted on structure, which is the precedent.

### §0.6 — DO-NOT-REDO ACKNOWLEDGED (rule 28(a))

Not re-opened, re-proposed or used: CT_PEAKER availability; the band-order
inversion; caiso-242's P-1 and §H‴; `nearby_fuel_price_zone_donor_guard` as a
CAISO lever; form (b); G-CTRL form 4; caiso-229 / caiso-230 (untouched);
`CT_PEAKER.committed`; the measured BID committed multipliers; any cross-ISO
transfer; EIA-930's CISO NG cell (this session reads the INTERCHANGE product,
`TI` family, never the NG generation cell); `_DEFAULT_HR_MULT_BY_GROUP`; the
five gas `mr` literals; `ST_GAS:econ`; the W-1/W-2/W-3 sweep (dated
≤ 2026-12-01); zonal congestion / Path-15 as a C3a instrument (caiso-230 §9.2).

---

## §1 — THE OBJECT, LOCATED IN CODE (nothing here is new; it fixes the vocabulary)

The keeper's CAISO seam (`run_config.json`): `caiso_per_hub_intertie` (two
signed corridors, WECC_PNW = COI/Malin → NP15, WECC_DSW = Path-46/Palo Verde →
SP15_rest), `caiso_perhub_firm_base`, `caiso_firm_import_shape`,
`caiso_firm_import_selfschedule`, `caiso_firm_import_envelope_clip`,
`caiso_firm_import_selfsched_clip`, `caiso_corridor_flow_limit`,
`caiso_asymmetric_path_ratings`, `caiso_per_year_import_caps`,
`caiso_dsw_{surplus,overnight,daytime}_clean` (+ `daytime_evening_trim`),
`capacity_deliverability_limits`. Import rows on the built fleet (caiso-188 §2):

| row | capacity | price | limb (caiso-188) |
|---|---|---|---|
| `PNW_hydro_base`, `DSW_solar_PV` | DMM RA-import capacity × MIC north/south split (1,072/1,558/1,566 · 1,251/1,813/1,805 MW), shaped by the measured (month × hod) median of corridor net import, clipped at the corridor p95 envelope; **floored (self-schedule) at min(capability, measured price-insensitive ceiling)** | **$28 / $48 fitted** (2 of the 6 scalars) — inframarginal bookkeeping AT the floor, **price-gating above it** (the caiso-151 clip leaves an elastic slice; caiso-188 §2 reading 1) | firm |
| `PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity` | **1,800 / 1,800 / 2,200 / 3,000 = 8,800 MW fitted** (4 of the 6), `RESIDUAL`, DOF closed as not identifiable | measured hub (Malin / Palo Verde) + OATT wheel + CARB border × EF ladder — measured | spot |
| `DSW_{surplus,overnight,daytime}_clean` | measured depth (caiso-87/93/94) | raw Palo Verde hub, EF 0, no wheel | clean depth |
| `EXPORT_<hub>` per corridor | −(published link rating) | hub − ε | export leg |

Ceilings: the corridor import link is capped at the measured p95 envelope
(operative in 25,866 / 26,280 corridor-hours, caiso-188 §3); the aggregate seam
at the published MIC (16,055 / 16,452 / 16,148 MW) when
`capacity_deliverability_limits` Part A resolves — **and on THIS keeper it
did**: `class_hourly` import peaks at 9,631 / 9,169 / 10,546 MW, never the
7,500 MW pin caiso-188 §4 found on the caiso-175…184 lineage.

**The LEVEL question, stated once:** the model's annual net import runs
~8.4 / 8.6 / 5.3 TWh above the measured corridor sum (§0.2, raw-clock; the
probe re-measures on the model clock). **Which rows carry that excess, in
which hours, and is it FORCED (a floor) or ECONOMIC (an offer below the
zone's dual)?** Until that is measured, "the import level object" names a
residual, not a mechanism.

---

## §2 — THE INSTRUMENT: row-level import dispatch reconstructed from the keeper's own duals, zero LP

`scripts/probes/_caiso244_import_level_anatomy.py` →
`results/calibration/_caiso244_import_level_anatomy.json`.

1. **Rebuild the keeper fleet on-recipe** for each year through
   `replay_keeper.run_year_kwargs` (§0.1 — the first CAISO probe to run on the
   repaired instrument by construction). From the fleet-only state take, for
   every import row (zones WECC_PNW / WECC_DSW): the assembled offer `c[r,t]`
   (`mc_base`, hub + wheel + carbon as injected), capability
   `u[r,t] = pmax × availability`, floor `f[r,t] = min_gen` (0 where none), and
   the export legs' `pmin`.
2. **Read the keeper's committed P1 zonal duals** `λ[z,t]` from
   `hourly/system_<year>.parquet` (WECC_PNW, WECC_DSW, NP15, SP15_rest) and the
   `import` klass from `hourly/class_hourly_<year>.parquet`.
3. **LP complementarity, row by row:** an import row with `c < λ_z − tol` is at
   `u`; with `c > λ_z + tol` at `f`; within `tol` it is MARGINAL and takes the
   residual that closes the hour's class total (residual split pro rata across
   marginal rows when more than one, and those hours COUNTED). An export leg
   with `hub − ε > λ_z + tol` is at full export; `< λ_z − tol` at 0.
   `tol = 0.05 $/MWh` (the injector's own `CAISO_INTERTIE_TIEBREAK_EPS` is
   1e-3; 0.05 absorbs float noise in the persisted duals and is reported, not
   tuned).
4. **Self-consistency gate G-RECON (the instrument's own falsifier):** the
   reconstructed hourly sum over import rows (with the export legs netted and,
   separately, not netted) is compared to the committed `class_hourly`
   `import` series. The basis that matches identifies whether the klass NETS
   the export legs. **PASS iff the matching basis reproduces the annual energy
   within 1 % and the hourly series with RMSE < 100 MW in every year.**
   FAIL ⇒ the reconstruction is not the keeper's dispatch, NO row-level
   attribution is claimed, and the session records that a unit-level replay
   (~75 min) is the only remaining instrument — as an owner ask, not taken.
5. **Measured side on the model clock:**
   `derive_caiso_import_tranches.corridor_net_import((2023, 2024, 2025))` —
   the committed producer (EIA-930 CISO ↔ DIBA, `CAISO_CORRIDOR_DIBA`, the
   `_caiso_interchange_model_clock` lag repair), hourly per corridor.
6. **Outputs:** per year × corridor × row: energy (TWh), energy at floor, at
   capability, marginal, hours in each state; corridor model vs measured net
   import annual / monthly / hod; the excess `model − measured` per corridor;
   the economic slice's spread anatomy (`λ_CAISO-zone − c`, the CAISO price vs
   the cheapest AVAILABLE domestic gas offer in the same hour); import-marginal
   hours; December-2025 anatomy; the two firm rows' price-live hours.

Nothing here is a fit. Every number is read from committed bytes or from the
on-recipe rebuild of the committed recipe.

---

## §3 — PREDICTIONS, REGISTERED BEFORE THE PROBE IS WRITTEN

Written to be **uncomfortable**: P-2, P-3, P-5 and P-7 each cut against a
standing reading of this object; P-1 is the instrument's own kill switch.

| # | prediction | falsified by |
|---|---|---|
| **P-1** (G-RECON) | the dual-merit reconstruction reproduces the committed `import` klass to **≤ 1 % annual energy and < 100 MW hourly RMSE** in every year, on ONE of the two bases (net / gross of exports) | either bound exceeded in any year ⇒ no attribution claimed |
| **P-2** (corridor) | the model−measured net-import EXCESS is **larger on the PNW corridor than on the DSW corridor in every year** | DSW excess ≥ PNW excess in any year |
| **P-3** (forced) | the **`PNW_hydro_base` FLOOR energy alone exceeds the ENTIRE measured PNW corridor net import by ≥ 4 TWh in every year** — i.e. the DMM-RA-capacity × MIC level, forced as ENERGY, is not an energy the corridor carried | margin < 4 TWh in any year |
| **P-4** (firm prices live) | the two firm rows dispatch **strictly between floor and capability** (the price-gated elastic slice of the caiso-151 clip) in **≥ 10 % of hours in 2024 and in 2025** — caiso-188 §2 reading 1 holds and caiso-229's "INERT BY CONSTRUCTION" does not, on this keeper | < 10 % in either year |
| **P-5** (spot ladder) | the four fitted spot rows together carry **< 25 % of model import energy** in every year, and `WECC_scarcity` dispatches in **< 1 % of its capability-hours** | ≥ 25 %, or ≥ 1 % |
| **P-6** (import-marginal) | hours in which an import row is MARGINAL at its WECC zone AND the corridor link is unbound (λ_WECC = λ_CAISO-zone within tol) are **< 5 % of hours** in every year (caiso-202 §C's direct-marginal acquittal re-measured on this keeper) | ≥ 5 % in any year |
| **P-7** (December) | in **Dec-2025** the ECONOMIC import (spot + clean-depth rows in merit) exceeds the FORCED import (firm floor energy) — the caiso-232 December level slab is an economic-import phenomenon, not a forced one | economic ≤ forced in Dec-2025 |
| **P-8** (exports) | the export legs carry **< 0.5 TWh in every year** (the per-hub "Palo Verde reverses to export midday" design is quantitatively small on this keeper) | ≥ 0.5 TWh in any year |

---

## §4 — WHAT COUNTS AS A RESULT, FIXED NOW

* **G-RECON is the only gate.** It gates whether §3 P-2…P-8 are scored at all.
* Each of P-2…P-8 is scored HOLDS / FALSIFIED at full magnitude. A falsified
  prediction is reported as such; **nothing is re-scoped after seeing which
  half of a quantity passes.**
* **The deliverable is an ATTRIBUTION, not a repair**: which rows and which
  mechanism carry the excess, at what spread, and which of the six fitted
  scalars (or which non-fitted mechanism) the level actually sits on. If the
  attribution lands on the firm FLOOR's energy basis (P-3), the candidate forms
  are enumerated for the owner with their admissibility and their C3a direction
  (§0.5) — **none chosen, none armed, none solved.**
* If the attribution lands on the spot ladder (P-5 falsified), the finding
  records that the closed depth lane is where the level sits and STOPS: no
  fourth estimator (caiso-235 §6 closure).

---

## §5 — OWNER ASKS ANTICIPATED (none presumed)

1. A **replay** of the keeper (unit-level dispatch) if and only if G-RECON
   fails.
2. The **form** of any firm-floor energy-basis repair, if P-3 holds.
3. Everything caiso-243 §9 carried, unchanged: D3 (55077's own row), the 2025
   overlay coverage gap, PJM/MISO exposure, the DOF-provenance instrument (this
   session's helper does not touch `_count_scalars`).
