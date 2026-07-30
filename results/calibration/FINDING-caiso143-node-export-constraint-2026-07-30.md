# FINDING — caiso-143: **BOTH chartered prerequisites are refused before any arm.** (1) The node-level export constraint is **algebraically redundant** with the corridor-group bound already armed (`limit_dn` == the measured export envelope, max diff **0.000000 MW**, and the node identity `Σ P_node ≡ link_flow` holds exactly — slack = dump = 0.0000 MW in every hour of both committed bundles), and worse: a **sound** export sink is **NOT LP-REPRESENTABLE AT ALL** — the soundness set is non-convex, its tightest linear surrogate reduces to `F + I_econ ≤ 0` (infeasible while the must-flow block forces 11.7/15.6 TWh), and its convex hull contains exactly the resale points being excluded. (2) The export price re-basis is **not identifiable without a fitted value** — PNW's measured netback swings **$4.74** across years (3.8× the import basis it mirrors) with a **$7.70–10.48 season/depth cell range** and a 2023 sign flip, and on DSW the measurement **refutes the price-taking form** (CA clears *above* the hub in 62–72 % of real export hours), which also **corrects caiso-142 §I**'s "over-prices on BOTH corridors". D-gate KILL before solve: no arm, no A/B, no new field, keeper unchanged. **The dependency inverts** — caiso-138 §C's forced-injection elasticity is not prerequisite (c), it is prerequisite (a) (2026-07-30)

**Keeper `2026-07-29-caiso139-dump-guard-offer` UNCHANGED** (NOT-YET, fail
{C3a-2025, C3c}). No LP was built, no solver ran, no bundle was produced, no
mechanism was armed, and — unlike caiso-142 — **no `ScenarioConfig` field is
added**: the chartered constraint is proved non-existent rather than
built-and-refused, so shipping a flag for it would be dead code (rules 24/26).
This is the caiso-129/140/142 kill-before-solve discipline executing.

Instrument (committed, no LP, no solver):
`scripts/probes/_caiso143_node_export_gates.py` — §A–§G below. §A reads the
model's own topology (`split_caiso_import_node_per_hub`) and the committed
`system_*`/`network_*` sidecars of the keeper **and** of `caiso142_seam_B`;
§B/§C exercise the real fleet build (`run_year(fleet_only=True)`, the
caiso-131/134/140/142 machinery) for all three years; §D reads arm B's committed
`class_hourly`; §E reads the committed actual-LMP reference, the measured hub
series and the committed EIA-930 interchange frame; §F is analytic; §G reads all
six ISOs' committed keeper `run_config`s.

---

## §A — D1: the chartered node-level row is **ALGEBRAICALLY REDUNDANT**

The charter asked for a row bounding *"the node's NET interchange in the EXPORT
direction by the measured export-direction envelope"*. Measured on the model's
own topology and on both committed bundles:

| check | result |
|---|---|
| priced corridor zones | `WECC_PNW` (1 link out: `WECC_PNW>NP15`, 0 in), `WECC_DSW` (1 link out: `WECC_DSW>SP15_rest`, 0 in) |
| `load_share` | **0.000** both (config: `Zone(..., load_share=0.0)`) |
| node `demand` / `slack` / `dump`, max │·│ over 8,760 h | **0.0000 / 0.0000 / 0.0000 MW** — every zone, every year, **keeper AND arm B** |
| fuels present at either node (keeper `unit_hourly`) | **`['import']` only** — no renewables, no storage, no thermal |
| **`max │Σ_g P[g,t] − link_flow[t]│`**, directly on the keeper's committed unit-level rows | **0.000244 MW** (PNW) / **0.000488 MW** (DSW), all three years — float32 parquet rounding |
| corridor group `limit_dn` vs `measured_corridor_flow_envelope(direction="export")` | **max diff 0.000000 MW**, all 6 corridor-years |

The node therefore has no load, no renewables, no storage, one link and zero
solved slack/dump, so its energy-balance row *is* the identity

```
Σ_g P[g, t]  ==  link_flow[t]      (verified directly, 0.000244 / 0.000488 MW)
```

