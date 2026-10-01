# FINDING — caiso-142: the A3 export-sink seam is **FIXED as infrastructure** (flag-gated, default-off, surgical) but it is **NOT a C3a-2025 lever and cannot be on ANY basis** — an export sink is an **absorption column**, so restoring it can only weakly **RAISE** every zonal λ, while the chartered effect was to push the import-parity plateau **DOWN**. Measured: the export leg sits **below** the plateau's own marginal-import λ by exactly the corridor's OATT wheel + 2ε (DSW defect-hour p50 **+$4.002**, night **+$0.002**), in-the-money in only **0.4–8.4 %** of defect hours; the one indirect channel is dead — the **simultaneous interface group binds in 0 of 26,280 corridor-hours**. D3 KILL before solve: no arm, no A/B, keeper unchanged (2026-07-30)

**Keeper `2026-07-29-caiso139-dump-guard-offer` UNCHANGED** (NOT-YET, fail
{C3a-2025, C3c}). No LP was built, no solver ran, no bundle was produced, no
mechanism was armed. One `ScenarioConfig` field is added
(`caiso_p1_export_sink_seam`, **default False**, byte-identical off, cache-key
registered) because the charter's step 1 orders the seam repaired as
infrastructure; step 2's basis question is answered and step 3's D3 gate
**fails**, so nothing solves. This is the caiso-129/140 kill-before-solve
discipline executing.

Instrument (committed, no LP, no solver):
`scripts/probes/_caiso142_export_sink_basis.py` — §A–§F below. §A exercises the
real `caiso_ra_p1_floor_fleet` / `_bridge_floored_fleet` on the reconstructed
2025 keeper fleet (`run_year(fleet_only=True)`, the caiso-131/134/140
machinery); §B–§E read the keeper's committed `hourly/` sidecars, the committed
actual-LMP reference and the committed EIA-930 interchange frame; §F reads the
other five ISOs' own committed keeper `run_config.json`.

---

## §A — D1: the seam, reproduced on the real functions, and the fix

The 2025 keeper fleet is 1,803 rows and carries exactly **two** `pmin < 0`
absorption rows — the per-hub export legs:

| row | pmin (MW) | pmax |
|---|---|---|
| `WECC_PNW_export_MALIN` | **−4,800** | 0 |
| `WECC_DSW_export_PALOVRDE` | **−10,623** | 0 |

Composing the real RA bridge floor over that fleet:

| | `WECC_PNW_export_MALIN` min_gen | `WECC_DSW_export_PALOVRDE` min_gen | verdict |
|---|---|---|---|
| gate **OFF** (every CAISO keeper since the RA bridge) | **0.0** | **0.0** | range **DELETED** — the LP variable is pinned off (`pmax = 0`, `min_gen = 0`) |
| gate **ON** (the fix) | −4,800.0 | −10,623.0 | range **PRESERVED** |

The fix is surgical, verified on the same call: **2 rows differ, both of them
absorption rows, 0 others**; `availability` byte-identical; and the spurious D-2
attribution is cleared — `MECH_RA_MUSTOFFER` was stamped on **17,520 sink
row-hours** (2 rows × 8,760 h, because the raw floor's 0 does exceed a negative
pmin) and is now stamped on **0**. The mech mask is re-expressed as
`new_min_gen > base_min_gen` (the composed rise, not the raw-floor comparison),
which is identical for every generator row and therefore byte-identical with
the gate off.

The invariant this restores is already written in the codebase, in
`data/fleet/arrays.py::_compose_min_gen_floors`' own zeros-init block: *"export
sinks (pmin < 0, absorption modeled as negative generation) must keep their
range — a zero floor would pin them off"*. `_bridge_floored_fleet` is the one
composition path that did not honour it.

Two consequences beyond the deleted outlet, both new here:

* **P0 and P1 solve structurally different economies** — the detector runs on
  P0, which has live sinks, and the floor rides into a P1 that does not.
