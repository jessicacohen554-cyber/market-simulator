# FINDING — caiso-133: the binding CAISO import limit is **the corridor deliverability group, alone**. The link's own TTC and the `WECC_import_simultaneous` seam row are **structurally unreachable in all 26,280 hours of 2023–2025, in BOTH directions**, and their solved duals are **exactly 0.000 in every hour** — so 100 % of the defect-hour congestion rent is charged by a MEASURED envelope. And in the very hours that envelope binds, the model already carries **+2.0 to +2.5 GW MORE import than actually flowed**, so it is not the inaccurate input. **C3a-2025 is handed back as unreachable from the corridor lane, with no candidate.**

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED. Nothing was armed** —
no mechanism, no flag, no new `ScenarioConfig` field. The one solve this session
ran is a **no-delta replay of the keeper's own recipe** whose only purpose was to
prove the new write path cannot touch the LP; it reproduces the committed keeper
**exactly** (`max |delta| = 0`, every class, every zone, every hour, all three
years) and is registered as the control arm `2026-07-28-caiso-133-sidecar-control`
per rule 15 `[R-DASHBOARD]`.

Instruments (committed):
`scripts/probes/_caiso133_binding_limit_separation.py` (sections A/B/C/D) and
`scripts/probes/_caiso133_sidecar_invariance.py` (the byte-identity gate).
Bundle: `results/calibration/caiso133_sidecar_A`.

---

## §1 — what this session was asked, and what it delivered

`FINDING-caiso132` killed ask A1 and, in doing so, filed an explicit honest
limit (§2): the zonal spread says *some* import-direction limit binds, but the
duals alone **cannot say which** of

1. the **corridor deliverability group** — the measured EIA-930 per-(month ×
   hour-of-day) p95 net-import envelope, one interface row per leg;
2. the **link's own TTC** — COI/Path-66 4,800 MW into NP15, Path-46/WOR
   10,623 MW into SP15_rest;