and the chartered row

```
Σ_g P[g, t]  >=  -envelope_export[t]
```

is **the same linear combination** as `link_flow[t] >= -envelope_export[t]`,
which the corridor group **already imposes at exactly that bound**. The row
cannot change the feasible set. FINDING-caiso142 §J measured the consequence
from the other side: in the resale hours the net link flow is **≥ 0 in 100.0 %**
of hours (PNW p50 exactly 0.0 MW), i.e. the chartered row is **slack in
precisely the hours D1 asks it to bind**, and it drives the sink to 0 in **none**
of the 99/1,463/734/1,422/1,393/948 hours.

Separately, the machinery the charter cites — `rows.py:1416` /
`_build_import_node_rows` — builds **one row per month** pinning a monthly
net-throughput *band* (the NYISO EIA-930 reconciliation design), not an hourly
directional bound, so it is not the row the charter describes either.

**D1a: FAIL — redundant, not weak.**

## §B — the resale channel's origin: the **must-flow block**, not the sink

Reconstructed 2024 keeper fleet, all 11 interchange rows:

| row | pmin | pmax | wheel | floor > 0 h | forced TWh |
|---|---|---|---|---|---|
| `WECC_PNW_PNW_hydro_base` | 0 | 3,100.8 | $2 | **7,725** | **11.668** |
| `WECC_DSW_DSW_solar_PV` | 0 | 3,608.3 | $4 | **7,994** | **15.564** |
| `PNW_midC`, `DSW_CCGT`, `DSW_CT`, `WECC_scarcity`, `DSW_surplus_clean`, `DSW_overnight_clean`, `DSW_daytime_clean` | 0 | 1,800–6,205 | $0–6 | **0** | 0.000 |
| `WECC_PNW_export_MALIN` / `WECC_DSW_export_PALOVRDE` | −4,800 / −10,623 | 0 | — | 0 | 0 |

**Exactly 2 of 9 injection rows are price-insensitive.** That is decisive:

* an **economic** tranche costs `hub + wheel + ε` while the sink pays
  `hub − ε`, so buy-to-resell loses `wheel + 2ε` per MWh (wheels $2/$4/$5/$6) —
  **an all-economic node cannot resell at all, whatever the sink's bound**;
* the two **firm** rows are floored at `min_gen = pmax × availability`
  (`inject_caiso_firm_import_selfschedule`, caiso-77 must-flow), so **27.2 TWh**
  of 2024 energy arrives at the node whatever CA's λ is — that *is* the
  counterparty caiso-142 §J measured (inject p50 ~2,100 MW vs ~1,800 MW absorbed,
  node identity to 0.0002 MW).

A bound on the **sink** can therefore only *meter* the channel. It closes only
where it opens: at the forced injection.

## §C — D1c: the one LP-representable alternative **meters the channel, and disarms the gate that caught it**

The only linear form that is *not* redundant is a **gross** absorption bound —
a per-hour column bound `S[t] ≥ −envelope_export[t]` (not a row). It does pin
the sink to 0 in every closed-envelope hour. What it leaves in the **open**
hours, measured (keeper node injection `I_A`, must-flow `F`, envelope `E`;
transacting = envelope open ∧ sink in the money on the as-built basis):

| year | corridor | env > 0 h | transacting h | **F ≥ E** | **I_A ≥ E** | net-flow floor p50 | net < 0 share |
|---|---|---|---|---|---|---|---|
| 2023 | PNW | 8,048 | 3,699 | **31.7 %** | 31.7 % | −877.9 MW | 68.3 % |
| 2023 | DSW | 1,559 | 460 | **7.4 %** | 7.4 % | −954.0 MW | 92.6 % |
| 2024 | PNW | 7,116 | 4,496 | **51.4 %** | 51.4 % | **+67.6 MW** | 48.6 % |
| 2024 | DSW | 1,588 | 153 | **37.9 %** | 37.9 % | −413.0 MW | 62.1 % |
| 2025 | PNW | 5,698 | 3,127 | **51.4 %** | 51.4 % | **+46.4 MW** | 48.6 % |
| 2025 | DSW | 1,500 | 211 | **39.8 %** | 39.8 % | −439.4 MW | 60.2 % |

