# nyiso-180 — the per-generator prerequisite is LIFTED, and it REFUTES the object three sessions were chasing: against its own offer the model dispatches **99.2 %** of the in-the-money `ST_GAS`, not 52–77 %, and the failing gate is an **OVER**-generation miss

**Session:** nyiso-180, NYISO backcast-calibration track, 2026-09-03.
**Keeper: UNCHANGED — `2026-09-02-nyiso-177-vintage-matched`.** This session's
run is registered as an **instrument probe**, explicitly NOT a keeper candidate
(§8).
**Run registered (rule 15):** `2026-09-03-nyiso-180-unit-dispatch`, bundle
`results/calibration/nyiso180_unitdispatch`, NYISO 2023–2025, one invocation,
years sequential.
**Gates:** `results/calibration/PREREG-nyiso180-per-generator-dispatch.md`,
committed and pushed at `2966b0c4` **before the first solve**, predictions and
falsifiers fixed in advance.
**Machine artifacts:** `results/calibration/_nyiso180_unit_dispatch.json`,
`_nyiso180_mc_reconstruction_gap.json`, `_nyiso180_topdecile_decomposition.json`;
probe `scripts/probes/nyiso180_unit_dispatch_adjudication.py`.

---

## 1. The one-paragraph answer

The prerequisite the lever queue named for three consecutive sessions is lifted:
`hourly/unit_hourly_<year>.parquet` now carries the solve's **own** installed
offer (`mc`) and the generation columns' **reduced cost** (`red_cost`), so the
generation column's stationarity identity closes per unit-hour and a diagnostic
can say not just *that* a unit did not run but *what charged it*. Measured on
it, **the nyiso-179 §6.1 object does not exist.** Against the LP's own offer the
model dispatches **0.992 / 0.991 / 0.992** of the `ST_GAS` it puts in the money
— not 0.767 / 0.522 / 0.740 — and the un-run in-the-money volume is **0.073 /
0.061 / 0.070 TWh**, not 3.84 / 9.09 / 3.99 TWh. Two orders of magnitude. The
identity closes **exactly** (§2.4 STOP population: 0 unit-hours in all three
years; Ω p95 = 3e-6 $/MWh), which closes candidates **(a)** the zonal loss
surface, **(b)** a post-solve price transform and **(c)** an in-LP capacity-basis
mismatch together. The carrier is a **reconstruction gap**: nyiso-179's `mc`,
rebuilt outside the solve, is **cheaper** than the offer the LP installed in
**97.6 / 97.3 / 88.2 %** of `ST_GAS` unit-hours, by a mean of **\$11.45 / \$17.25
/ \$5.43 per MWh**. And the consequence is larger than one refuted object: with
the offer corrected, **the failing gate is an OVER-generation miss** — C1-2023
`ST_GAS` is the model running **+3.53 TWh MORE** steam than measured (top decile
2,339 MW model vs 2,114 MW measured) — while nyiso-177/178/179 spent three
sessions hunting an *under*-generation explanation that the artifact had
manufactured.

---

## 2. The instrument (deliverable 1)

`DispatchResult` gains two fields and the sidecar two columns:

* **`gen_mc` → `mc`** — the `(n_gen, T)` marginal-cost array the solve installed
  in its objective. The LP's own offer, not a reconstruction of it.
* **`gen_reduced_cost` → `red_cost`** — the generation columns' HiGHS reduced
  cost, float32, HiGHS-raw. The exact twin of the already-retained `flow_dual`
  for the `P` block.

Joined to `hourly/system_<year>.parquet`'s zonal `price`:

```
red_cost[g,t] = mc[g,t] − price[zone(g),t] + Σ_r a(r,g)·y_r
Ω[g,t]        ≡ red_cost[g,t] − (mc[g,t] − price[zone(g),t])
```

`Ω` is the net rent every **non-energy** row charges that unit-hour, exactly and
with no free parameter; `sign(red_cost)` says which bound the column sits at.

### 2.1 Inertness — proven, not asserted (PREREG §4)