* **The RA bridge's own decommit screen credits absorption the scored pass
  cannot use.** `_write_economic_bridge_floors` counts *"unused export-sink
  capacity"* as hourly dispatchable absorption (`model/commitment.py:641-662`),
  i.e. up to **15.4 GW** of headroom, from a P0 solution where the sinks are
  live. The P1 pass it feeds has none of it.

## §B — D2: the export leg is priced **inside** the no-trade band, by construction

`inject_caiso_per_hub_intertie_prices` writes, per hour:

    import leg → hub + wheel + border_carbon × (EF / EF_unspecified) + ε
    export leg → hub − ε

so for the **same** corridor the export price is below **every** import rung by
`wheel + carbon + 2ε ≥ 2ε` in every hour — the injector's docstring states this
as a design property ("each corridor nets to one direction per hour, no MIP").
The measured OATT wheels are `PNW_hydro_base` $2, `PNW_midC` $5,
`DSW_solar_PV`/`DSW_CCGT`/`DSW_CT`/`DSW_surplus_clean` $4, `WECC_scarcity` $6,
and `DSW_overnight_clean`/`DSW_daytime_clean` **$0** (raw-hub WEIM transfer
basis).

Node λ **minus** export price, on the keeper's committed sidecars (positive =
the sink is out of the money, i.e. **inert**):

| year | set | n | DSW p50 gap | DSW in-the-money | DSW marginal rung interior | PNW p50 gap | PNW in-the-money |
|---|---|---|---|---|---|---|---|
| 2023 | defect | 192 | **+4.002** | 8.3 % | 91.1 % (wheel $4) | −4.006 | 66.1 % |
| 2024 | defect | 239 | **+4.002** | 8.4 % | 85.4 % (wheel $4) | −7.576 | 74.5 % |
| 2025 | defect | 229 | **+4.002** | **0.4 %** | 86.9 % (wheel $4) | +0.757 | 48.0 % |
| 2025 | belly | 732 | **+4.002** | 2.9 % | 82.5 % (wheel $4) | +1.129 | 44.1 % |
| 2025 | night | 854 | **+0.002** | 9.3 % | 65.6 % (wheel $0) | +1.364 | 33.3 % |
| 2025 | annual | 8,760 | +0.002 | 22.2 % | 58.8 % | −0.399 | 53.7 % |

Two readings, both load-bearing:

1. **The DSW gap is the wheel, exactly.** In the defect hours the DSW node λ
   sits `+$4.002` above the export price in the median hour — `wheel($4) + 2ε`
   — because the marginal rung there is `DSW_surplus_clean` (interior in
   85–91 % of defect hours). In the overnight set the marginal rung is
   `DSW_overnight_clean`, whose wheel is **$0**, so the gap collapses to
   exactly `2ε = $0.002`. Either way the sign is **positive**: the sink is out
   of the money in the plateau, and where the band is nonzero it is *the
   corridor's own measured OATT charge*, not a tunable.
2. **PNW is the caiso-138 §E U-turn set, re-measured.** Its node λ is *below*
   the MALIN hub in 44–74 % of belly/defect hours (2023/2024 p50 −$2.4 to
   −$7.6): that is forced firm import sitting at a node priced under the hub,
   which a live sink would resell — exactly the refused U-turn, and it is on the
   corridor that carries **no** part of the plateau.

## §C — D3: the gate. The plateau does **not** break, and cannot

**The structural argument (basis-independent).** An export sink is an
absorption column: `pmin ≤ P ≤ 0`, cost `mc × P`. Restoring its range enlarges
the feasible set with **withdrawal only** — it can add demand at its node and
can never supply. Permitting `D ≥ 0` MW of extra withdrawal at a node is
equivalent to raising that node's balance RHS by `D`, and an LP's energy-balance
dual is **nondecreasing** in its RHS (convex supply). The CA zone then sees
weakly *less* net inflow, so every CA λ moves **weakly up**. Therefore:

> No sink price and no sink bound can lower a zonal λ.