Three readings:

1. **`F ≥ E` and `I_A ≥ E` coincide to 0.1 pp in all six corridor-years.**
   Injection ≥ the forced floor always, so `{F ≥ E} ⊆ {I_A ≥ E}`; their equality
   means **no hour has `F < E ≤ I_A`** — the residual resale is driven *entirely*
   by the must-flow block, never by economic imports. §B, confirmed numerically.
2. **The bound leaves resale in 31.7–51.4 % of PNW and 7.4–39.8 % of DSW
   transacting hours** — the hours where the forced block alone equals or
   exceeds the corridor's own measured export capability. In PNW 2024/2025 the
   net-flow floor is **positive** (+67.6 / +46.4 MW) at the median: even at
   *full permitted absorption* the corridor stays a net importer, so the whole
   absorbed quantity is same-node injection. That residual **is** caiso-138 §C's
   firm overreach (permitted absorption 6.7/3.6 TWh PNW against 11.7/12.5 TWh
   forced).
3. **It would make the pre-registered P2 pass by construction.** P2 was written
   as *"the gate that distinguishes a bounded, measured outlet from the
   caiso-138 §E unbounded U-turn"*, and both its limbs (0 MW in closed hours;
   annual energy ≤ Σ E) become identities under the bound. Arming it would
   **disarm the only gate that detected the defect while ~half the defect
   persists** — rule 1 [R-STRUCT]'s "never reach the right number through a
   mechanism that isn't real", in its sharpest form.

**D1c: REFUSED.** Not because it fails a gate, but because it *guarantees* the
gate.

## §D — D2/D3: how much of arm B was ever export, and the bounded arm's C3a

Arm B's `hourly/network_*.parquet` is gitignored (rule-15 slim bundle), so its
per-corridor split is caiso-142 §J's binding record. What **is** committed is
arm B's `class_hourly` `import` class — the *signed* sum over both nodes' rows,
i.e. the seam's net interchange — which measures the aggregate directly:

| year | arm B net import TWh | **net-export h** | net-export TWh | closed-env txn h (§J) | gross export h (§J) | measured net-exp h |
|---|---|---|---|---|---|---|
| 2023 | 29.500 | **1,546** | 2.128 | 1,562 | 5,022 | 1,206 |
| 2024 | 31.179 | **981** | 1.084 | 2,156 | 6,284 | 972 |
| 2025 | 36.542 | **409** | 0.318 | 2,341 | 5,137 | 769 |

Arm B's sink transacted in **5,022/6,284/5,137** corridor-hours but the seam was
a net exporter in only **1,546/981/409** — **30.8 / 15.6 / 8.0 %**. (Aggregate
over both corridors, so a lower bound on per-corridor net-export hours; it is
independent corroboration of §J from bytes that *are* committed.)

