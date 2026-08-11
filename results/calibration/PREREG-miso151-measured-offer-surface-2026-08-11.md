# PREREG — miso-151: a MISO `measured_offer_surface`, POSITION-conditioned, SHAPE-ONLY, subsuming `gas_offer_margin`

**Session** miso-151 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(`miso148_basis_B`) · **Date** 2026-08-11 · **Owner charter given in session**
(item 9, full-year corpus variant), recorded in
`results/calibration/DECISION-miso151-item9-measured-offer-surface-2026-08-11.md`
§10 option 1 and re-confirmed in plain terms after the owner asked for the ask
to be simplified.

**Pushed BEFORE any adjudicating statistic.** Everything read or computed prior
to this registration is disclosed in §10, in full.

---

## 0. Keeper determination, re-verified from committed artifacts

`scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`
(stdlib-only, pre-venv): **NOT-YET**, rubric 3.2, scorable 2023/2024/2025,
**FAIL SET {C3a, C3b}**. C3a 2025 **−15.6 %** (2023/2024 PASS). C3b 2025 NRMSE
**0.212** (gate 0.200; 2023/2024 PASS at 0.082/0.125). C3c CAVEAT, ledgered,
**1 of 1 SPENT**. C1/C2/C4/C6 PASS. C8 PASS with ST_GAS **grounded above
budget** at 34.1/35.8/**48.4 %** and CT_PEAKER-2023 at 16.8 %.

MISO holds **no marker**. Rule 22: **2023–2025 only**, one invocation, all three
years (rule 16).

**Instrument caveat inherited, not re-litigated** (miso-148 K0): the keeper is
**not bit-reproducible at HEAD** (max |Δ| 912.5 MW, ~0.1 % of annual dispatch).
**Every quoted delta in this session is arm-vs-a-SAME-HEAD-CONTROL.** A
zero-delta control is solved first. No arm-vs-committed-keeper delta will be
quoted anywhere.

---

## 1. The object, and the one thing this session is testing

**The missing offer wall** (miso-145 §8, re-measured universe-robust at
miso-150 §8, `JJA_h12_17`, `lo`, universe U1):

| year · market | model wall | real wall | model $/GW | real $/GW |
|---|---|---|---|---|
| 2023 RT | 6.4322 GW | 0.8261 GW | $0.7004 | $51.69 |
| 2024 RT | 8.0215 GW | −0.0078 GW | $1.8809 | $56.06 |
| 2025 RT | **8.3024 GW** | **0.7081 GW** | **$0.7197** | **$73.4591** |
| 2025 DA | 8.3024 GW | 1.0723 GW | $0.7197 | $17.8987 |

**The hypothesis under test.** The model's gas offer curve is too FLAT above the
band it clears in, because the above-base band prices are hand-tuned
multipliers. Replacing that above-base **shape** with the shape MISO's own
submitted book exhibits — measured, class-free, level-free — steepens the model's
supply curve above its clearing point and raises the clearing price toward the
actual.

**What is NOT under test, and is excluded by construction:** the offer LEVEL.
miso-145 measured it NEGATIVE on every instrument, universe, year and
hour-subset (2025 JJA h12–17: RT **−$14.376**, DA **−$8.298**; the 2024 DA cell
is **−2.401** per the authoritative artifact). **Transferring level would move
C3a the WRONG WAY.** This mechanism transfers a within-unit DIFFERENCE, which
cancels level exactly; G-F3 measures that cancellation rather than asserting it.

---

## 2. Footing — reproduce before extend (HARD STOP)

**G-F0.** `scripts/probes/_miso150_universe.py --footing` re-run unchanged.
Bar: **0 fields out of tolerance** (it reproduced miso-145's entire committed
artifact at exactly zero: all six window deficits at Δ 0.0, segment-vs-dense
0.0 on 12 cells).

**G-F1 — corpus integrity across the refetch.** The full-year refetch must not
disturb the landed JJA span. On the JJA subset of the re-curated corpus:
* miso-146's committed intermittent capability at its primary threshold 0.50,
  RT-2025: **7.755 GW** (miso-150 §9 reproduced **7.78 GW**);
* miso-145's committed `_miso145_offer_conduct.json` cells.
Bar: ≤ **$0.01** on price statistics, ≤ **0.05 GW** on MW statistics.

**A footing failure on G-F0 or G-F1 is a HARD STOP.** No new statistic is
computed or reported; the session ends with the footing failure as its finding.

**G-F2 — rule-13 column census (not a formality).** The clean `energy-offers`
partition must carry **ZERO** outcome columns — RT `Cleared MW1`–`Cleared MW12`,
DA `MW`, `Target MW Reduction`. Measured by column-name census over the actual
written partition, not read off `OUTCOME_COLS`. Bar: **0**. A non-zero count is
a HARD STOP.

---

## 3. The corpus, and its extension

**Landed today:** JJA 2023–2025, both markets, 552 files, 429.6 MB.
**This session extends to the full year:** `--months 1 … 12`, 2023–2025, both
markets → **2,190 files**, ~1.7 GB raw, ~1.15 GB clean.

Rule 22: years 2023–2025 only; `--allow-out-of-train` is NOT passed and the
fetcher's own gate would refuse it.

**Disk discipline, declared in advance.** The raw zips and the clean partition
are BOTH disposable derived state (gitignored). The derive's output is a small
JSON artifact. **Phase 0 completes and the corpus is DELETED before swap is
enabled and any LP is solved** — the host has ~12–13 GB writable and a solve
needs 8 GB of swap. This ordering is a constraint on the session, not a
methodological choice, and it is disclosed because it means the corpus is not
resident at solve time.

---

## 4. The construction

### 4.1 The measured object — a within-unit rise, in $/MWh

For each corpus unit-hour and each offer step `j` (cumulative-MW/price
breakpoints 1…10):

```
p_j  =  cum_mw_j / ecomax_mw            own-curve POSITION, (0, 1]
Δ_j  =  price_j − price_1               own-curve RISE, $/MWh
```

`Δ` is a **within-unit, within-hour difference**. It carries no unit identity,
no class, no fuel level, and no market level: a constant shift of a unit's
entire curve cancels exactly. That is the whole reason this is the admissible
transfer and the level is not.

**Conditioning — POSITION, never class** (miso-138 refuted the offer-side class
bridge; the corpus carries 0 fuel/technology columns):

1. **position bin** — `p` on a fixed grid, declared here and frozen:
   `[0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0]`.
2. **system-state bin** — the hour's MISO net-load percentile within the
   training window, on the **registered cross-ISO geometry** `[0.80, 0.90,
   0.97]` → 4 bins. Not re-binned against any residual (rule 23).
3. **delivered-gas bin** — terciles of `data.fuel.trajectories._gas_series`
   over 2023–2025, the same series the `gas_offer_margin` anchor is identified
   on.

**Estimator: capacity-weighted MEDIAN of `Δ` per cell**, weights = the step's
own MW width. Median, not mean or OLS — the caiso-153 attenuation defect and the
PJM/NEISO derive convention (per-unit median-of-ratio + physics segmentation).

**Pooled across all three years and applied identically to every year.** Never
per-year. DA and RT are estimated as **separate surfaces and never averaged**
(miso-145 TRAP 4); the solve consumes the **DA** surface, because a
perfect-foresight hourly LP is the DA market's analogue (the C3c ledger's own
standing reasoning). The RT surface is derived and reported as a sensitivity,
never armed.

**Population rules, fixed here:**
* `ecomax_mw ≤ 0` (the −1.0 sentinel) → **dropped**.
* unit-hours with `self_scheduled_mw ≥ ecomax_mw` (fully self-scheduled — no
  economic curve is being offered) → **dropped**; partially self-scheduled kept.
* must-run-declared unit-hours → **kept**, with an excluded-population
  sensitivity reported.
* steps with non-increasing cumulative MW → dropped as malformed, count
  reported.

### 4.2 The application — a REPLACEMENT, not a stack (rule 19 `[R-ONE-MECH]`)

Armed today: `gas_offer_net_revenue_margin=True`, `gas_offer_margin_anchor
= 3.0492` $/MMBtu (measured, rule-23 frozen, **not a DOF**).
`apply_gas_offer_margin` adds `offer_markup_hr[g] × (anchor − fuel[g,t])`, so
each tranche's conduct margin is the fuel-invariant `offer_markup_hr[g] ×
anchor_g` $/MWh, sourced from the **fitted** `(mult − phys)` multipliers.

The new mechanism replaces that quantity, and only that quantity, on MISO gas
tranches **above the base band**:

```
mc[g, t]  +=  Δ_measured(p̄_g, state(t), gas(t))  −  offer_markup_hr[g] × anchor_g
```

where `p̄_g` is the midpoint of tranche `g`'s own cumulative-MW span over its
plant's `pmax`. Applied after `apply_gas_offer_margin`, on the BASE marginal
cost so P0 and P1 see the same curve, vectorized over the full `(n_gen, T)`
block (rule 2 — no hour loop).

> ### AMENDMENT 2026-08-11 — §4.2's formula above is WRONG and is corrected here, BEFORE any adjudicating statistic
>
> **The defect.** `Δ_measured` is the real unit's **total** own-curve offer
> rise — physical heat-rate rise *and* conduct rise, inseparably, because the
> corpus publishes no heat rates. The formula above removes only the
> **conduct** half of the model's own rise over its base band
> (`offer_markup_hr × anchor`) while adding that **total** measured rise, so
> the model's physical rise above base is counted **twice**.
>
> **The correction, and it is a like-for-like comparison rather than a
> workaround.** Each above-base tranche is re-priced onto its own plant's base
> row plus the measured rise:
>
> ```
> mc[g, t]  :=  mc[base(g), t]  +  Δ_measured(p̄_g, state(t), gas(t))
> ```
>
> where `base(g)` is that plant's FIRST tranche in fill order — the model-side
> analogue of the corpus's `price_1`. Offer-rise is transferred onto
> offer-rise: both sides' physical component sits inside their own rise, and
> the model's base LEVEL, which carries its physical/fuel basis, is untouched.
> The alternative — transferring conduct alone — would require separating the
> real units' physical rise from their conduct rise, which **this corpus cannot
> identify**, so it is not available at any price.
>
> **What this changes about the claim.** The mechanism now replaces the model's
> `phys_*`-driven rise above base as well as its fitted markup, so its scope is
> larger than §4.2 first stated: the above-base offer curve's **shape** is
> measured end to end, not merely its markup. The DOF consequence in §10 item 4
> is unchanged (the retired *fitted* scalars are still the 24 above-base price
> multipliers; `phys_*` are measured, not free).
>
> **Status.** Found by inspection while wiring the mechanism, **before the
> derive was run and before any solve**; no measurement informed it. The
> corrected algebra is verified by a unit check (base row untouched, above-base
> = base + measured rise, positions 0.167/0.500/0.833 on a synthetic 3-tranche
> plant). Gates, priors, branches and traps in §§5–8 are **unchanged** — P-2's
> prior was never conditioned on the formula's algebra.

**Untouched:** every `committed` base tranche (the level anchor), all coal
(rule 19 — coal has its own gas-keyed supply sigmoid; MISO-53 adjudicated the
deep-discount premise on a different mechanism), every non-MISO ISO (rule 25).

`gas_offer_margin` is **SUBSUMED**: its fuel-invariance form survives — the part
externally validated by the 2022 NEISO rotation that rejected the multiplicative
form — and only its *source* changes from fitted multiplier to measurement. Two
mechanisms never both price the same tranche's margin.

### 4.3 Fields (rule 21 `[R-REGISTRY]`, rule 28(c))

* `miso_offer_surface_measured: bool = False`
* `miso_offer_surface_path: str | None = None` (None → the frozen derived
  artifact under `data/raw/_validation-source/`)
* `miso_offer_surface_netload_pcts: list[float] = [0.80, 0.90, 0.97]`
* `miso_offer_surface_position_bins: list[float] = [0.0,0.2,0.4,0.6,0.8,0.9,1.0]`

All four registered in `_CACHE_KEY_OPTIONAL_FIELDS` with declared defaults **in
the same commit** (verified by `scripts/check_cache_key_registration.py` and
`tests/regression/test_persisted_identity.py`), plus a `mechanism-matrix.js` row
in the same PR.

---

## 5. Two-sided numeric prior, stated before measurement

| # | statement | central | band | P |
|---|---|---|---|---|
| **P-1** | measured Δ at the model's clearing-position band ÷ the model's own above-base margin there | **3.0×** | [1.2×, 12×] | 0.75 |
| **P-2** | arm's C3a-2025 move (needs +7.09 to close) | **+2.5 $/MWh** | [+0.5, +5.5] | 0.80 that the sign is POSITIVE |
| **P-3** | C3b-2025 NRMSE does not rise above 0.212 | — | — | 0.55 |
| **P-4** | May-2025 moves FURTHER OVER (already +12–15 %) | +1.5 $/MWh | [0, +4] | 0.70 |
| **P-5** | C8 ST_GAS 2025 forced share does **not** rise from 48.4 % | — | — | **0.45** |

**P-5 is stated against the mechanism.** Making above-base gas dearer reduces
ST_GAS *economic* dispatch, which mechanically **raises** its forced share on an
unchanged floor. I judge it more likely than not that this gate is pressured,
and I am registering that before I measure it.

**P-2's central value does NOT close the miss and is not claimed to.** 2023
carries nearly the same CC gap and C3a-2023 **PASSES**; nothing here predicts,
claims, or sizes closure of 2025's −15.6 %.

---

## 6. Pre-committed branches

* **BRANCH-SHAPE-CONFIRMED** — P-1 fires (ratio > 1.2×) **and** C3a-2025
  improves by ≥ +0.5 $/MWh **and** no kill gate breaches → the arm is a keeper
  CANDIDATE. **It is not promoted by me.** Rule 22 leave-one-year-out is scored,
  and the keeper call **escalates to the owner** under the standing
  structure-over-gates guidance.
* **BRANCH-SIGN-INVERTED** — C3a-2025 moves **negative** → **K1 fires, STOP.**
  The mechanism is REFUTED as specified; cell `R`; the level-transfer diagnosis
  of §1 is confirmed and recorded as such. No re-scoping, no second arm, no
  re-binning to recover it (rule 23 bars re-binning against a residual anyway).
* **BRANCH-INERT** — |ΔC3a-2025| < 0.5 $/MWh → mechanism provably inert on this
  keeper; cell `I`; reported with the measured Δ that made it inert.
* **BRANCH-GATE-BREACH** — C3a improves but a kill gate fires → reported at
  **FULL MAGNITUDE** and **escalated to the owner**. Not my call, not silent,
  not auto-fatal.

**Whichever branch fires, BOTH runs (control and arm) are registered on the
backcast dashboard in this session** (rule 15), keeper or rejected.

---

## 7. Traps, each with its counter-measurement

| # | trap | counter-measurement |
|---|---|---|
| **T-1** | asserting a cross-check without coding it (the miso-150 lesson) | every claim in the FINDING traces to a coded gate that printed a number; no docstring assertion is quoted as evidence |
| **T-2** | an array/ordering bug in the new `(n_gen, T)` construction, discovered after a 50-min solve (the miso-150 lesson) | **synthetic-fleet shape self-test** on a hand-built 3-gen × 48-h case with a known-answer surface, run and PASSED before any solve is launched |
| **T-3** | an outcome column reaching the derive (rule 13) | G-F2 column census on the written partition, bar 0 |
| **T-4** | **LEVEL leakage** — the whole point of §1 | shift every unit's entire curve by a constant $c and re-derive: Δ must be **bit-identical**. Measured on real data, both markets, bar exactly 0 |
| **T-5** | silently changing the base band while "only" touching above-base | assert `offer_markup_hr` untouched on every `committed` tranche; count tranches modified vs expected, printed |
| **T-6** | the keeper-pointer seam (`_miso143_stack.KEEPER` hard-coded to the superseded `miso132_ccmin_B`) | footing runs at its committed value; any NEW measurement re-points to `miso148_basis_B` **saving and restoring**, and only AFTER the footing |
| **T-7** | `_miso147_strata._cache_dir()` writes npz into the CWD | `MISO147_CACHE` set to the scratchpad; repo root checked clean for `fleet_*.npz` before commit |
| **T-8** | timezone — the corpus is fixed **EST (UTC−5) year-round**, 24 rows/unit-day across both DST transitions | the state-bin join is built on the corpus's own declared EST stamps converted once, with a printed row-count reconciliation per year (expect 24 × units × days) |
| **T-9** | `ecomax` sentinel −1.0 → negative/∞ positions | dropped by the §4.1 population rule; dropped-row count printed per year |
| **T-10** | the surface is evaluated at the model's own **fitted** tranche positions (`econ_low_share`, `pct_peaking` stay fitted) | disclosed in the FINDING as a residual dependence; NOT repaired here (rule 19 — that is a geometry mechanism, a different phenomenon) |
| **T-11** | the full-year refetch silently changing the JJA span | G-F1 |

---

## 8. Kill gates (a breach is reported at FULL MAGNITUDE and escalated — never silent, never auto-fatal)

* **K1 — SIGN.** C3a-2025 moves negative at all → **STOP** (BRANCH-SIGN-INVERTED).
* **K2** — C3b-2025 NRMSE ≤ **0.212** AND MUST NOT RISE (already failing 0.200).
* **K3** — C3b 2023/2024 stay PASS (0.082/0.125); C3a 2023/2024 stay PASS
  (−1.98 %/−8.03 %).
* **K4 — MAY 2025.** Reported explicitly in **$ and %**, whatever the sign.
* **K5 — C8.** No material class's forced share rises; no D-4 break. ST_GAS is
  already grounded at 48.4 % (2025) and CT_PEAKER at 16.8 % (2023).
* **K6 — C3c is 1/1 SPENT.** The tail motivates nothing. Fail-set stays
  **⊆ {C3a, C3b}**.
* **K7** — C1/C2 PASS on gated years; 2025 descriptive vs EIA-930 only.
* **K8** — leave-one-year-out within 2023–2025 before any promotion (rule 22).
* **K9** — the derive is **frozen against residuals** (rule 23): re-derives only
  on a corpus update, and such a commit cites the data change.

---

## 9. Rule-13 `[R-MEASURED]` admissibility, adjudicated in advance

**The forward-analogue test.** `Δ(position, net-load percentile, gas price)` is
estimated from **multi-year** (2023–2025 pooled) submitted-offer history and
conditioned on three drivers that all exist in a forecast year: a unit's
position in its own output range, the hour's net-load percentile, and the
delivered gas price. It **regenerates for a forward year** and **responds to
changed conditions** (a tighter forecast year draws higher state bins; a higher
gas forecast draws the upper gas tercile). It is the CEMS-emission-rate
precedent in form.

**Explicitly excluded and forbidden** (miso-146 PREREG §9, standing, binding on
any successor — this session is that successor): *a measured same-year offer
curve pinned into the backcast is a measured **outcome** overlay with no forward
analogue — forbidden as methodology, and admissible at most as an
explicitly-labelled, default-off diagnostic probe.* This surface is pooled
multi-year and applied identically to every year. **No per-year surface is
derived, armed, or reported as a candidate.**

**Outcome columns never enter.** The corpus's dispatch awards are dropped at
curation, absent from the schema, and G-F2 measures their absence in the written
partition.

**No fitted parameter is added.** The surface is a derived artifact; its two bin
geometries are the registered cross-ISO convention and a declared position grid,
both frozen here before measurement and never re-tuned against a residual.

---

## 10. Full disclosure — everything read or computed before this registration

**Read:** `FINDING-miso150-the-universe-was-never-load-bearing-2026-08-10.md` in
full; `FINDING-miso145-offer-conduct-2026-08-09.md` §§1, 6, 8;
`FINDING-miso149-the-object-is-the-price-level-2026-08-10.md` §§7–9;
`PREREG-miso146-intermittent-screen-2026-08-09.md` §§9–10;
`PREREG-miso150-model-side-universe-2026-08-10.md` §§1–2;
`data/dictionary/schema/energy-offers.schema.yaml` header;
`data/raw/miso-energy-offers/README.md`; `scripts/data/fetch_miso_energy_offers.py`
(header + CLI); `src/market_sim/data/offer_curves.py::apply_gas_offer_margin`;
`src/market_sim/config/scenarios.py` gas-offer-margin field block;
`src/market_sim/config/constants.py::GAS_OFFER_MARGIN_ANCHOR_BY_ISO`;
`src/market_sim/data/fleet/assembly.py` tranche construction ~L1130–1185; the
`measured_offer_surface` matrix row (cells `KKRUGI`, MISO = **U**).

**Computed — reference-side and availability only, no adjudicating statistic:**

1. **§0 re-verification** — `calibration_verdict.py --run-id
   2026-08-09-miso-148-basis-aware`, summarised in §0.
2. **C3a reproduction and its monthly decomposition**, from the committed run
   payload + `bench/MISO/<y>.json.gz`: model lw 32.197/29.704/38.372 vs actual
   lw 32.85/32.30/45.46 → −1.99/−8.04/−15.59 %, reproducing the committed
   −1.98/−8.03/−15.58; demand-weighted JJA share of the deficit −9.6/52.8/61.1 %
   by year. **This is the target's description, not a test of this mechanism.**
   Basis caveat: the monthly leg mixes a zone-load-weighted model side with the
   bench's simple monthly RT mean, so its levels are descriptive and only its
   shares are quoted.
3. **DOF census** from `miso148_basis_B/{run_config,calibration_attestation}.json`:
   30 entries, `n_residual` = 2; `offer_curve_by_group` 92 scalars (gas 67, of
   which 20 measured `phys_*`; coal 25); `offer_curve_smoothing` 2.
4. **CORRECTION TO THIS SESSION'S OWN DECISION PACKAGE.** That document sized
   the shrink at **−47 fitted scalars**, assuming the whole gas block is
   retired. Once §4.2's construction was fixed, the honest number is
   **−24**: the above-base price multipliers (`econ_low`, `econ_high`, `peak`)
   across 8 gas classes. The 8 `committed` base multipliers and the 15 quantity
   splits (`econ_low_share`, `pct_peaking`) survive, and `n_residual` stays
   **2** rather than falling to 1 — `offer_curve_by_group` shrinks 92 → 68 and
   remains residual-identified. The correction is against interest and is
   recorded here rather than in the FINDING.
5. **Environment only:** venv built, versions pinned to the bundle's recorded
   set (highspy 1.15.1, pandas 3.0.5, pyarrow 25.0.0);
   `curate_capacity_deliverability.py` run → **776 MISO rows** as expected; the
   full-year corpus fetch launched. **No offer datum has been read, binned, or
   aggregated.**

**Concurrent-session check at open:** no other MISO backcast session — one open
PR (#3848, ERCOT), no remote MISO branches, `claude/fh-4-miso-leg-*` absent.
Re-checked at close.
