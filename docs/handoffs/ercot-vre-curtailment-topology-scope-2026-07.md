# ERCOT wind/solar curtailment — topology-refinement scope (2026-07-07)

**Purpose.** Scope the two forward-admissible fixes for the ERCOT VRE
under-curtailment localised in step 2
(`docs/handoffs/ercot-vre-undercurtailment-step2-2026-07.md`): (A) a
West/Panhandle **zone split** and (B) a **derived curtailment-share driver**.
Re-scoped now that two things changed since the Far_West split was built and
reverted (`docs/ercot-far-west-zone-split-2026-06.md`):

1. **The NP6-86 SCED binding-constraint archive is now in the repo**
   (`data/raw/iso-specific-transmission/SCEDBTCNP686_*_{2020..2025}.parquet`,
   plus `xhr`/`retry` variants) — the measured-limit source the Far_West doc
   said was *"not present in this environment."*
2. Zone-assignment metadata is confirmed present and is **two tables**, not one:
   the CAMPD-binned thermal fleet carries a hard-coded `ERCOT_Zone` column in
   `data/raw/reference/custom-bin-assignments.csv`
   (`zone_assignment.load_reference_zone_crosswalk`); renewables + everything
   else are sited by EIA-860/eGRID **lat/lon + FIPS county**
   (`zone_assignment._oris_to_location` → `_ercot_zone`).

## The decisive evidence from the new NP6-86 data

Binding frequency by constraint, 2024 (`ShadowPrice > 0`, 103,691 SCED
intervals, 739 distinct constraints):

| constraint | binds % of intervals | median limit MW | maps to model link? |
|---|---|---|---|
| PNHNDL | 12.1% | 3,239 | **yes** — Panhandle→North (2,680) |
| NE_LOB | 11.0% | 1,260 | **yes** — Northeast→North (1,300) |
| WESTEX | 10.7% | 10,275 | **yes** — West→North + West→SC (7,300+2,700=10,000) |
| BURNS_RIOHONDO_1 | 9.9% | 186 | no — single 138 kV line |
| 6520__E, ZAPSTR, HAINE_LA_PAL1, LARDVN_LASCRU1, DILLEYSW … | 3–9% each | 30–500 | no — station-to-station nodal |
| VALEXP (Rio Grande Valley) | 4.5% | 531 | no — intra-zone pocket |

Two facts settle the design:

1. **The three interface GTCs that map to the wind corridor — WESTEX, PNHNDL,
   NE_LOB — are ALREADY modeled, at their measured limits.** WESTEX's measured
   median 10,275 MW ≈ the model's 10,000 MW West export; PNHNDL 3,239 ≈ 2,680;
   NE_LOB 1,260 ≈ 1,300. `curate_gtc_limits.py` keeps only these interface GTCs
   (empty `FromStation`) and `ERCOT_GTC_LINK_MAP` already wires all three. There
   is **no additional interface-scale GTC** behind which the West/Panhandle wind
   sits — a zone split cannot introduce a binding interface that is not already
   present. This is why ercot39 (measured aggregate GTC) and step 2 both found
   transmission on the 8-zone topology is not the binding lever.
2. **The chronic curtailment lives in the station-to-station tail.** Reported
   wind curtailment is active in 66–90% of ALL hours (step 2); the interface
   GTCs bind only ~11–12%. The residual is the long tail of **single-element
   nodal constraints** (BURNS_RIOHONDO, LARDVN_LASCRU, DILLEY, the numbered
   `NNNN__X` lines, VALEXP…), each a specific 138/345 kV line with a 30–500 MW
   limit. These are structurally below zonal resolution: representing them as
   zonal links would require hundreds of zones, and each caps one line, not an
   interface.

**Conclusion up front:** the new TTC data does **not** unblock the zone split
(the interfaces it measures are already in the model) — it unblocks the
**derived driver** (it supplies the measured binding-frequency identification
source rule 21/23 requires). WP-B is the higher-value use of the import; WP-A is
scoped below for completeness and as honest structure, but its expected yield on
the chronic gap is ~zero on this evidence.

---

## WP-A — West/Panhandle zone split (scoped; low expected yield)

Rebuild the reverted Far_West node and, optionally, a CREZ wind sub-zone. The
recipe is the NE_LOB carve-out mirror, fully recorded; the five coordinated
touch-points:

1. **Topology** — `config/iso_configs.py:_ercot_config()`: add
   `Zone(name="Far_West", load_share=…)` (and/or `Zone(name="West_CREZ", …)`),
   cut `West`'s share, add the `TransferLink`s. Use measured WESTEX/PNHNDL from
   the NP6-86 archive; for an asymmetric basin rating use a one-way link pair
   (`is_bidirectional=False`) as commit `aad79c1` did.
2. **Plant/renewable siting** — `data/zone_assignment.py:_ercot_zone()`: split
   the `lon < -99.5` branch (Far_West `lon < -101 & lat < 33.5`; a CREZ pocket
   by the −99.5…−101 / lat band). This re-buckets renewables via the lat/lon
   lookup — **the lever that moves wind capacity into the new zone.**