**D3 — the bounded arm's price prediction.** A bound can only *reduce*
absorption, so arm B's realised C3a move is the upper bound and 0 the lower;
apportioning by the absorption a closed-hour bound removes (§J's own census):

| year | arm B Δnet TWh | closed-h absorption removed | kept share | arm B C3a | **bounded C3a prediction** |
|---|---|---|---|---|---|
| 2023 | 6.928 | 2.251 TWh | 67.5 % | +3.401 | **+2.296** |
| 2024 | 9.520 | 3.477 TWh | 63.5 % | +4.172 | **+2.648** |
| 2025 | 5.817 | 3.716 TWh | 36.1 % | +2.649 | **+0.957** |

**C3a-2024's band headroom is $0.69** (keeper gap +2.768 against a ±$3.46 band).
The bounded arm is predicted at **+2.648 — 3.8× the headroom**, so it leaves the
band exactly as the unconstrained arm did. The sign is unchanged and not
re-litigated (caiso-142 §C monotonicity: an absorber can only raise λ).

**D3: FAIL.** **D4: zero fitted values** — no parameter was swept, and none is
introduced.

## §E — the price re-basis is **not identifiable without a fitted value**, and it **corrects caiso-142 §I**

For the export leg to be re-based the way caiso-93/94 based the *import* leg, the
measured `actual CAISO RT − raw hub` spread in real net-export hours must be
stable enough to pick one static constant *without choosing*, and the right sign
for a price-taking sink. Measured, with the **import** direction of the same
series as the standard the mirror has to meet:

| corridor | year | n | p25 | **p50** | p75 | IQR | mean | sd |
|---|---|---|---|---|---|---|---|---|
| PNW | 2023 | 4,341 | −14.44 | **−3.56** | +7.88 | 22.32 | +0.51 | 35.06 |
| PNW | 2024 | 3,224 | −21.11 | **−8.30** | −0.83 | 20.28 | −12.48 | 23.13 |
| PNW | 2025 | 2,560 | −15.49 | **−7.40** | −0.94 | 14.55 | −9.07 | 13.31 |
| DSW | 2023 | 474 | −4.08 | **+3.69** | +11.06 | 15.13 | +5.56 | 41.17 |
| DSW | 2024 | 459 | −4.07 | **+4.39** | +11.79 | 15.86 | +3.84 | 13.30 |
| DSW | 2025 | 405 | −0.85 | **+4.49** | +10.69 | 11.54 | +4.77 | 9.98 |

| reference (import direction, same series) | p50 | IQR |
|---|---|---|
| PNW 2023 / 2024 / 2025 (n = 4,097/5,226/5,885) | −1.98 / −3.23 / −2.97 | 28.20 / 10.40 / 9.62 |
| DSW 2023 / 2024 / 2025 (n = 8,170/8,181/8,257) | −0.24 / −0.86 / −0.70 | 24.70 / 12.61 / 11.43 |

**The dispersion argument does NOT discriminate** — the import basis was read
off a distribution with a comparable IQR (9.6–28.2), so wide spread alone is no
objection. Recorded because it cuts against the convenient conclusion. What does
discriminate is three things:

1. **Across-year instability, PNW.** p50 range **$4.74** (−3.56/−8.30/−7.40)
   against the import basis's **$1.25** — 3.8×. Any single constant is a *choice
   among three*, i.e. a fitted value (rules 21/24).
2. **Congestion structure.** Median spread by cell (shallow/deep/summer/winter/
   on-peak/off-peak) ranges **$10.48 / $9.67 / $7.70** (PNW 2023/24/25) and up to
   **$12.88** (DSW 2024), with a 2023 PNW **sign flip** (winter +5.80 vs summer
   −3.49) and a monotone depth gradient (shallow −1.01 → deep −4.68). A delivery
   basis should not track congestion; this does, so it is a congestion rent being
   relabelled as a wheel.
3. **The DSW sign refutes the form outright.** CA RT is *below* the hub in only
   **38.0 / 35.1 / 27.9 %** of real DSW net-export hours (PNW: 60.6 / 77.5 /
   78.6 %). A sink priced off the hub can only export when CA < hub, so it cannot
   reproduce 62–72 % of reality's DSW exports **at any level** — those exports
   are contractual/wheeling, not price-driven.

**This corrects caiso-142 §I part 2** (and the same sentence in PREREG-caiso142
§0.4 and the matrix note): its claim that `hub − ε` *"over-prices the outlet on
**both** corridors"* holds only for **PNW**. On DSW the measured spread is
**+$3.69/+4.39/+4.49**, i.e. `hub − ε` **UNDER**-prices the DSW outlet by ~$4.4,
so a re-basis there would make the DSW sink **more** in the money and **worsen**
the U-turn. The stable DSW constant (range $0.80) is therefore the *wrong-sign*
one, and the unstable PNW constant is the only one that would help.

**Re-basis verdict: NOT DERIVABLE** from the measured record without a fitted
value. The brief's second stop condition is met.

## §F — the deeper result: a **sound** node-level export constraint **does not exist** in this model class

"Sound" = every MWh the sink books as an export is energy that actually left
CAISO: `−S[t] ≤ max(0, −flow[t])`. By §A's exact identity, `flow` and the node's
net interchange are the same variable combination, so this is a joint condition
on `(flow, S)`. It is **non-convex**, demonstrated on the corridor's own scale:

| point | flow | S | sound? |
|---|---|---|---|
| endpoint 1 (net import, sink off) | +2,100 MW | 0 | **yes** |
| endpoint 2 (net export 500, sink takes 500) | −500 MW | −500 MW | **yes** |
| convex combo λ = 0.50 | **+800 MW** | **−250 MW** | **NO — resale** |
| convex combo λ = 0.75 | **+1,450 MW** | **−125 MW** | **NO — resale** |

An LP's feasible region is convex by construction. Therefore:

* **No set of linear rows** — node-level, link-level, hourly, monthly,
  per-corridor or grouped — can express soundness. The exact condition is the
  disjunction `{flow ≥ 0 ⇒ S = 0} ∨ {flow < 0 ⇒ −S ≤ −flow}`, which needs a
  binary (a MIP) and is **forbidden by the stack rules**.
* Its tightest **linear surrogate**, `−S ≤ −flow` imposed unconditionally,
  reduces via the §A identity to `F + I_econ ≤ 0` — **infeasible** while the
  must-flow block `F > 0` (§B: 11.7 + 15.6 TWh in 2024).
* Its convex **hull** contains the resale points above: the best any LP
  relaxation can do is permit exactly the behaviour being excluded.

**So the charter's prerequisite (a) is not merely redundant — it does not
exist.** And the dependency **inverts**: the forced injection must go elastic
**first**, after which no new constraint is needed at all — because with `F = 0`
the resale channel is precluded by the **objective** itself (§B: buy-to-resell
loses `wheel + 2ε` per MWh), and the already-armed net bound still bounds the
physical flow. *Not* because the surrogate becomes usable: at `F = 0` it
collapses to `I_econ = 0`, which would forbid legitimate imports too. The
surrogate is over-strong at every `F`; what changes is that there is nothing left
to constrain.

## §G — cross-ISO: the precondition, per node — and **MISO's keeper already has the channel open**

§B identifies the channel's precondition exactly: an absorption row **and** a
price-insensitive (must-flow) injection row **at the same priced node**. Neither
half alone opens it. Measured on each ISO's own committed keeper `run_config`
(rule 25 — a measurement of exposure, never a verdict in another lane; this
refines caiso-142 §F, which censused the *bridge* axis):

| ISO | keeper | rows | pmin<0 | must-flow armed | precondition | sink **live in scored P1** | signed seam < 0 |
|---|---|---|---|---|---|---|---|
| ERCOT | ercot139_cc_committed_arm | 0 | 0 | — | no | — | — |
| CAISO | caiso139_dumpguard_B | 11 | 2 | `caiso_firm_import_selfschedule` | **YES** | **NO** (deleted by the seam) | 0 / 0 / 0 h |
| PJM | pjm137_ctheatrate_B | 80 | 40 | — | **no** | yes | — |
| **MISO** | miso101_tempgrain_B | 64 | 32 | `miso_firm_imports` | **YES** | **YES** | **29 / 577 / 1,182 h** |
| NYISO | nyiso99_demandfix | 8 | 1 | `nyiso_firm_imports` | **YES** | **NO** (deleted by the seam) | 0 / 0 / 0 h |
| NEISO | neiso61_netrev_margin | 9 | 3 | — | **no** | yes | — |

Per-node, for the three that meet it: CAISO `WECC_DSW` (1 sink + 7 injects) and
`WECC_PNW` (1 + 2); MISO `MISO_external` (**24 sinks + 24 injects**, including
the `ref_import_Manitoba_t*` must-flow block) and `MISO_external_South` (8 + 8);
NYISO `NYISO_external` (1 + 7, including `HQ_hydro`).

Three readings, all measurement:

1. **PJM and NEISO cannot resell** despite carrying 40 and 3 absorption rows —
   they arm **no** must-flow import injector, and §B shows an all-economic node
   cannot resell at any sink price. caiso-142 §F called them "latent" on the
   bridge axis; on the **resale** axis they are *not* exposed at all.
2. **CAISO and NYISO meet the precondition but their sinks are pinned off** by
   the very seam bug caiso-142 fixed flag-gated — so the channel is currently
   closed **by the bug**, and their signed seam totals never go negative
   (0 hours, all years). For NYISO this inverts the usual reading: *arming* the
   seam fix there would **open** the channel, so the pinned state is the safer
   of the two until its own lane decides. Nothing changes for it here — the fix
   is CAISO-flag-gated.
3. **MISO is the one ISO where the channel is structurally OPEN in the scored
   keeper today**: 24 live sinks alongside 24 injects (Manitoba firm must-flow)
   at one node, **no P1-native bridge to delete them**, and its signed seam total
   goes negative in **29 / 577 / 1,182 hours** (2023/24/25) — rising. caiso-142
   §F called MISO "latent"; on this axis it is **live**, which is a correction
   worth handing to that lane. **What this does and does not show:** the
   precondition is met and the sinks are live; whether the channel is *exercised*
   (gross absorption against same-node injection, as caiso-142 §J measured for
   CAISO) needs unit-level rows, and MISO's slim bundle carries none — that
   measurement is MISO's lane's to make, on its own keeper. No verdict is entered
   in its cell.

## §H — what this changes on the record

* **Keeper unchanged**, NOT-YET, fail {C3a-2025, C3c}. No dashboard
  registration due (rule 15 applies to completed runs — the
  caiso-134/135/140/141/142-§A–§F disposition; nothing solved).
* **No code change.** No `ScenarioConfig` field, no LP row, no cache-key entry,
  no test — the chartered mechanism is proved non-existent (§F), so a flag for
  it would be dead code (rules 24 `[R-REGISTRY]` / 26 `[R-DELETE]`).
  `ScenarioConfig().cache_key()` is untouched by this branch.
* **The prerequisite ORDER in caiso-142 §J is corrected.** Its list was
  (1) node-level constraint → (2) export re-basis → (3) firm-block elasticity.
  (1) does not exist (§A/§F) and (2) is not derivable (§E), so the correct list
  is: **(a) caiso-138 §C firm-block elasticity — the only real prerequisite;
  (b) then re-examine whether any sink is wanted, using the net bound already
  armed.** The same correction applies to `docs/calibration-log/caiso.md`'s
  caiso-142 disposition bullet 6 and to the matrix note.
* **caiso-138 §E's refusal is re-confirmed a second time, on a stronger basis.**
  caiso-142 §J confirmed it by measurement; §F here shows it is not a
  measurement outcome but a **model-class impossibility** for as long as the
  firm block is forced.
* **caiso-142 §I part 2 is corrected, not withdrawn** (§E): PNW over-priced,
  **DSW under-priced by ~$4.4**, so "both corridors" is wrong and the DSW
  re-basis has the wrong sign.
* **Rule 28:** new row `caiso_node_export_constraint` — CAISO **G**
  (closed-no-mechanism: non-convex, not LP-representable), ERCOT **·** (0
  interchange rows, caiso-142 §F), PJM/MISO/NYISO/NEISO **U** (their own lanes,
  rule 25 — including MISO, whose §G exposure is measured but whose verdict is
  its own). The `caiso_p1_export_sink_seam` row's "what a future arm needs
  first" list is corrected, and `caiso_corridor_export_path`'s note records that
  its limb-(a) bound is a **net-flow** bound (never a sink bound).
* **The cross-ISO exposure census is refined on a second axis (§G).** caiso-142
  §F censused the *bridge* axis (does the seam delete the sink?); §G censuses the
  *resale* axis (do an absorption row and a must-flow injection meet at one
  node?). They disagree in three places, all measurement: **PJM and NEISO are
  NOT exposed** on the resale axis (no must-flow injector at all, so their 40/3
  absorption rows cannot resell); **NYISO** meets the precondition, so arming the
  seam fix there would *open* the channel; and **MISO's keeper already has it
  open** — 24 live sinks alongside the Manitoba must-flow block at
  `MISO_external`, no bridge to delete them, signed seam negative in
  29/577/1,182 hours and rising. Handed to those lanes; nothing changed for them
  here (the seam fix is CAISO-flag-gated).
* **Rule 22 [R-HOLDOUT]:** 2023–2025 only; no out-of-training year touched.
* **Pre-existing, not this session's:** the default `cache_key` drift
  (`603c2498bf71d21d` pinned vs `2c8098e8e1684c7d` on main, 4 tests),
  `tests/regression/test_fleet_arrays_golden.py`, stale `status/NEISO.js`, and
  the D-1 ST_GAS 2024/2025 FAIL inherited from the keeper.

## §I — DO-NOT-REDO (new, binding; extends caiso-142 §H)

* **Proposing a node-level (or any other) LP constraint to make an export sink
  sound.** §F: the soundness set is non-convex, its tightest linear surrogate is
  infeasible while the firm block is forced, and its convex hull permits the
  resale it is meant to forbid. This covers hourly, monthly, per-corridor,
  grouped, net-interchange and gross-throughput forms. Cite §F rather than
  re-deriving; do not re-open on the grounds that a *different* row granularity
  might work.
* **Citing `rows.py:1416` / `_build_import_node_rows` as the machinery for a
  directional export bound.** §A: it is a monthly net-throughput *band*
  (the NYISO EIA-930 reconciliation design), and a node net bound is in any case
  redundant with the corridor group's `limit_dn`.
* **Arming a gross absorption bound at the measured export envelope.** §C: it
  leaves resale in 31.7–51.4 % (PNW) / 7.4–39.8 % (DSW) of transacting hours —
  exactly the hours the must-flow block over-delivers — while making the
  pre-registered P2 gate pass by construction.
* **Re-basing the export leg's price off the measured export-hour spread.** §E:
  PNW is congestion-structured and year-unstable ($4.74 range, $7.70–10.48 cell
  range, 2023 sign flip); DSW is stable but the **wrong sign** and cannot
  reproduce 62–72 % of reality's DSW exports at any level. Any single constant
  is a fitted choice.
* **Saying `hub − ε` over-prices the outlet on "both corridors".** §E: PNW yes,
  **DSW is under-priced by ~$4.4**.
* **Re-measuring** the node identity, the `limit_dn`/envelope equality, the
  must-flow census, the `F ≥ E` shares, arm B's net-export hours, the export- or
  import-direction spreads, the convexity demonstration, or the cross-ISO
  precondition census. The committed probe carries all of them;
  §A/§D/§E/§F/§G reproduce in seconds, §B/§C in ~6 minutes (three fleet
  reconstructions).
* **Calling PJM or NEISO exposed to the resale channel** (§G: they arm no
  must-flow import injector, and an all-economic node cannot resell), or calling
  **MISO merely "latent"** (§G: its keeper's sinks are live alongside the
  Manitoba must-flow block, no bridge deletes them).
* **Reading arm B's per-corridor flows from its bundle.** §D: its
  `hourly/network_*.parquet` and `unit_hourly_*.parquet` are gitignored
  (rule-15 slim bundle); caiso-142 §J is the binding per-corridor record, and
  `class_hourly`'s `import` class is the committed aggregate substitute.

Carried forward unchanged: everything in `FINDING-caiso142` §H (including its
first bullet — an absorption column can only raise λ — which this finding does
not touch), `FINDING-caiso141` §G, `FINDING-caiso140` §G, `FINDING-caiso139` §G,
`FINDING-caiso138` §G (both sink re-arm forms remain refused; §F now supplies the
model-class reason), `FINDING-caiso137b` §6, caiso-137 §7 first bullet,
`FINDING-caiso136` §5, caiso-135 §10, caiso-134 §9, caiso-133 §9, caiso-132 §10,
caiso-131 §10, caiso-130 §7, caiso-129 §6, caiso-127 §7.

Next number: caiso-144.