3. the **`WECC_import_simultaneous` seam row** over both legs — 7,500 MW baked,
   superseded by the published branch-group MIC under
   `capacity_deliverability_limits` (the keeper's setting).

Until that was separated, no lever could be selected for **C3a-2025** and any
candidate was a guess. Two parts, the first unblocking the second:

- **Part 1** — two write-only, solve-invariant sidecars on the caiso-127
  storage-sidecar precedent (§2).
- **Part 2** — the separation itself, answered **two independent ways** that
  agree exactly: a no-LP reachability argument from committed data (§3) and the
  measured duals from the new sidecar (§4).

## §2 — Part 1: the two sidecars, and the proof they cannot touch the LP

Both land under `hourly/`, which escapes the slim-bundle gitignore by
construction, so a KEEPER bundle can carry them (rule 15).

| sidecar | grain | carries | size / year (CAISO) |
|---|---|---|---|
| `hourly/unit_hourly_<y>.parquet` | LP unit × hour | `mw`, `cap_mw` (= `pmax × availability`, the LP's own upper bound), `plant_code`, `plant_group`, `fuel`, `zone` | **1.7 MB** (14.2 M rows) |
| `hourly/network_<y>.parquet` | link **and** interface group × hour | `mw`, `dual`, `limit_up`, `limit_dn` | **0.20 MB** |

**Both are committed onto the KEEPER bundle**, not only onto this session's arm.
That is the `replay_keeper` precedent used exactly as documented — replay the
keeper's own recipe to *add* a solve-invariant output the original bundle
lacked (the same thing `btm.parquet` did), justified here by the `max |delta| = 0`
result below. Every pre-existing keeper file is untouched; the bundle only gains
six files and goes from 3.7 MB to 9.1 MB. So a later session reads the keeper
directly, as rule 15 intends, instead of replaying it —
`scripts/probes/_caiso133_binding_limit_separation.py results/calibration/caiso130_nameplate_B`
reproduces every number in this FINDING with no solve.

**Size was a hard constraint and it nearly bit.** The first build wrote
`unit_hourly_2023` at **12.60 MB**, of which the tiled `0..8759` `hour` ramp
alone was **11.12 MB** — PLAIN int32, 88 % of the file — against 1.04 MB for
`mw` + `cap_mw` combined. Delta-packing that one column
(`DELTA_BINARY_PACKED`, lossless) takes the file to **1.74 MB** and the 3-year
bundle from ~38 MB to **5.2 MB**, i.e. from 6× the largest committed bundle to
the same order as the existing class/system sidecars. A regression test pins the
encoding (`tests/unit/pipeline/test_diagnostic_sidecars.py::TestSidecarEncoding`)
because losing it would silently re-inflate every future keeper.

**The byte-identity requirement, met exactly.** The claim "write-only" is a claim
about code, so it was measured. The keeper's recipe was replayed at this
session's HEAD (`scripts/replay_keeper.py`, no `--set`) and compared to the
keeper's own committed sidecars:

| year | series | max \|delta\| |
|---|---|---|
| 2023 / 2024 / 2025 | `class_hourly.mw` | **0** |
| 2023 / 2024 / 2025 | `system.price`, `.slack`, `.dump`, `.demand`, `.reserve_price` | **0** |

Not a tolerance — exact zero on every series, every zone, every class, every
hour, all three years.

Two further checks, both clean:

* **Run-to-run determinism.** The replay was solved twice (the second time only
  to pick up the `hour`-column encoding fix), and the two independent solves
  agree at `max |delta| = 0` on every column of every `hourly/` sidecar —
  including `network` and `unit_hourly`. The encoding change is lossless:
  `unit_hourly_2023` 12.62 MB → 1.74 MB, identical values.
* **Basis clean across the rebase.** The bundle was solved at `b0ee3eb` and the
  branch then rebased onto `b1c91e7` (7 upstream commits: miso-99 CHP heat
  rates, ercot-128 coal min-config, pjm-134 matrix rows). Rather than assume
  those are CAISO-inert, every LP input `run_year(fleet_only=True)` hands the
  CAISO 2025 solve was hashed before and after: `pmax`, `pmin`, `availability`,
  `min_gen`, `heat_rate`, `vom`, `unit_ids`, `demand`, `fuel_prices`, `mc_base`,
  `wind_cf/cap`, `solar_cf/cap`, `storage_power_cap` — **all 16 hashes
  identical, `n_gen` 1,358 both sides**. Identical LP inputs ⇒ identical LP ⇒
  identical dispatch, so the window is CAISO-inert and the bundle is what the
  merged HEAD produces. (The two new upstream flags,
  `measured_chp_heat_rates` and `ercot_coal_min_config_floor`, are both
  default-off and their data artifacts are MISO/ERCOT-scoped — the hashes are
  the measurement of that, not the inference.) Structurally this is what the code guarantees: the writers
run *after* `run_energy_solve` returns and read only the solved result plus LP
inputs the solve already consumed, and the LP-side additions
(`rows.build_constraints` returning the interface block's row offset; `model.py`
slicing the interface row duals and the flow columns' reduced costs out of the
HiGHS solution) add **no row, no bound and no coefficient**. Six unit tests in
`tests/unit/model/test_dispatch.py::TestNetworkDualAttribution` pin the
extraction on trivial systems, including the two one-limit corner cases and the
stationarity identity §4 rests on.

## §3 — §A: the answer, with **no LP at all** — two of the three limits are unreachable

A constraint can carry a positive dual only if some feasible point makes it
tight. Each corridor leg's flow is bounded above by its **own** corridor group
cap, so the other two limits are strictly slack whenever

* `env_leg(t) < TTC_leg` — the link's own bound is unreachable, and
* `env_PNW(t) + env_DSW(t) < MIC` — the seam row is unreachable.

Both hold in **every hour of every year, in both directions**:

| year | leg | import env max | TTC | env/TTC | h env ≥ TTC | export env max | export/TTC |
|---|---|---|---|---|---|---|---|
| 2023 | WECC_PNW | 3,846 | 4,800 | 0.801 | **0** | 3,762 | 0.784 |
| 2023 | WECC_DSW | 6,755 | 10,623 | 0.636 | **0** | 2,195 | 0.207 |
| 2024 | WECC_PNW | 2,951 | 4,800 | 0.615 | **0** | 3,328 | 0.693 |
| 2024 | WECC_DSW | 7,134 | 10,623 | 0.672 | **0** | 2,773 | 0.261 |
| 2025 | WECC_PNW | 3,239 | 4,800 | 0.675 | **0** | 3,024 | 0.630 |
| 2025 | WECC_DSW | 7,656 | 10,623 | 0.721 | **0** | 2,180 | 0.205 |

| year | Σ leg import caps (max) | seam cap (published MIC) | Σ/MIC | h Σ ≥ MIC |
|---|---|---|---|---|
| 2023 | 9,631 | 16,055 | 0.600 | **0** |
| 2024 | 9,557 | 16,452 | 0.581 | **0** |
| 2025 | 10,777 | 16,148 | 0.667 | **0** |

**Therefore every bind on either corridor leg — import or export — is the
corridor deliverability group.** The `FINDING-caiso132` §2 three-way ambiguity is
closed, and it is closed *analytically*, from data that was already committed
when caiso-132 was written.

## §4 — §B: the measured duals say the same thing, to machine precision

The LP's own stationarity on the zero-cost flow column closes the decomposition
exactly. The column appears in the two energy-balance rows plus every interface
group it belongs to, so

```
    lambda_to − lambda_from  =  −z_link  −  Σ_g s(g,link) · y_g
```

with `z_link` the column's reduced cost (its own TTC bound), `y_g` each group's
row dual and `s` its signed membership. Every right-hand term is ≥ 0 in the
import direction and is the rent charged by **exactly one** limit. Read off
`hourly/network_<y>.parquet`, on the Sep–Dec surplus belly (caiso-120/121's
conventions, the same defect-hour mask caiso-132 used):

| year | n | leg | rent $/MWh | **corridor group** | link TTC | seam row | identity residual |
|---|---|---|---|---|---|---|---|
| 2023 | 192 | WECC_PNW | 17.16 | **17.16 (100.0 %)** | **0.00** | **0.00** | 3.9e-07 |
| | | WECC_DSW | 8.99 | **8.99 (100.0 %)** | **0.00** | **0.00** | 1.9e-07 |
| 2024 | 239 | WECC_PNW | 21.71 | **21.71 (100.0 %)** | **0.00** | **0.00** | 5.1e-07 |
| | | WECC_DSW | 6.31 | **6.31 (100.0 %)** | **0.00** | **0.00** | 1.4e-07 |
| **2025** | **229** | **WECC_PNW** | **35.33** | **35.33 (100.0 %)** | **0.00** | **0.00** | 6.8e-07 |
| | | **WECC_DSW** | **9.02** | **9.02 (100.0 %)** | **0.00** | **0.00** | 2.1e-07 |

Whole-year, demand-weighted, the same split holds (PNW 33.00/29.52/19.48, DSW
8.95/3.32/3.04 — all 100 % corridor group). The link-TTC and seam duals are not
merely small: they are **nonzero in 0 of 8,760 hours** on both legs in all three
years.

**Three independent reconciliations, all exact.** (i) The defect-hour rents
reproduce `FINDING-caiso132` §6 digit-for-digit ($17.16 / $8.99, $21.71 / $6.31,
$35.33 / $9.02). (ii) The corridor group's binding-hour share read off its *dual*
reproduces caiso-132 §3's binding-direction census read off the *spread sign* —
2023 PNW 0.5281, DSW 0.3765 — the same numbers by two unrelated routes. (iii) The
stationarity identity closes to **3.4e-06 $/MWh worst-case** across all legs,
hours and years.

## §5 — §C: the binding limit is a MEASURED envelope, and it is **not** the inaccurate input

Having named the limit, rule 14 `[R-ACCURATE]` asks the next question: is it
wrong? The session's brief was explicit that relaxing the import ceiling is
refused on its face unless the limit itself is shown inaccurate. It is not — and
the evidence points the other way.

| year | corridor import ceiling | model import | utilisation | **measured (EIA-930)** | **model − measured** |
|---|---|---|---|---|---|
| 2023 | 4,270 MW | 3,296 MW | 0.760 | 756 MW | **+2,540 MW** |
| 2024 | 5,901 MW | 4,898 MW | 0.824 | 2,882 MW | **+2,016 MW** |
| **2025** | **6,050 MW** | **5,569 MW** | **0.929** | **3,510 MW** | **+2,059 MW** |

(Measured is read from the same EIA-930 bytes, the same model-clock lag
correction and the same (month × hod) bucketing that
`measured_corridor_flow_envelope` uses to *build* the cap — so this is the model
against the cap's own source, not a re-derivation. It reproduces caiso-121's
+2,606 MW surplus-belly over-import on the current keeper.)

**The model is pressed against a cap it is already over-running by 2 GW relative
to what physically flowed.** The cap is not too tight; on the hours that matter
it is if anything too generous. So:

* **Relaxing the corridor envelope is refused** — rule 1 `[R-STRUCT]` and rule 14
  `[R-ACCURATE]`. It would move the model *further* from measured flow to buy a
  price improvement, which is the definition of reaching the right number through
  a mechanism that isn't real.
* **`FINDING-caiso132` §8's net-vs-gross observation is priced, not rehabilitated.**
  Its objection (ii) was that the model already over-imports; §5 now measures that
  objection on the exact hours a gross representation would act on. A bidirectional
  corridor representation that buys *more* import headroom moves the wrong way
  there. It remains an unchartered observation with its objections intact.

## §6 — the hand-back: C3a-2025 is unreachable from the corridor lane

Stated plainly, as the brief asked. The corridor congestion carrying C3a-2025 is
real, it is import-direction (caiso-132), and it is charged **entirely** by a
measured, rule-13-admissible capability envelope that regenerates for a forward
year and responds to changed conditions. There is no inaccurate input to fix and
no slack limit to tighten. **The corridor lane is closed for C3a-2025, and this
session deliberately manufactures no candidate.**

What the measurement *does* say — filed as an observation, **not** a chartered
candidate — is that the pressure is **upstream of the corridor**. The cap binds
because the model *wants* ~2 GW more import than reality took in the midday
Sep–Dec surplus, not because the cap is below what reality delivered. The corridor
is where that pressure shows, not where it originates: the object that would have
to change is whatever makes CA's own midday supply expensive enough to pull that
much import. Any future charter in this lane belongs there, and it must clear the
ask memo §2 envelope, above all **E1 (2025 spillover ≤ +$0.00)** — 2025 has
−$0.31 of band room.

## §7 — Part 1's first dividend: ask A2's D1 is now computable, and it passes

`docs/handoffs/caiso-131-c3c-c3a-ask-2026-07-27.md` §4 records A2's D1 as
**BLOCKED** on exactly the data the unit sidecar now carries. It is now a read:

| year | TOTAL thermal headroom (min / p10) | **PLANT-LEVEL ONLINE thermal (min / p10)** | offline quick-start (min) |
|---|---|---|---|
| 2023 | 3,090 / 10,679 MW | **704 / 1,201 MW** | 643 MW |
| 2024 | 3,225 / 10,644 MW | **701 / 1,119 MW** | 1,614 MW |
| 2025 | 3,815 / 11,128 MW | **670 / 1,021 MW** | 2,524 MW |

D1's gate is < 5 GW in the model's own tightest decile; the online measure is
**1.0–1.2 GW**, an order of magnitude below the 12–13 GW total-headroom surface
`FINDING-caiso131` §4 measured, and it sits *inside* the LOLP's live range
(CAISO MCL 1,400 MW, σ 2,500 MW). **D1 does not kill A2.**

Two honest qualifications, neither of which this session adjudicates:

1. **A premise in the ask needs correcting against the code.** §4 states that
   "CAISO's overlay still evaluates `reserve_headroom` on total fleet headroom."
   It does not: `results.scarcity.caiso_scarcity_overlay` calls `reserve_headroom`
   — which already splits online/offline through `_online_plant_mask` — and passes
   `reserves_online_mw=r_online` into `ordc_adder`, where it drives the half-hour
   LOLP term. What is large is `reserves_total = r_online + r_offline +
   import_headroom`, the **full-hour** term's argument. What A2 should therefore
   re-specify is A2's question, not this one's.
2. **The number above is the online THERMAL component**, the part this sidecar
   uniquely unblocks. The overlay's own `r_online` additionally carries storage
   headroom and curtailed-renewable headroom, which no committed sidecar holds.
   It is a lower bound on `r_online` and is reported as one.

A2's D2 (the §2 E1/E2 spillover pre-check) and D3 (no fitted parameter) are **not**
run here. Arming A2 remains a separate owner ask with its own prereg.

## §8 — what this does and does not change

* **Keeper unchanged**, determination NOT-YET, fail set **{C3a-2025, C3c}**. No
  mechanism was armed, no `ScenarioConfig` field added, no gate re-scored.
* **C3a-2025 keeps its diagnosis and now also loses its lane.** caiso-132 removed
  its *selected family*; caiso-133 shows the remaining corridor object is a
  correct measured input, so the corridor lane as a whole is closed for it.
* **The `capacity_deliverability_limits` seam half is measured INERT in the CAISO
  backcast.** At 16,055 / 16,452 / 16,148 MW the published MIC sits above the sum
  of both legs' own measured envelopes (max 9,631 / 9,557 / 10,777 MW), so its row
  dual is exactly 0.000 in every hour of every year. This bounds what the flag's
  part (a) can do in a *backcast*; it says nothing about the forecast lane, where
  the corridor envelope is not the binding object. Recorded on the mechanism
  matrix (rule 26 `[R-MECH-MATRIX]`).
* **C3c was not touched** — separate lane (asks A2/A3/A4).
* **Rule 20 `[R-HOLDOUT]`**: 2023–2025 only. No year outside the training window
  was solved, scored or probed.

## §9 — DO-NOT-REDO (new, binding)

* **Re-measuring which CAISO import limit binds**, by any route. §3 settles it
  analytically from committed data and §4 confirms it from the solved duals, and
  the two agree exactly. The link TTC and the seam row are unreachable in all
  26,280 corridor-hours in **both** directions; their duals are 0.000 in every
  hour. This does not need a solve and does not need repeating.
* **Proposing to relax, widen or re-derive the corridor import envelope to close
  C3a-2025.** §5: the model already over-imports the defect hours by +2.0 to
  +2.5 GW against measured flow. Rule 1 / rule 14 refused on its face; a proposal
  must first show the *envelope* is wrong against its own EIA-930 source, which
  §5 shows it is not.
* **Re-deriving the C3a-2025 corridor story as a transmission defect at all.** The
  binding object is a correct measured input. Further corridor work on C3a-2025 is
  closed; the pressure is upstream (§6).
* **Re-running the sidecar byte-identity proof.** §2: `max |delta| = 0` on every
  scored series, all three years, against the committed keeper. The arm bundle and
  its instrument are committed.
* **Re-measuring ask A2's D1.** §7 carries it for all three years from the
  committed sidecar; the instrument re-runs it in seconds with no solve.
* **Dropping the `DELTA_BINARY_PACKED` encoding on the sidecars' `hour` column.**
  §2: it is 88 % of the unencoded file and its loss silently re-inflates a 3-year
  keeper bundle from ~5 MB to ~38 MB. Pinned by a test.

Carried forward unchanged: everything in `FINDING-caiso132` §10 (above all, the
corridor **export**-path family is CLOSED in any scoped or windowed form, and
re-arming the corridor export envelope is a no-op), `FINDING-caiso131` §10,
`FINDING-caiso130` §7, `FINDING-caiso129` §6 and `FINDING-caiso127` §7. Notably
still binding: `caiso_endogenous_wecc_node` is not re-armable; the allocation-floor
and AS-award families are CLOSED; the extract basis is frozen (caiso-123 /
neiso-66 ACTIVE) and C3a-2025 is a guard, never a tuning target.

Next number: caiso-134.