3. **Thermal siting** — `data/raw/reference/custom-bin-assignments.csv`: set
   `ERCOT_Zone` for the ~13 Permian plants (Permian Basin 3494, Odessa-Ector
   55215, Quail Run 56349, Ector County 58471, C R Wing 52176, …) — the fleet
   uses this column, not the heuristic.
4. **Load shape** — `data/eia_loader.py:_ERCOT_LOAD_ZONE_GROUPS`: map `FWEST`
   (and any CREZ split) to the new zone; re-run
   `scripts/data/derive_load_shares.py ercot` so all shares re-derive from NP6-345 and
   sum to 1.0. **Fix the two open bugs in that script first** (Far_West doc §
   disposition): its `REF` path predates the W1 `data/reference` →
   `data/raw/reference` move, and its weather-zone map still sends `EAST → North`
   though the live model carved EAST into Northeast — so it currently cannot
   reproduce the committed Northeast share.
5. **Gas basis** — `data/raw/ercot_zonal_gas_hub.csv`: add `Far_West = Waha` (and
   CREZ = Waha) so the new zone doesn't fall back to a default.

**Expected yield: ~none on the chronic gap.** The measured WESTEX limit ≈ the
model's existing West export, so the split relocates load/gen behind the *same*
non-binding interface — the exact copper-plate no-op that reverted Far_West,
now provably so from the data. It captures only the ~11% of curtailment the
interface GTCs already explain. **Risk:** a zone change is Tier-0 — it changes
`n_zones`, the LP column layout, and every cross-scenario/keeper comparison
baseline. Not worth carrying inert.
**Effort:** ~1–2 days to rebuild + the derive-load-shares bug fixes; validation
across all three years. **Recommendation: defer** unless paired with WP-B or a
future *intra-corridor* interface limit that binds tighter than WESTEX (none
exists in the current archive).

---

## WP-B — Derived curtailment-share driver (recommended; now identifiable)

A forward-admissible curtailment share applied to West/Panhandle wind (and
midday solar), in the WS-A mould
(`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §4). **The NP6-86 archive is
what makes this legitimate now** — it supplies the measured identification
source rule 21/23 demands.

**Design.**
```
curt_share_c(t) = f( net_load_pct(t), hour_of_day(t), season(t) )   for c in {West/Panhandle wind, solar}
```
applied as a ceiling on the zone's VRE dispatch (a real, forward-regenerating
congestion probability — more West VRE build → deeper troughs → higher share;
more takeaway → lower), **never** an additive volume/price adder.

**Identification source (the new unlock, DOF-ledger entry).** Fit the shares to
the **measured NP6-86 congestion incidence in the West/Panhandle**, NOT to the
curtailment volume or price residual:
- Interface layer: WESTEX + PNHNDL binding frequency per (net-load percentile ×
  hour × season) — already curated at the GTC level.
- Nodal layer (the new work): aggregate the **station-to-station** binding rows
  (currently dropped by `curate_gtc_limits._gtc_only`) whose `FromStation`/
  `ToStation` sit in the West/Panhandle/CREZ geography into a measured
  "curtailment-pressure frequency." Needs a station → area crosswalk (ERCOT
  publishes station→county/load-zone; the archive carries `FromStationkV` to
  filter to the 138/345 kV lines that curtail wind). This becomes a new curated
  datatype via the `data-intake` contract (schema-first, `write_clean`/
  `read_clean` seam), re-derived only on source-data updates (rule 20/23).

**Anti-residual gate (hard, per rule 13/14/23).** The fitted share must
reproduce, leave-one-year-out on 2023–2025, the measured *binding frequency*
distribution — not the [3e] curtailment volume. A share that only lands the
volume is rejected at the validation script. The share is a function of the
model's own forecast net-load, so it regenerates forward (admissibility #10/#12).

**Effort:** ~3–5 days (curated nodal-congestion datatype + derive script +
`ScenarioConfig` seam + LP ceiling wiring + validation). **DOF ledger + zero-
forcing ablation twin required before any keeper (rule 21).**

---

## Recommendation & sequencing

1. **Do not lead with the zone split.** The new TTC data proves the wind-corridor
   interfaces are already modeled at measured limits; WP-A is a Tier-0 change with
   ~no yield on the chronic gap. Keep the recipe on the shelf (this doc + Far_West
   doc) for the day an intra-corridor interface limit tighter than WESTEX appears.
2. **Build WP-B.** It is the only route that can represent the sub-zonal nodal
   congestion driving 66–90%-of-hours wind curtailment, and the NP6-86 import now
   gives it a clean, forward-admissible identification source (measured binding
   frequency), keeping it clear of the rule-13 measured-outcome-pinning line.
3. **Guardrails hold throughout** (CLAUDE.md #1/#13/#14, step-2 §): no HSL pin, no
   residual-tuned curtailment adder, no GTC re-probe; the driver is fit to
   measured congestion frequency, never to the price/volume residual; DOF ledger
   + ablation twin before any keeper; all three in-sample years in one bundle
   (rule 16); holdouts 2022/H1-2026 untouched (rule 22).

**Owner decision needed:** approve WP-B (derived driver) as the next build, or
request WP-A rebuilt as inert structure anyway. Either way the level fix does not
proceed to a keeper without the DOF ledger and owner sign-off.