C3a-2025 is a **+$2.90 over-price**. The chartered effect — re-price the
2.7–3.0 GW import-parity plateau *downward* — is unreachable by construction,
not by parameter choice. The basis question of charter step 2 is **moot for the
chartered effect**.

**Channel 1, direct — dead.** The plateau's λ *is* a delivered-import price
(caiso-140 §C: CA λ equals the WECC_DSW node λ to p50 0.00 in the parity-priced
regime), and §B measures the export leg strictly below it by the corridor's own
wheel + 2ε. The sink is out of the money exactly where the plateau binds.

**Channel 2, indirect — dead, and this is the one that had to be measured.**
The only way an absorber could have *lowered* CA λ is by freeing a **shared**
constraint: divert forced PNW firm energy out the PNW sink, releasing
simultaneous-interface headroom so the cheaper DSW corridor imports more, with
λ_CA falling by the congestion component (DSW group dual mean −$18.40 in bound
hours). That requires the simultaneous group to be the binding constraint.
Measured on the keeper's committed network sidecars:

| year | `grp:+WECC_DSW>SP15_rest` | `grp:+WECC_PNW>NP15` | `grp:+WECC_PNW>NP15+WECC_DSW>SP15_rest` (**simultaneous**) |
|---|---|---|---|
| 2023 | binding 3,392 h, max │dual│ 127.94 | 3,211 h, 152.64 | **0 h, max │dual│ 0.00** (flow p50 3,933 / limit 16,055) |
| 2024 | 3,105 h, 72.07 | 1,441 h, 154.82 | **0 h, 0.00** (4,536 / 16,452) |
| 2025 | 3,224 h, 46.90 | 1,467 h, 70.94 | **0 h, 0.00** (4,679 / 16,148) |

The simultaneous group binds in **0 of 26,280 corridor-hours across all three
years**; every congested regime is bound by the corridor's **own** measured ATC
group. PNW headroom is therefore **not fungible** into DSW import room, and the
congestion-release channel does not exist.

**D3 VERDICT: KILL before solve.** No arm, no pre-registration, no A/B.

## §D — D4: the E1 exposure of arming it anyway, and what the measured bound removes

Upper bound per hour: a live sink can raise CA λ at most to the corridor's
export price, so `Δλ ≤ max(0, export_px − λ_CA)` on the corridor with the higher
export price, load-weighted to the C3a basis. This is a deliberately loose
**ceiling** (it assumes unbounded absorption and full CA↔node coupling):

| year | basis | sink binds | C3a move | defect-hour Δλ mean |
|---|---|---|---|---|
| 2023 | hub−ε (as built) | 42.9 % | **+9.379** | +13.167 |
| 2023 | netback (hub−wheel−ε) | 29.1 % | **+7.745** | +10.363 |
| 2024 | hub−ε | 60.4 % | **+7.860** | +11.763 |
| 2024 | netback | 35.6 % | **+5.698** | +8.508 |
| 2025 | hub−ε | 52.3 % | **+3.865** | +5.487 |
| 2025 | netback | 25.2 % | **+2.139** | +3.448 |

Every basis moves C3a in the **wrong** direction on a model that already
over-prices — the sign is structural (§C), so **nothing was swept**: there is no
value to sweep (rule 21 / D4 zero fitted values, satisfied vacuously).

**What the measured quantity bound removes.** The corridor group's
export-direction limit is *already* the measured export envelope in the keeper
(`limit_dn` on each corridor group = `measured_corridor_flow_envelope(
direction="export")`, verified byte-for-byte: DSW mean 177/189/171 MW and **0 MW
in 7,201/7,172/7,260 hours**; PNW mean 1,377/1,110/725 MW). Intersecting the
netback in-the-money set with the hours that envelope is open:

| year | PNW in-money | …and envelope open | DSW in-money | …and envelope open |
|---|---|---|---|---|
| 2023 | 24.8 % | 24.3 % (mean 1,909 MW) | 22.8 % | **4.5 %** (1,134 MW) |
| 2024 | 33.3 % | 29.4 % (1,736 MW) | 19.1 % | **1.2 %** (1,125 MW) |
| 2025 | 23.3 % | 17.6 % (1,406 MW) | 12.8 % | **1.6 %** (995 MW) |