| check | result |
|---|---|
| cache keys at HEAD+change | `4c6b03ae098b6e3e` / `8211c72bb1960adc` — **identical** to the capx-D44 pins. No `ScenarioConfig` field added. |
| byte-identity control, **with links** | **BYTE-IDENTICAL** on every primal and dual + objective |
| byte-identity control, **without links** | **BYTE-IDENTICAL** — and this is the branch that actually changed behaviour (it did not convert `col_dual` before and now does) |
| suite | `test_dispatch.py` + `test_p1_floor_inplace.py` + `tests/unit/pipeline` — **314 passed** |
| gate reproduction | every substantive criterion of the replayed keeper reproduces exactly (§8) |

## 3. The adjudication

All figures from `_nyiso180_unit_dispatch.json`, ST_GAS, P1, 93 LP unit rows.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`R` (dispatched ÷ in-the-money), LP's own offer** | **0.992** | **0.991** | **0.992** |
| nyiso-179's `R`, reconstructed offer | 0.767 | 0.522 | 0.740 |
| un-run in-the-money | **0.073 TWh** | **0.061 TWh** | **0.070 TWh** |
| nyiso-179's un-run | 3.84 TWh | 9.09 TWh | 3.99 TWh |
| §2.4 STOP population (identity fails to close) | **0** | **0** | **0** |
| Ω p50 / p95 (\$/MWh) | 0.0 / 3e-6 | 0.0 / 3e-6 | −0.0 / 4e-6 |

**Ω is essentially identically zero.** No non-energy row charges this class in
any material way. The LP is a clean merit-order dispatch for `ST_GAS`, and the
residual 0.06–0.07 TWh is **LP indifference at the margin**: 94.5 / 92.3 / 78.7 %
of it sits within \$1/MWh of the clearing price, and at a strict \$1 margin
`R` = **0.9995 / 0.9992 / 0.9981**.

### 3.1 Candidate (b) — post-solve price transform: **CLOSED**
Code (checked before any solve): `prices = row_dual[: n_zones*T]`, the raw
energy-balance dual; `_system_frame`'s `total_overlay` and every contributing
term sit inside `if iso == "ERCOT"`. Measurement: the median of `mc − price`
over **interior** (LP-marginal) `ST_GAS` unit-hours is **exactly 0.000** in all
three years. A transform would displace the median. **Closed.**

### 3.2 Candidate (a) — the armed `nyiso_zonal_loss_surface`: **CLOSED**
Code: the loss fraction scales the **receiving-end incidence of lossy LINK
columns**; a generator enters its own zone's balance row at exactly `+1`. There
is no injection-side delivery factor, so `mc ≤ price_z` was already the correct
test. The same zero median confirms it. **Closed.**

### 3.3 Candidate (c) — capacity-basis mismatch **inside the LP**: **CLOSED**
`max(mw − cap_mw)` = **3.1e-5 MW**; zero unit-hours exceed the cap; the share of
un-run in-the-money MW sitting at an **upper** bound is **0.0 / 1e-6 / 2e-6**.
The sidecar's `cap_mw` and the LP's own bound are the same object. **Closed.**
*(The mismatch that mattered was between the LP and nyiso-179's EXTERNAL
reconstruction — §4 — not inside the LP.)*

## 4. The carrier — a reconstruction gap, measured

`_nyiso180_mc_reconstruction_gap.json`, ST_GAS, 770,880 matched unit-hours/yr:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| share of unit-hours where the **LP's offer is DEARER** than nyiso-179's | **97.6 %** | **97.3 %** | **88.2 %** |
| mean (LP − reconstruction), \$/MWh | **+11.45** | **+17.25** | **+5.43** |
| median | +9.57 | +15.39 | +11.98 |

A dearer offer puts **less** capacity in the money, which is exactly the
direction needed: nyiso-179 computed its in-the-money envelope against an offer
the LP never used, so its `ITM` was inflated and its `R` correspondingly
deflated.

