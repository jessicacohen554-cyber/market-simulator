# RESULT caiso-285 — the belly deficit is NOT a candidacy gate. It is the RESTART INEQUALITY, and it fails by a factor of two on the model's own arithmetic

**Lane:** CAISO calibration · **Date:** 2026-09-17 · **Keeper UNCHANGED**
`2026-09-12-caiso-275-gascoupling` · **LP spent: ONE year, in ONE shard** (rule 32 `[R-SHARD]` (a):
the parent never solved). Nothing armed, no `ScenarioConfig` field, no derive re-run, **nothing
registered** (a 2024-only replay of a 2023–2025 keeper is not a registrable run under rule 16
`[R-ALLYEARS]`). Pre-registration: `docs/PRECOMMIT-caiso285-instrumented-probe-2026-09-17.md`,
pushed at `b48448cbacc3eabebf57a051039797847ff9cf14` **before** the shard was launched. Every
threshold, bucket and verdict word below was fixed there.

---

## 0. The answer in one paragraph

The CAISO RA bridge's belly coverage is **not** limited by any candidacy gate. All 30 CC plants are
eligible, they anchor, the `startup_aware` screen drops nothing that matters, and the decommit
screen never gets a say. What stops them is the **restart inequality itself**: at the model's own
belly numbers a CC's marginal cost is **~$31/MWh**, the median belly gap is **11 hours**, minimum
load is **26 %**, so holding costs **~$97/MW even crediting the energy at $0** — against a startup
cost of **$50/MW, flat**. The inequality fails by roughly **2×**, on **99.88 %** of the belly
weight at $0 and on **100.0 %** at the belly's actual negative price. The model is making an
economically correct decision on its own inputs. The gap to reality is not a mis-set gate; it is
that a single flat class-midpoint start cost, applied identically to a 4-hour and a 24-hour
downtime, is the whole of what the model thinks a belly decommit costs.

---

## 1. The instrumented probe, and what it cost

ONE shard, ONE command, 2024 only:

```
scripts/replay_keeper.py results/calibration/caiso275_B_gascoupling_span \
  --years 2024 --out-dir results/calibration/caiso285_instr_2024 \
  --persist-p0-commitment --note "caiso-285 instrumented replay: P0 pattern + SOC"
```

**Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e)).** The shard pushed its **whole** bundle —
`dispatch/`, `floors/` and all, 92 MB, 17 files. `git ls-tree -r <sha> -- <path>` returns 17, so
rule 34 (d) is satisfied and **nothing is stranded on an ephemeral container**. Recovery, by full
SHA because branch names are not durable here (rule 33 `[R-SHARD-ARCHIVE]` (d)):

```
git checkout 203124e310f7be4f806ad968d6cf5755f96bbc00 -- results/calibration/caiso285_instr_2024
```

The bundle is **`.gitignore`d, not deleted** (rule 31 `[R-RETAIN]`; rule 29 `[R-SCREEN]` (c) governs
what reaches `main`, never the working tree). The shard was archived only after fetch + checkout +
verify (rule 33 (a)). Its branch is left in place: deletion returns HTTP 403 for this credential, and
saying so beats reporting a cleanup that did not happen (rule 33 (f)(5)).

**Shard discipline audit.** One commit, `.gitignore` (+2 lines) and its own bundle — **zero edits
under `src/` or `scripts/`**, no PR, no `git add -A`. Rule 32 (c)(6) respected. Its first solve
attempt died and it relaunched itself; it repaired nothing, which is the behaviour the prompt asked
for.

## 2. Gate G1 — the reproduction check PASSES, and the residual is characterised rather than waved

Pre-registered: the 2024 load-weighted model price must reproduce the keeper's to **< $0.01/MWh**.

| | |
|---|---|
| keeper | **37.547014** $/MWh |
| probe | **37.547070** $/MWh |
| delta | **+0.000056** → **PASS** |

The honest detail, which the headline hides. The solve is **not** byte-identical: **532 of 61,320
zone-hours** carry a different price. But the movement is not where it would matter:

* **390 of the 532 are `WECC_PNW`** — an external import node whose dual flips between $0 and a
  binding value (max |Δ| **$171.28**). That is vertex degeneracy at a node, not a CA price change.
* **Every CA zone moved in exactly 27 zone-hours**, max |Δ| **$0.28** across the whole year.
* **Inside the 876-hour belly the CA zones moved in 8 zone-hours each, max |Δ| $0.0044.**
* **The belly dispatch is reproduced exactly.** CC_REGULAR belly mean by band, keeper vs probe:
  `committed` **670.470581 / 670.470581**, every econ and peak band **0.000 / 0.000**, delta
  **0.0** on all twelve. Belly ΔMW is **0.0000** for CC_REGULAR, CT_PEAKER, CC_CHP and wind.

Supporting drift evidence, both zero-LP:

* **Registry values: zero drift.** The capx-D79 CAISO solve-surface fingerprint at HEAD is
  `cba92d202f32f9fd` over 204 rows with `moved = {NUCLEAR_MONTHLY_CF_BY_YEAR: 9f120808f18b3f19,
  STATE_CARBON_PRICE_BY_ISO: c970824c3c583991}` and `epochs: []` — identical, name for name and hash
  for hash, to what the keeper recorded at `b8ddf8bc`.
* **Config: identical on every field the keeper recorded.** The nine fields that differ are all
  fields that **did not exist** at the keeper's sha (`hydro_cascade_coupling`,
  `committed_band_measured_basis`, `unit_outage_window_hour_grain`,
  `mustrun_commitment_feasibility_clip`, `coal_fuel_inventory`,
  `gas_offer_margin_zonal_anchor_vintage`, `miso_import_sil_measured_envelope`,
  `nyiso_st_gas_econ_bands_deleaked`, `neiso_coldsnap_derate_dualfuel_unswitched`) and **all nine
  are at their HEAD default of `False`** in the probe.

So: **the HEAD CAISO backcast path still reproduces the caiso-275 keeper**, and the artifacts below
are the keeper's own. The code diff since the keeper's sha is large (96 files, +14,739/−1,445) and
was deliberately not hunk-audited — the PRECOMMIT §3 states why, and this measurement is the reason
it was the right call.

## 3. Gate G2 — the alignment check, and a defect it caught in the sanctioned rebuild helper

G2 required the P0 sidecar, the floors array and the fleet rebuild to be row-for-row aligned.
**It failed on the first attempt** — the rebuild produced **1,905** rows against the solve's
**1,705** — and the cause is a real defect, not a probe bug:

`scripts/lib/bundle_fleet.reconstruct_bundle_fleet` is **THE SANCTIONED zero-LP rebuild route**
(caiso-243 §7.3: *"every zero-LP probe that rebuilds a keeper's fleet … must take its kwargs from
here"*). `replay_keeper.DERIVED_RUN_YEAR_INPUTS` has documented since caiso-248 that
`inject_biomass_mustrun` is derived from `solve_and_persist`'s own locals, is never recorded in
`meta.json`, and that *"every fleet-only rebuild should splat this"* — **and the sanctioned helper
did not.** The rebuilt fleet therefore carried **exactly 200 phantom biomass LP rows** the scored
solve never had: a strict superset, `plant_group == ""`, which is precisely the caiso-248 defect
class, reproduced inside the helper written to make it unreachable.

**Repaired in this session** (`scripts/lib/bundle_fleet.py`): the rebuild now splats
`derived_run_year_inputs(bundle, year)`. Post-repair the rebuild is **1,705** rows and G2 passes on
all three legs. The eligible population is unchanged by the repair (the phantom rows are not
`gas_cc`/`gas_ct`, so they never entered it) — but **any prior CAISO probe that measured anything
row-aligned to a bundle artifact through this helper was reading a fleet 200 rows wider than the
solve**, and that is worth a look by whichever lane owns those probes.

## 4. The population — measured at zero LP, before the probe landed

From the (repaired) `run_year(fleet_only=True)` rebuild of the keeper's own 2024 recipe:

| | rows | tranche pmax | econ-eligible rows | Σ `target_mw` |
|---|--:|--:|--:|--:|
| **CC_REGULAR** | 30 | 4,466.2 MW | **30 / 30** | **3,631.2 MW** |
| **CT_PEAKER** | 44 | 829.8 MW | **0 / 44** | 789.5 MW |

* The CC fleet is **30 plants / 15,986.8 MW** of plant pmax; `0.26 ×` that is **4,156.6 MW**.
* **Every one of the 30 CC plants clears the 4-hour rule** (`min_down` ∈ {4, 6, 8}, startup
  $50/MW). **S1 cannot be the CC story.**
* **No CT_PEAKER clears it**: `min_down = 1.0 h` on all 44 rows. That is rule 18 `[R-PHYSICS]`
  working exactly as designed — a fast-start CT restarts within the hour and the real market cycles
  it off — **not a defect**, and it accounts for essentially the whole CT column below.
* **`caiso_ra_mustoffer_quantity_gate` is OFF** on the keeper, so the published gas-RA MW cap is not
  what caps coverage. Ruled out with no probe, and consistent with the matrix's existing
  WRONG-SIGNED adjudication of that cell.

## 5. The partition — PRECOMMIT §6.2, verbatim, on the frozen 876-hour belly

Mean belly MW, weighted by the detector's own `target_mw`, exhaustive over belly-hour × eligible
unit. Verdict cuts fixed ex ante: **IMPLICATED ≥ 0.40**, **EXONERATED < 0.05**.

### CC_REGULAR (deficit 1,921.4 MW)

| bucket | mean belly MW | share | **verdict** | what it means |
|---|--:|--:|---|---|
| `P_UNAVAIL` | 914.3 | — | — | on outage; correctly excluded |
| `P_ON` | 18.4 | — | — | already running in P0 |
| `P_FLOOR` | 777.1 | — | — | the bridge held it |
| **`S3_5`** | **1,593.4** | **0.829** | **IMPLICATED** | restart inequality **or** decommit screen |
| `S2` | 302.1 | 0.157 | CONTRIBUTORY | DA horizon, gaps > 24 h |
| `S0` | 25.9 | 0.014 | **EXONERATED** | no anchor |
| `S1` | 0.0 | 0.000 | **EXONERATED** | min-down eligibility |
| `S4` | 0.0 | 0.000 | **EXONERATED** | `startup_aware` run screen |

### CT_PEAKER (deficit 789.5 MW) — `S1` 757.8 MW, **share 0.960, IMPLICATED**; everything else ≈ 0.

**Three of the four suspects are dead, including the one this session added.** `S4`
(`caiso_ra_bridge_startup_aware`) — the gate the handoff did not name, which is armed in the keeper
and is the only one that can zero a unit outright — removes **0.0 MW** of belly coverage. `S0` is
1.4 %: **the fleet does anchor**, so the PRECOMMIT §6.3 "object is upstream of the bridge" reading
is **refuted by its own pre-registered test**. `S1` is 0.0 on CC and is the whole CT story, by
design.

Two pre-registered identity checks **FAILED**, and both failures are informative:

1. **`P_FLOOR` (777.1) > the keeper's committed band (670.5).** The cause is the weighting the
   PRECOMMIT fixed: buckets are weighted at `target_mw`, while the floor the LP actually writes is
   `target_mw × availability`, and the startup-trajectory leg writes a *ramp* below that. Weighting
   at the floor the LP saw gives the **actual RA `min_gen` belly mean = 670.470 MW** against the
   keeper's committed band delivery of **670.471 MW**. **They are the same number.** That is a
   stronger result than the check passing would have been: **the entire CC_REGULAR belly output IS
   the RA floor, exactly — the committed band delivers its minimum and not one megawatt more.**
   The availability-weighted restatement (disclosed, *not* substituted for the pre-registered
   partition) moves the verdicts not at all: `S3_5` 1,193.0 MW / **0.890**, `S2` 121.7 / 0.091,
   `S0` 25.7 / 0.019, `S1` and `S4` 0.000.
2. **3 gen-belly-hours carry an RA floor on a P0-online hour** (of 64,824 — 0.005 %). The cause is
   forced: `startup_aware` rebinds `runs` to `kept_runs`, so a gap between two *kept* runs can span
   hours a *dropped* run was online for. No other leg is armed for CAISO. So the screen **does**
   drop runs — `S4 = 0` means its drops cost no belly coverage, **not** that the screen is inert,
   and this session does not claim the latter.

Check 3 passed: no unit carries floor with zero P0 runs.

## 6. Splitting `S3_5` — the restart inequality, not the decommit screen

The P0 dual is not persisted, so the inequality cannot be evaluated directly. It does not need to
be. Inverting it gives, per gap, the LMP **above which** the bridge would hold:

```
hold  ⟺  startup_per_mw  >  (mc_gap − lmp) × min_load_frac × gap_hours
      ⟺  lmp  >  mc_gap  −  startup_per_mw / (min_load_frac × gap_hours)
```

Over **all 1,866** S3_5 gaps touching the belly — exhaustive, covering all 1,593.4 mean-belly-MW,
MW-weighted percentiles p1/p25/p50/p75/p99:

| quantity | p1 | p25 | **p50** | p75 | p99 |
|---|--:|--:|--:|--:|--:|
| gap hours | 8 | 10 | **11** | 13 | 22 |
| `mc_gap` $/MWh | 25.71 | 29.80 | **31.36** | 33.87 | 45.71 |
| **LMP needed to hold** $/MWh | 5.65 | 11.77 | **14.24** | 18.46 | 33.54 |

| the bridge would need a belly LMP above… | share of S3_5 belly MW that fails |
|---|--:|
| $0.00 | **0.9988** |
| −$6.71 (the 2024 belly mean price) | **1.0000** |
| −$20.00 (the surplus reprice floor) | **1.0000** |

**This decides it.** The bridge needs roughly **+$14/MWh** to hold a median belly gap. The belly
clears at **−$6.71**. The failure is total at any price the belly can produce, and it is total
*before* the decommit screen does anything — so **the surplus reprice to −$20 is irrelevant, and the
decommit screen is EXONERATED from the arithmetic**, which sharpens caiso-284 §2.3's "not binding"
from a mean-hour comparison into a proof.

**The bar, stated as arithmetic and explicitly NOT proposed as a value.** To hold the median gap
requires a startup cost of **$96.9/MW** crediting the energy at $0, or **$115.4/MW** at the belly's
actual price (p75: $124.5 and $145.7). The model carries:

```
BIN_STARTUP_COST_PER_MW["CC_REGULAR"] = 50.0      # data/fleet/eia860.py:3230
# "Source: NREL/SR-5500-55433 (Kumar et al. 2012), consistent with the legacy
#  CC_STARTUP_PARAMS / CT_STARTUP_PARAMS midpoints."
```

**A single flat class midpoint, carried identically by all 30 CC plants and applied identically to a
4-hour gap and a 24-hour gap.** It is a cited class constant, not a fitted knob — but it is the sole
term standing between the model's belly and reality's, and it has **no dependence on downtime**,
which is the one variable a decommit-and-restart decision turns on.

**Rule 1 `[R-STRUCT]`, stated plainly: the bar above is NOT a proposed parameter value and this
session does not propose one.** Choosing $97 or $115/MW because it is what closes the residual is
exactly the fitted mechanism rule 1 forbids, and inverting a residual is how you get one. A
successor must obtain a **downtime-dependent** start cost from a source and then discover whether it
lands above or below this bar — and must be willing to report that it lands below.

## 7. The storage ENERGY premise — **FALSIFIED**, and INERT for this object

`_apply_economic_bridges` excludes storage-charge headroom from `absorb` on an explicit energy
premise: *"the fleet already fills by the belly in P1."* caiso-284 falsified the power half and could
not test the energy half at all. With the SOC columns caiso-284 landed:

| | |
|---|--:|
| total storage energy capacity | 894,576.7 MWh |
| **median belly-hour headroom (Σcap − Σsoc)** | **427,293.2 MWh** |
| **as a share of capacity** | **0.4776** (p10 0.167, p90 0.938) |
| hours the unused 1,945 MW of belly charge power could be sustained | **219.7 h** |

Pre-registered cut: FALSIFIED at ≥ 0.20. **The premise is false by more than a factor of nine** —
at the median belly hour the storage fleet is **less than half full**, with ~220 hours of charging
headroom behind the unused power caiso-284 measured.

**And it does not matter, which this session reports rather than burying.** Widening `absorb` would
move gap hours out of surplus and credit held energy at the LMP instead of −$20 — but §6 shows the
inequality fails at **any** price at or below zero. A falsified premise that cannot move the object
is a **correction to the record, not a lever**, and promoting it to one would be selecting a
mechanism on something other than its own evidence.

## 8. What this closes, and what it opens

**Closed (rule 28 `[R-MECH-MATRIX]` (a) — do not re-test without new evidence):**

1. `RA_BRIDGE_ECON_MIN_DOWN_HOURS` as the CC belly limiter — **0.0 MW**, 30/30 plants eligible.
2. `caiso_ra_bridge_startup_aware` as a belly-coverage limiter — **0.0 MW** (it does drop runs; the
   drops cost no belly coverage).
3. The surplus **decommit** screen — the inequality fails before it is consulted, on 100 % of belly
   weight.
4. "The fleet does not anchor" (`S0`) — **1.4 %**. It anchors.
5. `caiso_ra_mustoffer_quantity_gate` — OFF on the keeper; cannot be the cap.
6. The storage-headroom premise — falsified, and inert for this object.

**Open, and named without being armed:** the belly commitment decision rests entirely on a **flat,
downtime-independent CC start cost**. The successor is to find out what a CAISO CC actually charges
to restart after 8–24 hours down — CAISO's own published start-up cost bids by configuration, or the
hot/warm/cold structure the cited NREL source distinguishes and this repo's constants do not carry
anywhere. That is a **measured-input question (rule 14 `[R-ACCURATE]`)**, answered before any solve
and with its own PRECOMMIT.

**`S2` (DA horizon, 9–16 %)** is left alone: `DA_COMMITMENT_HORIZON_HOURS = 24` is market design — a
gap longer than one operating day is a next-day re-offer decision — and 302 MW does not justify
re-opening it while §6 holds.

**Cost if the successor proceeds:** CAISO's registered year set is **2022–2025**, so rule 34
`[R-SHARD-PROMOTABLE]` (c) and rule 35 `[R-PROMOTE]` (c) price it at **four year-shards**, each
pushing its bundle. Nothing here authorizes that; PRECOMMIT §6.3's "no lever ⇒ no span" was
respected and **no span was launched.**

## 9. Ledger

* **Keeper unchanged.** Nothing registered, nothing promoted, nothing pruned.
* **No `ScenarioConfig` field**, no derive re-run, no offer-curve multiplier touched.
* **Matrix (rule 28 (b)):** no mechanism was *tested* — this instruments one already in the keeper —
  so no cell verdict moves. The `gas_commitment_bridge` cell stays **K** and its evidence line is
  extended with this result.
* **Code changed:** `scripts/lib/bundle_fleet.py` only (§3), a correctness repair to the sanctioned
  zero-LP rebuild route.
* **Artifacts:** `results/calibration/_caiso285_bridge_candidacy.json` (the full partition, per-unit
  census and gap table), `results/calibration/_caiso285_belly_2024.json` (the frozen hour set),
  `scripts/probes/caiso285_bridge_candidacy.py` (committed before the answer existed).