So the admissible bound removes ~95–99 % of the DSW U-turn exposure by
construction (reality's DSW corridor essentially never net-exports) and leaves
the PNW leg — which is where the §B U-turn lives. The ceiling above is
correspondingly loose, but the **sign is not**.

## §E — the basis: an admissible third basis EXISTS, and half of it is already armed

The charter asked for a measured, rule-13-admissible export capability/price
envelope, distinct from the two adjudicated forms (caiso-138 §E: the naive
`hub−ε` at full-TTC bounds, REFUSED; the exactly-tight stranded-residual guard,
REJECTED). It exists:

* **Bound — already in the keeper.** `min(corridor link TTC, measured
  export-direction deliverability envelope)`. The envelope is in-repo
  (`measured_corridor_flow_envelope(direction="export")`, the symmetric
  counterpart of the import cap `caiso_corridor_flow_limit` already rides) and
  is **already applied** as each corridor group's reverse-direction limit — the
  keeper's own solve log prints *"export-direction cap on (evening net-export
  ~0 → no wheel-out): median export DSW 0.0 GW / PNW 0.3 GW"*. Nothing needs
  building.
* **Price — measurably too HIGH, and its provenance is NOT what this section
  first said (CORRECTED, see §I).** The as-built `hub − ε` is the **WEIM/EDAM
  transfer basis** — no OATT point-to-point wheel, exactly the basis the
  *import* side's `DSW_overnight_clean` / `DSW_daytime_clean` rungs carry,
  cited in `CAISO_IMPORT_DELIVERY_BASIS` to FINDING-caiso93 §3/§5 and caiso-94
  §2–3 ("WEIM/EDAM transfers use available transmission without an OATT
  point-to-point wheeling charge"). It is therefore **sourced**, and this
  section's original claim that the free wheel-out was "an asymmetry with no
  source" was **wrong**. What §I measures is that the **level** is too high on
  both corridors, which is a different (and re-basable) defect.

**This also un-confounds caiso-132 §3.** Its verdict that the export-direction
envelope is *"provably inert, re-arming is a no-op"* (active in 2 of 52,560
corridor-hours) was measured on a fleet whose export outlet was deleted: the
bound is armed and correct, it simply had nothing to bound. The verdict's
*conclusion* survives — for the stronger reason in §C — but its stated basis
does not, and the same correction caiso-138 §D applied to caiso-132's D0 census
applies to its envelope limb.

**What the basis does not buy: §C.** It is the right way to arm the seam
whenever the seam is armed; it is not, and cannot be, a C3a-2025 closer.

## §F — cross-ISO exposure: measured, and it CORRECTS the caiso-138 §D list

Exposure = the keeper's own interchange fleet carries a `pmin < 0` row **and**
that keeper arms a P1-native bridge whose prep routes through
`_bridge_floored_fleet`. Built from each ISO's committed keeper
`run_config.json` (rule 25: a measurement of exposure, never a verdict in
another lane):

| ISO | keeper bundle | interchange rows | pmin<0 rows (MW) | bridge flag | armed | **exposed** |
|---|---|---|---|---|---|---|
| ERCOT | ercot139_cc_committed_arm | 0 | 0 | `ercot_gas_commitment_bridge` | yes | **NO** |
| CAISO | caiso139_dumpguard_B | 11 | 2 (15,423) | `caiso_ra_mustoffer` | yes | **YES** |
| PJM | pjm137_ctheatrate_B | 80 | 40 (16,300) | — | no | no (latent) |
| MISO | miso101_tempgrain_B | 64 | 32 (17,200) | — | no | no (latent) |
| NYISO | nyiso99_demandfix | 8 | 1 (600) | `nyiso_gas_commitment_bridge` | yes | **YES** |
| NEISO | neiso61_netrev_margin | 9 | 3 (2,345) | — | no | no (latent) |

* **ERCOT is NOT exposed** — its keeper builds **no interchange rows at all**,
  so the shared composer has no absorption row to collapse. This **corrects**
  caiso-138 §D, which named ERCOT in the blast radius on the (true but
  insufficient) grounds that `_bridge_floored_fleet` serves its bridge.
* **NYISO IS exposed** — one −600 MW sink and `nyiso_gas_commitment_bridge`
  armed in `2026-07-29-nyiso-99-demandfix`, so its scored P1 has been solving
  without that outlet since the bridge was promoted. Its lane re-gates on its
  own evidence; nothing is changed for it here (the fix is CAISO-flag-gated
  precisely so no other keeper recipe shifts).
* **PJM / MISO / NEISO** carry absorption rows (40 / 32 / 3) but arm no such
  bridge today: latent, not live. Any future P1-native bridge in those ISOs
  inherits the seam unless it threads the same exemption.

## §G — what this changes on the record

* **Keeper unchanged**, NOT-YET, fail {C3a-2025, C3c}. No dashboard
  registration due (rule 15 applies to completed runs — the
  caiso-134/135/140/141 disposition; nothing solved).
* **Code:** `pipeline/commitment.py::_bridge_floored_fleet` gains
  `preserve_absorption` (default False, byte-identical), threaded from the CAISO
  RA path only; `ScenarioConfig.caiso_p1_export_sink_seam` (default False,
  registered in the cache-key drop list so every pre-existing key stays
  byte-stable — verified `2c8098e8e1684c7d` before and after); the mech mask is
  re-expressed as the composed rise. Test:
  `tests/unit/pipeline/test_pipeline_commitment.py::test_caiso_p1_export_sink_seam_gate`.
* **A3 is CLOSED as a C3a-2025 lever** — structurally, not on a residual
  measurement. A1 (the per-plant own-p25 ride-through floor) therefore does
  **not** re-open: FINDING-caiso140 §E made its return conditional on A2 or A3
  changing the closure arithmetic, and A3 changes it in the wrong direction. The
  rule-13 grant question stays unposed (caiso-141 §C).
* **C3a-2025 is now diagnosed-unclosed with an empty in-model lever queue.**
  All three of caiso-140's asks are resolved against: A1 standalone delivers
  <½ the gate (caiso-140 §D, DO-NOT-REDO standalone), A2 is walled (caiso-141),
  A3 is structurally the wrong sign (here). What remains is caiso-141 §C's
  option 2 (owner-level non-public hourly PS data) or option 3 (accept it as
  diagnosed-unclosed, the nyiso-97 C3c disposition).
* **Rule 28:** new row `caiso_p1_export_sink_seam` — CAISO **R** (rejected ex
  ante as the C3a-2025 lever, §C/§D; the code fix ships gated default-off),
  ERCOT **I** (measured-inert by construction, §F), NYISO **U** (measured
  exposure, its lane's call), PJM/MISO/NEISO **U** (latent). The
  `caiso_corridor_export_path` row's note is corrected per §E (its inertness
  measurement was confounded by this seam; the R verdict stands on §C).
* **Rule 22:** 2023–2025 only; no out-of-training year touched.
* **Pre-existing, not this session's:** `ScenarioConfig().cache_key()` on
  `origin/main` is `2c8098e8e1684c7d` while four tests pin
  `603c2498bf71d21d` — the drift predates this branch (verified by stash) and is
  untouched by it.

## §H — DO-NOT-REDO (new, binding)

* **Proposing ANY export/absorption mechanism as a fix for a model
  OVER-price.** §C: an absorption column can only raise λ. This covers the
  export sink on any price basis, any bound, either corridor, and any "surplus
  export" / "wheel-out" variant — including re-proposing
  `caiso_corridor_export_path` limb (b), which caiso-132 already rejected on
  sign. A candidate whose mechanism is "give the LP somewhere to put surplus"
  cannot lower a price; state the sign before proposing.
* **Quoting the plateau as "the export-sink seam wearing a price"**
  (caiso-140 §C bullet 3). The plateau is **interior economic import** priced at
  delivered parity; the seam is a *different* defect on the same node, and
  fixing it does not touch the plateau. That bullet's mechanism claim is
  WITHDRAWN — its arithmetic (2.7–3.0 GW, 51–61 % of defect hours) stands.
* **Re-measuring the no-trade band, the wheel-by-tranche table, the marginal
  rung identification, the group-binding census, the E1 ceiling, the measured
  export envelope, or the cross-ISO exposure census.** The committed probe
  carries all of them; §A–§F reproduce in ~5 minutes, most of it the fleet
  reconstruction.
* **Re-testing the simultaneous-interface / shared-headroom release channel**
  in any form (freeing one corridor to relieve the other). §C: the group binds
  in 0 of 26,280 corridor-hours; the corridor-own ATC groups are the binding
  constraints in every regime.
* **Re-deriving the admissible sink basis.** §E: bound is already armed at the
  link; price is `hub − wheel_out − ε`. Cite §E rather than re-surveying.
* **Naming ERCOT in the export-sink blast radius.** §F: its keeper builds no
  interchange rows.
* **Re-opening A1 on the grounds that A3 landed.** §G: A3 closed against.

## §I — ADDENDUM (same session, after the owner's promotion grant): the export price basis, measured

The owner granted promotion on structural grounds ("if structural integrity
improves but gates regress that may still be a keeper"), which turned the arm
question live and made the export leg's **price** decision-relevant for the
first time — a sink pinned at 0 has an unobservable price. Two results, both on
committed bytes, both recorded **before** either arm solved
(`PREREG-caiso142-export-sink-seam-2026-07-30.md` §0):

**1. The quantity bound was never the sink's pmin.** Each corridor group's
`limit_dn` **is** `measured_corridor_flow_envelope(direction="export")` —
verified byte-for-byte (DSW mean 177/189/171 MW with **0 MW in
7,201/7,172/7,260 hours**; PNW mean 1,377/1,110/725 MW). So a live sink is
bounded by the corridor's **own measured export capability**, and caiso-138 §E's
objection to "bounds beyond the stranded residual" does not describe this fleet.
That is the new evidence that retires the refusal — not a re-litigation of it.

**2. The export basis is measured too high (probe §G).** Identified the same way
caiso-93/94 identified the *import* basis — read off `actual CAISO RT − raw hub`
in the hours the corridor **measurably net-exported** (EIA-930 CISO BA-to-BA
interchange, model-clock aligned, net < −50 MW):

| corridor | n (2023/24/25) | p50 2023 | p50 2024 | p50 2025 | deep export (< −500 MW) p50 |
|---|---|---|---|---|---|
| WECC_PNW | 4,341 / 3,224 / 2,560 | **−3.56** | **−8.30** | **−7.40** | −4.68 / −10.81 / −8.30 |
| WECC_DSW | 474 / 459 / 405 | **+3.69** | **+4.39** | **+4.49** | +5.20 / +5.60 / +5.09 |

Reality's PNW export netback sits **$3.6–$10.8 below** the raw hub; reality's
DSW exports happen with CA priced **$3.7–$5.1 above** the raw Palo Verde hub. So
`hub − ε` over-prices the outlet on **both** corridors: a live sink on that
basis **over-exports** relative to reality, and any price regression it produces
is an **upper bound** on the correctly-priced mechanism's.

**Not stacked on the arm (rule 19, single delta).** Re-basing the export leg
introduces a new measured parameter needing its own derive script, citation and
forward story. It is the named successor charter; the arm under the grant carries
the seam composition fix alone.

## §J — the A/B result: **NOT a keeper. P2 FAILS, and it falsifies §I.** The restored outlet is node-level RESALE, not export — caiso-138 §E was right and my §I read of the bound was wrong

Arms (both `--year 2023 2024 2025`, one invocation each, sequential, same
`basis_sha 9e393a9`): `caiso142_control_A` (no delta) and `caiso142_seam_B`
(`caiso_p1_export_sink_seam=true`). Scored by the frozen
`scripts/probes/_caiso142_arm_gates.py`, committed before the arms finished.

| gate | result |
|---|---|
| **P1** outlet exists | **PASS** — B exports in 3,339/4,788/4,075 h (PNW) and 1,683/1,496/1,062 h (DSW); A exports in **0** h; corridor-group limit violation **0.0000 MW** |
| **P2** volume inside the measured envelope | **FAIL** — B's export energy EXCEEDS the corridor's measured export-envelope energy in 4 of 6 corridor-years (PNW 2024 **10.030 vs 9.722 TWh**, PNW 2025 **7.040 vs 6.352**, DSW 2023 **2.033 vs 1.552**, DSW 2024 **2.207 vs 1.659**), and B exports in **99/1,463/734/1,422/1,393/948** hours where that envelope is **0 MW** |
| **P3** corridor net toward measured | PASS as written (PNW │err│ 9.90→3.28, 10.22→0.24, 8.07→1.12 TWh) — **but see below: achieved through the P2 channel, so it is not evidence of structural gain** |
| **P4** C3a up, inside ceiling | PASS — move **+3.401/+4.172/+2.649** vs ceilings +9.379/+7.860/+3.865 |
| **P5** band | **C3a-2024 leaves the band: +8.00 % → +20.06 % (PASS → FAIL).** 2023 +3.22 % → +9.50 % (still PASS, 0.5 pt of margin left); 2025 +10.91 % → +18.61 % (FAIL → FAIL) |
| **P6** control integrity | **PASS, exact** — arm A max │Δprice│ = 0 and max │Δdump│ = 0 vs the committed keeper, all 3 years / 7 zones, which also proves the flag-OFF path byte-identical on the full solve path |

**Per the pre-registered §3 rule (P1∧P2∧P3∧P6 ∧ P4-sign/ceilings): NOT
PROMOTED.** P2 fails, and P2 was written as the gate that *"distinguishes a
bounded, measured outlet from the caiso-138 §E unbounded U-turn."* It does.

**The scored rubric confirms it independently, and worse than P5 alone showed.**
Registered run ids `2026-07-30-caiso142-control` and
`2026-07-30-caiso142-seam-sink-live`:

| | determination | governance | fail set | grade |
|---|---|---|---|---|
| keeper `caiso139_dumpguard_B` | NOT-YET | PASS | {C3a, **C3c**} | 7/9 |
| **arm A control** | NOT-YET | PASS | {C3a, **C3c**} | 7/9 — **identical to the keeper** |
| **arm B seam** | NOT-YET | PASS | {C3a, **C3b**} | 7/9 |

Arm A reproduces the keeper's determination, governance and fail set exactly —
control integrity confirmed at the rubric level as well as byte level (P6).

Arm B keeps the *count* at 2 but **swaps a load-bearing criterion for a
supporting one**: **C3b (price duration/shape, load-bearing) breaks
PASS → FAIL**, while C3c (price tail, supporting) flips FAIL → PASS. That C3c
"pass" is the phantom-resale price inflation putting hours into the tail, not
scarcity formation — CAISO still has no scarcity-pricing mechanism in the scored
lane (caiso-137b), so it cannot be read as a C3c closure. Net: the arm trades
C3b **and** the C3a-2024 band exit for a mechanism §J shows is not real.

**The mechanism, measured (why P2 fails while the link limit is never
violated).** In the closed-envelope hours where the sink transacts:

| year | corridor | closed-envelope h | of which sink exports | net LINK flow p50 | flow ≥ 0 | import inject p50 | sink absorb p50 |
|---|---|---|---|---|---|---|---|
| 2024 | WECC_PNW | 1,644 | 734 | **0.0 MW** | **100.0 %** | 2,095 MW | 1,825 MW |
| 2024 | WECC_DSW | 7,172 | 1,422 | +212 MW | **100.0 %** | 2,262 MW | 1,503 MW |
| 2025 | WECC_PNW | 3,062 | 1,393 | **0.0 MW** | **100.0 %** | 2,078 MW | 1,761 MW |
| 2025 | WECC_DSW | 7,260 | 948 | +741 MW | **100.0 %** | 2,314 MW | 1,332 MW |

Node balance `import_inject + sink = link_flow` holds to **0.0002 MW**. So the
sink's counterparty is the **same-node import block**, and the transaction never
crosses the link — the net corridor flow stays ≥ 0 in 100 % of those hours.

**§I is therefore WRONG and is withdrawn.** Its claim that *"the quantity bound
was never the sink's pmin — each corridor group's `limit_dn` bounds the
outlet"* misread the topology: `limit_dn` bounds the **net link flow**, not the
sink's withdrawal. A sink that trades against injections at its own node is
invisible to every link and group constraint in the model. **caiso-138 §E's
refusal was correct on its own terms**, and this session's "new evidence retires
it" was a reading error, corrected here by measurement. The refusal stands; §E
of this finding stands only as the *price-basis* observation (§I part 2), not as
a bound argument.

**What the U-turn actually is.** The firm tranches (`PNW_hydro_base`,
`DSW_solar_PV`) are pmin = pmax must-flow blocks priced at inframarginal
contract cost, so the forced energy arrives at the node whatever CA's λ. With a
live sink the LP diverts it to `hub − ε` whenever that beats delivering to CA —
exactly the "delivered firm energy U-turned out of the market" §E described.
Consequences all measured: the PNW link's delivered flow collapses **1,067→311 /
1,402→263 / 1,462→668 MW mean**, CA loses that supply, and C3a rises
+$3.40/+4.17/+2.65.

**P3's pass is not a structural win, and is not claimed as one.** The PNW
corridor net does move toward its measured net (9.90→3.28, 10.22→0.24,
8.07→1.12 TWh of error) — but the channel doing it is the phantom resale above:
a phantom *import* (caiso-138 §C's ~1 GW-mean overreach) is being cancelled by a
phantom *export*. The interchange number improves through a mechanism that is
not real, which is precisely what rule 1 [R-STRUCT] forbids ("never reach the
right number through a mechanism that isn't real"). The pre-registered P3 was
too weak to separate these — a fair criticism of the prereg, recorded rather
than argued away. Its per-corridor split did discriminate partially (DSW 2023
moves *away*), but the decisive discriminator turned out to be P2.

**Disposition.** Keeper stays `2026-07-29-caiso139-dump-guard-offer`. The seam
fix stays in the code, **default-off**, byte-identical off (P6, exact) — a
correctly-implemented gate whose arm is now measured-refused on this fleet. What
a future arm would need first, in order:

1. **A node-level export constraint**, not a link-level one — the sink must be
   barred from absorbing against same-node injections. The natural form is a
   per-node net-interchange row (the machinery exists: `model/lp/rows.py:1416`
   already pins a node's net interchange for other designs), bounded by the
   measured export envelope. Without it no sink bound is enforceable.
2. **The re-based export price** (§I part 2): measured PNW netback
   −$3.56/−8.30/−7.40 and DSW +$3.69/+4.39/+4.49 vs the raw hub, so `hub − ε`
   over-prices the outlet on both corridors and maximises the U-turn.
3. **Only then** the caiso-138 §C firm-block energy overreach, whose phantom
   import is what the sink is currently laundering.

Carried forward unchanged: everything in `FINDING-caiso141` §G,
`FINDING-caiso140` §G, `FINDING-caiso139` §G, `FINDING-caiso138` §G (both sink
re-arm forms remain refused — this finding adds the reason they cannot help),
`FINDING-caiso137b` §6, caiso-137 §7 first bullet, `FINDING-caiso136` §5,
caiso-135 §10, caiso-134 §9, caiso-133 §9, caiso-132 §10 (as corrected in §E),
caiso-131 §10, caiso-130 §7, caiso-129 §6, caiso-127 §7.

Next number: caiso-143.