**One missing step is identified by name.** `apply_gas_offer_margin`
(`data/offer_curves.py`) is called by the solve path immediately after
`assemble_mc` (`run_calibration.py:3931`, `runner.py:2494`) and mutates `mc` in
place by `markup_hr × (anchor − fuel)`. nyiso-179's `build_year` calls
`resolve_fuel_prices` then `assemble_mc` and **stops** — it never applies it.
This keeper's anchor is \$3.9046/MMBtu and its gas averaged \$2.54 / \$2.19 /
\$3.52, i.e. **below** the anchor in every year, so the omitted step makes the
reconstruction cheaper — and the ordering matches, 2024 (furthest below the
anchor) being the year nyiso-179's `R` was most extreme.

**Stated against my own convenience: this does NOT close the gap.** Adding
`apply_gas_offer_margin` back leaves a residual mean of **+\$7.58 / +\$11.53 /
+\$12.29**/MWh, and in 2025 the residual is *larger* than the raw gap. So **at
least one further channel between `assemble_mc` and the installed objective is
unidentified**, and it is left open rather than guessed. What is established is
sufficient for the verdict: the reconstruction is not the LP's offer, so nothing
computed on it about this class is evidence.

## 5. Predictions graded at full magnitude, misses included

| prediction | bar | measured | verdict |
|---|---|---|---|
| **P-b/P-a** median `mc − price` on interior unit-hours | ≤ \$0.01 | **0.000 / 0.000 / 0.000** | **PASS** |
| **P-b** mean `mc − price` | ≤ \$0.05 | −0.071 / +0.014 / **−0.127** | **FAIL 2 of 3 years** |
| **P-c** un-run share at an upper bound | < 10 % | 0.0 / 1e-6 / 2e-6 | **PASS** |
| **P-c** `max(mw − cap_mw)` | ≤ 1e-3 MW | 3.1e-5 | **PASS** |
| **P-d** un-run share at a **lower** bound | ≥ 70 % | **5.8 / 16.5 / 29.8 %** | **FAIL, badly** |
| **P-d** headroom occupancy beats ramp | — | reserve `pearson r` = **0.010 / 0.025 / −0.007**; ramp share 1.1 / 4.3 / 9.6 % | **FAIL — neither** |

**P-b's mean bar failed in two years while its median passed in all three.** The
mean is computed over only 3,220–4,533 interior unit-hours and is moved by tails
(`p95_abs` \$1.77–2.39); the median is the statistic that discriminates a
systematic transform, and it is exactly zero. I record the mean miss rather than
re-cutting the bar, and note that a bar whose median twin passes cleanly was the
wrong summary statistic to have pre-declared.

**P-d was my ranked prior and it is comprehensively wrong.** The un-run MW is
dominated by **interior** (marginal) columns — 94.2 / 83.5 / 70.2 % — not
lower-bounded ones, and my named favourite, reserve shared-headroom occupancy,
has **no relationship at all** to it (held/un-run ratio 1,404–1,682×, correlation
≈ 0). The honest reading is that once the offer is the LP's own, there is no
withheld population left to explain, so the mechanism I predicted had nothing to
do.

## 6. The consequence — the lane has been chasing the wrong sign

`_nyiso180_topdecile_decomposition.json`, and annual model-vs-measured:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model − measured `ST_GAS`, annual | **+3.53 TWh** | −0.91 TWh | −3.57 TWh |
| top decile: measured CAMPD | 2,114 MW | 2,405 MW | 2,597 MW |
| top decile: model dispatch | **2,339 MW** | 1,884 MW | 1,815 MW |

**The ONLY C1 failure is 2023 `ST_GAS`, +3.86 TWh, and it is the model running
TOO MUCH steam** — confirmed against the scorer: `FAIL 2023 ST_GAS: +3.86 TWh,
share +3.2pp [MODEL MISS]`, with 2025 `ST_GAS` **SKIPPED** (preliminary EIA-923
vintage, not gated). nyiso-177/178/179 all framed the object as *why does
in-the-money steam not run* — an under-generation question — and that framing
came from the reconstruction artifact. In the failing year the model over-runs
steam, in the dear hours included.

