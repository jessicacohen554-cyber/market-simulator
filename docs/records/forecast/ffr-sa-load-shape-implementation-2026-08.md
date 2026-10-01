# FFR-SA — FF-G4 Option-B load-shape implementation (2026-08-03, DEFAULT OFF)

**Session.** FFR-SA (Fable), implementing the DECIDED design of
`docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md` (§8-D1 = **Option B —
additive end-use layers**; charter: implement, do not re-design). Branch
`claude/ff-g4-load-shape-mzfsgg` off `origin/main` 5e934b8 (2026-08-03).
Closes the *mechanism* half of audit **FR-16**; the *posture* half (arming) is
the owner box in §5, untouched here (no default flip, per charter).

---

## 1. What landed

- **Config surface (rule 24).** `ScenarioConfig.electrification_path`
  (`"off"|"low"|"mid"|"high"`, **default `"off"`**) +
  `electrification_percentile` (neutral 0.5) — the exact
  `datacenter_load_path`/`datacenter_percentile` grammar (the memo §5.1
  master-gate + shared-path recommendation collapsed onto the on-main
  one-field pattern the memo itself cites as the precedent). Both echo to
  `run_config.json` via `asdict`; both registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` (pinned default cache_key `603c2498bf71d21d`
  UNMOVED — measured) and `TIER_TAGS` (tier 2).
- **Backcast/hindcast coercion.** `__post_init__` validates the label and
  coerces the path to `"off"` in `mode=="backcast"` or `hindcast=True` — the
  FF-1F DC pattern verbatim; `data.datacenter.validate_electrification_config`
  is the standalone defense-in-depth mirror.
- **Adoption anchors (rule 5/13).** `constants.ELECTRIFICATION_LAYERS`
  `{iso: {layer: {path: {year: GWh}}}}`, incremental to the weather-year base.
  Populated TODAY: **NEISO `heat_pump` mid `{2026: 0, 2035: 7165 GWh}`**
  (ISO-NE 2026 CELT Heating Electrification Forecast; the companion 5,533 MW
  winter-peak figure is reconciliation CONTEXT, never a target). Every other
  cell ships `{}` with its reason documented in place (bot-walled M11 PJM
  tables; NYISO peak-MW-only; CAISO CED-hourly intake pending; MISO LTLF
  intake pending; ERCOT no decomposition). `ev` ships `{}` in EVERY ISO — see
  §6.
- **Heat-pump profile (physics, weather-aligned).**
  `data.datacenter.heat_pump_layer_profile`: hourly heating-degrees
  `max(0, 18.3°C − T(h))` (65 °F NOAA/EIA degree-day base,
  `constants.HEAT_PUMP_BALANCE_POINT_C`) on the run weather year's measured
  NOAA GHCN daily zone-mean TMIN/TMAX, bridged to hourly by the on-main
  Parton & Logan (1981) reconstruction
  (`data.eia930.weather.diurnal_drybulb_from_daily` — the miso-101 mechanism;
  rule 19, one reconstruction). Normalized to Σ=1. Winter-morning ridge
  EMERGES from the temperature series (NEISO 2024: January hour-of-day peak
  at h5 — consistent with CELT's "winter peaks migrate to morning").
- **Unified fold-in (rule 19).** `data.datacenter.add_load_layers` replaces
  `add_datacenter_block` at BOTH runner seams: the DC block is layer #1,
  folded jointly with the electrification layers under one relocation and one
  sum-of-layers (tail-regime) guard. **DC-only path is BIT-IDENTICAL to the
  legacy function (tested)**, so the armed `datacenter_load_path="mid"`
  forecast default — the Wave-3 baseline — rides through unchanged.
  `add_datacenter_block` remains as a documented DC-only entry point (never
  call both).
- **Fail-closed profile registry.** A layer with populated anchors but no
  registered profile builder raises at fold-in; a standing test
  (`test_every_populated_layer_has_a_registered_profile_builder`) keeps
  anchors and profile sources from drifting apart.
- **Probe arm.** `run_full_horizon.py --electrification-path {off,low,mid,high}`
  (default off). Matrix row `electrification_layers` added in the same PR
  (rule 28c).
- **The CX-4 zero stub is deleted** (`electrification_shape`, rule 26
  [R-DELETE]) — superseded by the real machinery it deferred to.

## 2. The DC double-count seam (rule 19 — the load-bearing constraint)

What already shapes demand at this seam, enumerated:

1. `_scale_demand` — the flat compound growth scalar; the near-era
   `DEMAND_GROWTH_RATES` are **TOTAL** (DC- **and** electrification-inclusive:
   the CAISO comment says so explicitly, and CELT/Gold-Book totals embed HEF/
   TEF by construction).
2. `add_datacenter_block` (now layer #1 of `add_load_layers`) — relocates the
   DC energy already inside that total onto a flat shape.
3. The FF-G4 layers (this session) — relocate the electrification energy
   already inside that total onto each layer's own shape.

**Reconciliation:** one fold-in, joint algebra. With `E` = grown total energy
and `E_i` the layer energies, `demand := demand × (1 − ΣE_i/E) + Σ layerᵢ`.
Every layer relocates **its own** energy exactly once out of the same grown
total; the layers are **disjoint end-uses** (DC servers ≠ EV charging ≠ space
heating), so no MW is claimed twice — the DC block's MW never appears in an
electrification trajectory (ISO-NE CELT's HEF/TEF are heating/transport
components, disjoint from large-load/DC adjustments by the source's own
decomposition; NEISO's DC block is `{}` anyway). The tail-regime guard is
shared: if `ΣE_i ≥ E` the layers are genuinely incremental and add on top.
Energy invariance in the relocate regime is tested to machine precision.
No second mechanism floors/shapes the same phenomenon: the weather pool
(`weather_year`) spans weather variability, not structural shape change
(memo §4.3 rejection of Option C stands).

## 3. DOF ledger additions (rule 21 — memo §7 pinned)

| Parameter | Identification source | Open DOF? |
|---|---|---|
| `ELECTRIFICATION_LAYERS["NEISO"]["heat_pump"]["mid"]` | ISO-NE 2026 CELT HEF 7,165 GWh @2035 (memo §2.2 [F]) | No — cited; re-derives on vintage only (rule 23) |
| `HEAT_PUMP_BALANCE_POINT_C` = 18.3 °C | NOAA/EIA 65 °F degree-day standard | No — frozen physical input |
| heat_pump hourly profile | measured GHCN weather × Parton-Logan bridge (on main) | No — physics; regenerates per weather year |
| Zone allocation (load_share) | `iso_configs` load shares (no published per-zone electrification split) | Documented limitation, not a knob |
| `electrification_path` default | owner posture (§5 box) | **Owner** |
| ev layer profile | — | **Open blocker (§6), NOT a parameter** |

No parameter is identified from a model residual. A shape residual that
survives sourced layers routes to L-INP as a finding, never a profile edit.

## 4. T0 smoke (NEISO → PJM, 2026–2028, armed vs off)

Run dirs: `results/ffr-sa-smoke/{neiso,pjm}-{off,mid}` (summaries committed).
Solve slots honored (rule 12): all four legs strictly SEQUENTIAL, one
invocation at a time.

**NEISO 2026–2028, off vs `--electrification-path mid`** (3/3 years each,
~5 min/leg, distinct cache keys `9ff63395d1c39726` / `2dd851fb5010a74d`):

| yr | peak_demand off→mid (MW) | reserve_margin off→mid | lw_price off→mid | CO₂ off→mid (Mt) |
|---|---|---|---|---|
| 2026 | 24,890 → 24,890 (=) | 0.153 → 0.153 (=) | 52.13 → 52.13 | 16.32 → 16.32 |
| 2027 | 25,213 → 25,044 | 0.198 → 0.206 | 49.41 → 49.40 | 16.56 → 16.58 |
| 2028 | 25,541 → 25,203 | 0.201 → 0.217 | 50.76 → 50.76 | 14.09 → 14.09 |

2026 is IDENTICAL by construction (the layer's near anchor is 0). From 2027
the armed annual (= summer) peak falls as HP energy relocates into winter, and
the reserve margin rises accordingly; prices/CO₂ move negligibly at these
horizons. **Invariants: no status delta armed-vs-off.** Both legs carry the
SAME single FAIL — I12 reserve-margin band (2026 15.3 % vs [0.2, 15.2] band,
widening with the entry backstop by 2028) — and the off leg is bit-identical
to the pre-FFR-SA baseline config, so I12 is an INHERITED baseline property
of the NEISO forecast reference posture, not this mechanism (armed moves RM
+0.8/+1.6 pp further above the band in 2027/28 via the lower summer peak —
reported, not hidden).

**Winter-peak expressibility (the FR-16 acceptance, demand-seam measured —
the summary trajectory is season-blind, memo §6's per-season rows remain a
proposed follow-up):** system winter/summer peak ratio, off vs mid:

| yr | off | mid |
|---|---|---|
| 2026 | 0.7607 | 0.7607 |
| 2027 | 0.7607 | 0.7706 |
| 2028 | 0.7607 | 0.7817 |
| 2030 | 0.7607 | 0.8035 |
| 2035 | 0.7607 | 0.8581 |

Off, the ratio is FROZEN forever (the FR-16 defect). Armed, winter-peak CAGR
2026–2035 is ~1.9 %/yr against ~0.75 %/yr off — the trajectory is now
EXPRESSIBLE and driver-caused. CELT CONTEXT (never a target): winter
+2.6 %/yr, winter>summer by 2035/36. The armed model undershoots and does not
flip by 2035; the divergence is explained, not nudged (FC-5 discipline):
(a) the EV layer — 1,509 MW of CELT's 2035/36 winter peak — ships `{}`
pending its profile intake (§6.1); (b) linear degree-hours omit cold-climate
COP rolloff (§5 box); (c) CELT's flip is on NET peaks (BTM solar suppresses
summer), a channel this model carries elsewhere.

**PJM 2026–2028 armed vs off (FFR-SA-close, 2026-08-04 — the owed §2 half):**
the assembled demand arrays are BIT-IDENTICAL — `ARMED==OFF` measured exactly
at the runner's demand seam (sha256 over the assembled `(n_zones, T)` array,
runner-exact reconstruction incl. the external-node topology): equal in
2026/2027/2028 and in the 2030/2035 seam-only context years — because PJM
ships `{}` anchors, the honest no-op the memo designed. Both legs then solved
end-to-end (strictly sequential, rule 12; ~10-11 min / 8.65 GB peak RSS each;
distinct cache keys `c5054dc0d093da2a` / `ced93433f2383d26` — the armed path
enters the key, so neither leg reused the other): trajectories IDENTICAL
through the LP to the last recorded decimal, and **both arms score 14/14
invariants PASS (0 FAIL, 0 WARN) — no armed-vs-off status delta**, and (unlike
the NEISO legs' inherited I12) no baseline FAIL in the PJM probe posture:

| yr | peak_demand off→mid (MW) | reserve_margin off→mid | lw_price off→mid | CO₂ off→mid (Mt) |
|---|---|---|---|---|
| 2026 | 161,027 → 161,027 (=) | −0.094 → −0.094 (=) | 40.11 → 40.11 | 349.09 → 349.09 |
| 2027 | 163,627 → 163,627 (=) | −0.109 → −0.109 (=) | 39.18 → 39.18 | 356.58 → 356.58 |
| 2028 | 166,439 → 166,439 (=) | −0.117 → −0.117 (=) | 40.77 → 40.77 | 374.96 → 374.96 |

System winter/summer peak ratio, off vs mid (demand-seam measured, the FR-16
acceptance metric; 2030/2035 are seam-only context rows, no solve):

| yr | off | mid |
|---|---|---|
| 2026 | 0.8788 | 0.8788 |
| 2027 | 0.8826 | 0.8826 |
| 2028 | 0.8863 | 0.8863 |
| 2030 | 0.8933 | 0.8933 |
| 2035 | 0.8908 | 0.8908 |

Two readings, both required. (1) **Between arms the columns are EQUAL — that
is a DATA-ABSENCE result, NOT inertness** (the FFR-SC §1 discipline:
transmission's PJM rows, same shape). `ELECTRIFICATION_LAYERS["PJM"]` ships
`{}` for both layers because the PJM 2026 Load Forecast component MW-by-year
tables live in the bot-walled report PDF/XLSX (audit row M11). ARMED==OFF is
what an EMPTY input makes the mechanism do by design; it measures NOTHING
about what an armed, SOURCED PJM layer would do, so the matrix PJM cell
records `O` with this citation — never `I`. **MANUAL DOWNLOAD NEEDED: PJM
2026 Load Forecast Report PDF/XLSX (memo §8-D4 item 2 / audit M11)** — the
cell cannot adjudicate until that intake lands. (2) **Across years the ratio
MOVES (0.8788 → 0.8933 by 2030) in BOTH arms identically** — that is the
armed flat DC block (`datacenter_load_path` "mid" forecast default,
`DATACENTER_ADDITIONS_MW`) relocating growing DC energy onto a flat shape:
winter rises toward summer, the load-factor-raising direction PJM actually
publishes (energy +5.3 %/yr FASTER than peak, memo §2.1) — context, never a
target (rule 1). The §2 rule-19 seam is thereby verified OPERATIONALLY, not
just by construction: layer #1 (DC) is live and doing PJM's whole shape story
in BOTH arms, `elec == []` in both arms (`resolve_electrification_gwh` → 0.0
for `{}` anchors), one joint fold-in, each layer relocating its own energy
exactly once, no DC MW ever claimed by an electrification trajectory (disjoint
end-uses; PJM's electrification contribution is exactly zero while `{}`) —
the byte-equal seam output and the identical LP trajectories are the proof.
Leg artifacts: `results/ffr-sa-smoke/pjm-{off,mid}/` (summary + run_config
committed; the per-year LP cache dirs are not).

### 4.1 FFR-SA-close addendum (2026-08-04): PJM keeper byte-identity attestation

The mechanism is default-off and backcast-coerced, so the PJM keeper must be
bit-identical. Attested WITHOUT a re-solve (rule 15: keeper replays are for
unit-level questions), against the CURRENT designated keeper
`2026-08-03-pjm-151-seam-envelope` (`results/calibration/pjm151_seam_B`; the
lane moved the keeper from pjm-147b-chp-heat before this session — nothing
here moved it):

1. **Provenance.** The keeper was solved 2026-08-03T22:47 at sha `1c191624`
   (clean tree) — a commit CONTAINING the FFR-SA merge (`356df4b6` is an
   ancestor) — so its committed bytes were produced with the mechanism present
   at defaults: `run_config.json` echoes `electrification_path="off"` /
   `electrification_percentile=0.5`, `mode="backcast"` (coercion live;
   `datacenter_load_path` backcast-coerced `"off"` likewise).
2. **Cache identity.** Rebuilding the as-solved 2023 config from the committed
   `scenario_config` dump reproduces the recorded per-year cache key
   `abd1cd4a4140496f` EXACTLY at the keeper's recorded sha. Recomputed at this
   session's HEAD (`6040f28c`) the key moves to `ae2aec9c21e06d23` —
   payload-diffed to EXACTLY ONE field, `nyiso_seny_rcpf_increment_step`: the
   keeper solved inside nyiso-119's mid-registration window (field present but
   not yet in `_CACHE_KEY_OPTIONAL_FIELDS`; registration completed by
   `bd6d090a`, restoring drop-at-default). NOT an electrification field, and a
   PJM-lane housekeeping fact rather than a byte-integrity breach: the
   committed bundle and its recorded keys are untouched; the one operational
   consequence is that a `--reuse-solved` against this bundle at HEAD refuses
   conservatively. The electrification fields appear in NEITHER payload
   (registered optional from birth, drop at default at both shas —
   cache-key-invisible at defaults, as designed; pinned default key
   `603c2498bf71d21d` measured unmoved at HEAD).
3. **Seam identity.** At the keeper's exact as-solved config,
   `add_load_layers(year_demand, cfg, "PJM", 2023, zones)` returns the input
   array as the SAME OBJECT (no DC block, no electrification layers in
   backcast) — measured live at HEAD.
4. **Suites.** `tests/unit/data/test_electrification_layers.py` (35, incl. the
   DC-only bit-identity test), `tests/regression/test_persisted_identity.py`
   and the datacenter fold-in suite (38) all green at HEAD.

## 5. OWNER DECISION BOX — arming posture (§8-D2 of the memo; NOTHING flipped here)

**The mechanism ships DEFAULT OFF.** Per-ISO arming is a §2.1a-style posture
decision, evidence-first (the `datacenter_load_path` precedent: landed off,
flipped after T0 evidence):

- **D2-a (recommended by the memo): arm NEISO** (`electrification_path="mid"`
  in the forecast reference posture) once this session's §4 T0 evidence is
  reviewed — NEISO is the sharpest structural test (published winter flip)
  and its heat_pump layer is the one sourced layer today.
- **D2-b: hold everything off** until the ev profile intake (D4-1/D4-7) makes
  the layer family two-legged.
- **D2-c (not recommended): arm more broadly** — inert outside NEISO today
  (every other cell ships `{}`), so this buys nothing and muddies posture.

Known understatement to weigh with D2-a: linear degree-hours omit cold-climate
COP rolloff/resistance backup, so the modeled winter-peak contribution
undershoots CELT's 5,533 MW context figure (profile peak/mean ≈ 4.0 vs the
CELT-implied ≈ 6.9). The refinement channel is a published cold-climate HP
performance curve (D4), never a residual fit.

## 6. What could not be cited (open blockers, NOT parameters)

1. **The EV diurnal charging profile.** No NEISO-specific (or any in-session
   fetchable) hourly charging shape: the ISO-NE TEF PDF
   (`transfx2026final.pdf`) is bot-walled (memo §8-D4 item 1) and the NREL EFS
   profile dataset is a multi-GB manual intake (item 7). The published TEF
   adoption numbers (7,074 GWh; 594 MW summer / 1,509 MW winter @2035) are
   RECORDED in the constants comment for the intake session, but the `ev`
   anchors ship `{}` everywhere — the machinery fails closed if anchors land
   without a profile.
2. **CELT scenario band** for heat_pump low/high (mid-only today; resolver
   collapses low/high onto mid rather than inventing a band).
3. **Per-zone electrification siting** (allocated by load_share, documented).
4. **Post-2035 trajectory** (flat-hold after the last CELT anchor — a
   documented understatement, never an invented extension).

## 7. Scope attestation

- **No default moved; no keeper touched; no backcast solved.** The axis is
  default-off and backcast/hindcast-coerced; the pinned default cache_key
  `603c2498bf71d21d` is measured unmoved; all pinned identity tests pass.
- **Rule 22 held:** solves in this session are forecast-mode 2026–2028 only
  (unrestricted under the holdout freeze).
- Matrix row + citations landed in the same PR (rules 28c, 5); FR-16/FF-G4
  status rows updated in the audit and plan docs.