**nyiso-179 §7's decomposition is superseded**, because it was computed on the
refuted offer. Recomputed on the LP's own offer, 2025 top decile (mean actual
\$176.25 — nyiso-179's own figure, an independent cross-check that the two
windows agree): measured 2,597 MW, in-the-money at the **actual** price **2,665
MW**, at the **model's** price 1,594 MW, model dispatch 1,815 MW. Offer position
is no longer a deficit at all (**−8.7 %** of the gap: at the real price the
model's offer would clear slightly *more* than the market ran), and the model
runs *more* than its own price justifies (**−28.2 %**), which is the floors and
the commitment bridge. The whole 2025 top-decile gap, and more (**137 %**), is
the model's own price level — which is C3a, owner-court, and unchanged. The
2023 column of the same table has a **negative** total gap (−225 MW): the model
over-runs there too.

## 7. Sidecar size — the pre-registered gate, honoured against me

PREREG §1: *"if a year's frame exceeds 5 MB the layer is reported and NOT
committed, and the finding says so."* It does.

| | per year | bundle |
|---|---|---|
| full `unit_hourly` layer | **16.36 / 17.36 / 17.36 MB** | **51.1 MB** |
| of which `red_cost` | 14.75 MB (90 %) | — |
| of which `mc` | 0.73 MB | — |
| pre-nyiso-180 frame (`mw`+`cap_mw`+labels) | ~0.87 MB | 2.6 MB |

So **the full layer is NOT committed**, per my own gate. `red_cost` is 2.73 M
distinct float32 duals — genuinely incompressible, and that is the honest price
of the instrument. What **is** committed is the **`ST_GAS` slice**
(`hourly/unit_hourly_stgas_<year>.parquet`, **2.55 / 2.66 / 2.67 MB**, 7.88 MB
total, `git add -f` per the `.gitignore` §8 opt-in), which is the population
under study — so every number in this finding is reproducible from committed
artifacts with no replay. The stale `.gitignore` note claiming "920 KB/yr
(unit)" is corrected in the same commit; it described the pre-`red_cost` frame.

## 8. Keeper judgment — **NOT a keeper candidate; do not promote**

The brief's standing test is right ("structural integrity improves but gates
regress may still be a keeper"), and it does not fire here, because **model
structural integrity does not improve at all**:

1. It is a **replay of the keeper's own recipe** — zero mechanism change, zero
   parameter change, zero new DOF. Every substantive criterion reproduces the
   keeper **exactly**: `fuelmix` FAIL, `price_mean` FAIL, `price_tail` FAIL;
   `sysvol`, `price_shape`, `dispatch_corr`, `forced_share` PASS.
2. The only gate that moves, moves **backwards**: `governance` PASS →
   **UNATTESTED**, because `replay_keeper.py` regenerates no
   `calibration_attestation.json`. Promoting would swap a governance-attested
   bundle for an unattested one.
3. Its one differentiator — the per-generator layer — is **not committed** (§7),
   so the promoted bundle would carry no dashboard advantage either.

The improvement here is to the **instrument**, which lives in the merged code
and benefits every future run of every ISO regardless of which bundle is the
keeper. Keeper stays `2026-09-02-nyiso-177-vintage-matched`; determination
NOT-YET, unchanged, on the same three criteria.

## 9. Honest expected value

**Delivered.** The three-session prerequisite is lifted, on a change proven inert
four ways including a byte-identical control on the one branch whose behaviour
actually changed. All three §6.1 candidates are closed, on measurement, on bars
fixed before the bundle existed. The object they were candidates *for* is
refuted at two orders of magnitude, its carrier is identified as a
reconstruction gap and quantified, and one contributing step is named in code.
The lane's sign error is surfaced and the failing gate correctly characterised
as over-generation. nyiso-179 §7's decomposition is recomputed on the correct
basis.

**Not delivered, without softening.** **No keeper, no candidate, no repair.**
C1-2023 `ST_GAS` is exactly where nyiso-177 left it, +3.86 TWh, and nothing here
reduces it by a MWh — this session only establishes that it is the *opposite
sign* to what the last three assumed. The reconstruction gap is **not fully
attributed**: `apply_gas_offer_margin` is one named missing step and it does not
close the residual, so at least one channel between `assemble_mc` and the
installed objective is still unidentified — a reader should not take §4 as a
complete account. Two of my six pre-registered predictions failed, one of them
(P-d) comprehensively. The full unit layer is not committed, so a successor
interrogating a class other than `ST_GAS` must re-solve. C3a-2025 remains
owner-court and untouched.

## 10. Handed forward

1. **RE-AIM THE LANE AT 2023 OVER-GENERATION.** The failing C1 cell is the model
   running +3.86 TWh too MUCH `ST_GAS` in 2023. Enumerate what forces steam on
   (the `legitimacy_diagnostics.json` D-2 attribution; the gas commitment
   bridge's `gas_st` leg floors 0.163 TWh, so the bulk is elsewhere) and whether
   the 2023 offer level is too cheap. **Do not open another under-generation
   lever.**
2. **FINISH ATTRIBUTING THE RECONSTRUCTION GAP** (§4) — the residual after
   `apply_gas_offer_margin` is +\$7.58 / +\$11.53 / +\$12.29/MWh and is
   unidentified. Cheap now: diff the sidecar's `mc` against a step-by-step rebuild.
3. **EVERY PROBE THAT REBUILDS AN OFFER OUTSIDE THE SOLVE IS SUSPECT.** The
   sidecar's `mc` is now the reference; nyiso-178's and nyiso-179's instruments
   share the `build_year` construction and their class-level offer claims should
   be re-checked against it before being cited again.
4. **CLOSED:** §6.1 candidates (a), (b), (c) — all three, on measurement.
   DO-NOT-REDO.
5. **UNCHANGED and not opened:** C3a-2025 (owner-court); C3c; the nyiso-178/179
   DO-NOT-REDO list (`gas_st_committed_hr_mult` / caiso-239 transfer, the
   downstate gas basis + `dual_fuel_switching` dear hours, the `peak` 4.20).

## 11. Governance

* **Rule 1 `[R-STRUCT]`** — no residual chose what to measure; no mechanism
  adopted or rejected on fit. The instrument landed regardless of outcome.
* **Rule 13 `[R-MEASURED]`** — nothing pinned to actuals; CAMPD and the RT LBMP
  are comparison bases only.
* **Rule 15 `[R-DASHBOARD]`** — the run is registered
  (`2026-09-03-nyiso-180-unit-dispatch`) and committed in this session, marked
  `(PROBE)`.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, one invocation, one bundle.
* **Rule 21 `[R-DOF]`** — **zero free parameters.** No band swept, no scalar
  fitted, no DOF entry added.
* **Rule 22 `[R-HOLDOUT]`** — training window only; no out-of-training year
  solved, scored or registered; freeze untouched; no marker requested.
* **Rule 24 `[R-REGISTRY]`** — no new `ScenarioConfig` field, no env knob, no
  gate. The columns are unconditional because a write-only output cannot change
  a solve (§2.1).
* **Rule 25 `[R-ISO-SCOPE]`** — the sidecar is ISO-agnostic by construction (the
  LP's own output in the shared writer); only the NYISO matrix shard edited.
* **Rule 27 `[R-PUSH]`** — the three ≥300-line files were edited locally and
  pushed as exact on-disk bytes, blob-verified after the push (line count +
  hash) before any further commit.
* **Rule 28 `[R-MECH-MATRIX]`** — `unit_network_layer_sidecar`'s NYISO cell
  re-stamped (§12).

## 12. Matrix (rule 28 b)

`unit_network_layer_sidecar` NYISO cell re-stamped. It read **`K`** on the
strength of nyiso-116, i.e. "the per-unit layer is COMMITTED for NYISO" — but
**no NYISO `unit_hourly` parquet has been tracked in git since that bundle was
pruned under top-15 retention** (the only tracked one in the repo today is
NEISO's 2022). That stale cell is a large part of why three sessions recorded
the layer as an unavailable prerequisite while the matrix said it was in hand.
**Standing lesson: a `K` earned by committing an artifact inside a bundle is
only as durable as the bundle's retention slot** — retention pruning silently
un-does it, and nothing re-checks the cell.
