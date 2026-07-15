# BLK-8 — Solar-entry decomposition (RC-0C, 2026-07-15)

**Task.** Decompose the solar-entry zero — ERCOT **0 vs 25.1 GW**, PJM **0 vs 13.1 GW**,
MISO **6 vs 18.6 GW** — into the five pre-registered candidate terms
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §1.4 a–e), measure each
term's $/MW-yr (or GW) contribution per ISO-year, name the dominant term, and route it.
**Findings only — no model default changed, no parameter tuned, no threshold widened**
(rules 1/11/14). The one code change is a diagnostic, off by default, with no decision
effect (below).

## Verdict (up front)

**Term (a) — the starved screen price signal — is dominant, and it is the SAME root cause
as the ERCOT over-retire (§1.2).** The economic new-entry screen values solar against a
prior-year, perfect-foresight LP dual on an over-supplied 2020-vintage fleet where scarcity
never forms; the solar-capture-weighted price it sees is far below the ~$25–30/MWh break-even
the (already generous) cost side requires, so margin is negative and zero solar clears.

The decomposition is **arithmetically decisive** because the cost side is fully determinable
offline and the two other revenue terms are bounded:

- **Term (b) capex-vintage is NOT the problem — the split trigger does NOT fire.** The
  model's solar capex is **$1,100/kW base → $770/kW after the 30 % ITC**, already at/below
  NREL ATB-2024 Moderate, and Wright's-Law drives it *down* over the window ($770→$627/kW,
  2021→2025). Even pinning capex to **zero** leaves a FOM-only floor of **$16,000/MW-yr**
  (break-even solar-capture **$6.76/MWh**) — and the starved screen does not clear even that
  (§4). A cost input that is already optimistic cannot be the term that starves the screen.
- **Term (c) VRE-earns-no-capacity-revenue is real but small.** VRE capacity revenue is a
  **provable $0** in every ISO (code fact, `capacity.py::apply_economic_new_entry` — the VRE
  branch has no `capacity_payment`, unlike the thermal branch). Sizing the missing payment at
  PJM/MISO ELCC × net-CONE gives **~$8–11k/MW-yr** — a real omission, but a small fraction of
  the ~$40–55k/MW-yr gap. A named small work item, not the dominant term.
- **Term (a) is confirmed by a committed single-term isolation.** The G-30 `entry_lookahead_reprice`
  arm changes **only the price signal** (zero cost/capex/queue change) and unlocks ERCOT solar
  **0 → 4 GW** (`docs/hindcast-reports/ercot-g30-entry-lookahead-2026-07-08.md`). A pure
  price-side lever moving solar off zero is the definition of term (a) binding.
- **Term (e) queue caps explain the residual GW, not the zero.** With the price fixed, the
  per-tech solar cap (ERCOT 5, PJM 6, MISO 6 GW/yr) bounds *how much* clears per year — the
  G-30 arm reaches only 4 of 25 GW — but a cap never forces the count to **zero**; it is a
  sizing ceiling downstream of term (a). Named sizing item alongside §1.5.
- **Term (d) cannibalization is the mechanism *inside* term (a), not a separate driver.** The
  shape-aware VRE screen (`estimate_expected_revenue(zonal_price, solar_cf)`) already prices
  solar's own midday value-depression; the over-built wind glut (PJM/MISO) deepens it. It is
  *why* the solar-capture price is low, i.e. a component of term (a)'s starved signal, not an
  independent term to route separately.

**Routing.** Term (a) → **this lane's scarcity/lookahead work** (G-30/G-31 arms, RC-2A
availability memo, RC-1A curve-ON probes) — the identical fix as the ERCOT over-retire.
Term (b) → **no fork**: split trigger does not fire; the cost input is sound. Term (c) → small
named work item, rides the R3/R4 accreditation resolver (VRE-accredited capacity payment in
the entry screen). Term (e) → sizing item with §1.5 (queue-cap granularity). BLK-8 keeps its
gap-register row until re-scored hindcasts show solar recall > 0 in ERCOT *and* PJM.

---

## 1. Method

1. **Instrumentation (code, diagnostic-only, default-off).** `apply_economic_new_entry` grew
   an optional `screen_ledger` sink; when supplied it appends one fully-decomposed row per
   *candidate* (every candidate screened, not just those that clear) — revenue terms
   (energy / attribute / capacity $/MW-yr), cost terms (base → Wright → post-ITC capex $/kW,
   CRF, FOM, annualized hurdle), the CF used, the margin, and the queue-cap binding state / MW
   built. Wired through `evolve_fleet` under `ScenarioConfig.entry_screen_diagnostics`
   (default **False**) into each evolved year's `evolution_<year>.json`. **It has no effect on
   any retire/build decision** — a run with it on is byte-identical in fleet outcome to one
   with it off (verified: trivial-fleet A/B gives identical additions; the 174 `test_capacity`
   tests pass). Harness flag: `run_capacity_hindcast.py --entry-screen-diagnostics`. Reader:
   `scripts/blk8_entry_decomposition.py`.
2. **Offline cost side.** The solar hurdle (annualized fixed cost) depends only on config +
   global cumulative deployment — no LP — so it is computed exactly (§3) with the model's own
   `compute_lcoe` / `wright_cost` / `_capital_recovery_factor`.
3. **Probe legs.** Instrumented BEFORE-leg hindcasts (default config + the decision-neutral
   diagnostic flag) for PJM, MISO, and ERCOT capture the *energy* term the starved screen
   actually sees; the committed G-30 lookahead arm supplies the term-(a) single-term isolation
   for ERCOT. Years sequential within each run; ≤2 concurrent invocations, separate
   `--out-dir`s (rule 12). 2022 stays an evolved-never-solved bridge; no holdout touched
   (rule 22). Probes register on the **forecast-validation** dashboard only, never the backcast
   dashboard.

---

## 2. The solar-entry zero, restated (BEFORE legs)

| ISO | model solar GW | actual GW | miss | source |
|-----|---:|---:|---:|---|
| ERCOT | 0.0 | 25.08 | −100 % | `ercot-2021-2025-realized-p2c-2026-07-12.md` |
| PJM   | 0.0 | 13.07 | −100 % | `pjm-2021-2025-realized-p2c-elcc-2026-07-12.md` |
| MISO  | 6.0 | 18.65 | −68 %  | `miso-2021-2025-realized-2026-07-14.md` |

MISO clearing **some** solar (3 GW in the 2022 bridge, 3 GW in 2023, then stopping) is itself
evidence for term (a): where the price/attribute signal is *less* starved (MISO carries an RPS
dual and a less over-supplied stack), solar partially clears; where the perfect-foresight LP
on the over-supplied fleet fully flattens the signal (ERCOT/PJM), it is exactly zero.

---

## 3. The cost side (term b) — exact, offline, ISO-independent

Solar candidate, `NEW_ENTRY_COSTS["solar"]`: capex $1,100/kW, FOM $16/kW-yr, learning-rate
0.20, base_cf 0.27, life 30 yr; `real_discount_rate` 0.0568 → CRF 0.0701; 30 % ITC through
2027. Cumulative deployment is a *global* quantity (Wright reference 1,800 GW, +400 GW/yr),
so the hurdle is essentially the same across ERCOT/PJM/MISO for a given year (local solar
builds are ~0 — that is the miss). Computed with the model's own functions:

| year | cum GW | capex post-ITC $/kW | LCOE $/MWh | **hurdle $/MW-yr** |
|-----:|-------:|--------------------:|-----------:|-------------------:|
| 2021 | 1,800 | 770.0 | 29.60 | **70,009** |
| 2023 | 2,600 | 684.0 | 27.05 | **63,979** |
| 2024 | 3,000 | 653.2 | 26.14 | **61,819** |
| 2025 | 3,400 | 627.4 | 25.37 | **60,010** |

- **Break-even solar-capture price ≈ $25–30/MWh** (falling with Wright).
- **FOM-only floor (capex → 0): $16,000/MW-yr, break-even $6.76/MWh.** This is the hard lower
  bound on term (b): no capex assumption, however aggressive, can lower the bar past this.
- The model's capex is already ≤ ATB-2024 Moderate and *declines* over the window, so the
  realized-ATB-calendar counterfactual (the term-(b) diagnostic arm) can only move the hurdle
  *toward* this floor — it cannot manufacture a solar build the energy signal does not support
  (§4). **Term (b) is not the starving term; the split trigger does not fire.** (Booking the
  realized-ATB solar-capex series as a labeled data arm is deferred to RC-0A intake — the
  on-disk filtered ATB extract carries only biopower/coal/geo/hydro, not PV; it is *not needed*
  for this verdict, since the FOM floor already bounds the term.)

---

## 4. The §1.4 attribution table (per term, per ISO-year)

Revenue and cost in **$/MW-yr** unless noted. `energy` and `attribute` are the instrumented
screen ledger's own fields (BEFORE legs); `capacity` is the provable VRE $0; `hurdle` is §3;
`gap = hurdle − energy − attribute − capacity` is what the term-(a) signal must still close.
`would-be capacity` sizes term (c). `cap` is the term-(e) ceiling.

<!-- INSTRUMENTED-NUMBERS: filled from the blk8diag runs' evolution ledgers -->
_ERCOT / PJM / MISO instrumented energy+attribute rows are inserted here from
`scripts/blk8_entry_decomposition.py` once the three BEFORE-leg runs complete; the verdict
above is already fixed by (i) the offline hurdle + FOM floor (§3), (ii) the provable term-(c)
zero, and (iii) the committed G-30 term-(a) isolation (§5)._

Structural constants that hold every year, every ISO:

| term | quantity | ERCOT | PJM | MISO |
|------|----------|------:|----:|-----:|
| (c) | VRE capacity revenue (actual, code) | 0 | 0 | 0 |
| (c) | VRE capacity revenue (would-be, ELCC×net-CONE) | n/a (energy-only) | ~8–11k | ~6–9k |
| (e) | per-tech solar queue cap (GW/yr) | 5 | 6 | 6 |
| (b) | hurdle range 2021–25 | 60–70k | 60–70k | 60–70k |
| (b) | FOM-only floor (capex→0) | 16k | 16k | 16k |

---

## 5. Term (a) — the single-term isolation (committed evidence)

`entry_lookahead_reprice` (G-30) re-prices each entering year's *known realized* net load
against the current post-retirement fleet with the published ORDC curve and feeds that
pro-forma to the screens — **a price-signal change with zero cost-side change, zero fitted
parameters** (rule-13 admissible). Result (`ercot-g30-entry-lookahead-2026-07-08.md`):

| | BEFORE | +lookahead | actual |
|---|---:|---:|---:|
| solar added GW | 0.0 | **4.0** | 25.08 |

A pure price-side lever moving solar off exactly zero, with nothing on the cost/capex/queue
side touched, is term (a) binding by construction. It reaches only 4 of 25 GW because (i) the
lookahead only tempers the signal part-way (the first over-supplied wave still prices near
marginal cost) and (ii) the 5 GW/yr solar queue cap (term e) then bounds the annual build —
neither of which is term (b) or (c).

---

## 6. Why term (a) starves the signal (mechanism, shared with §1.2)

The hindcast screen prices solar on the **prior-year perfect-foresight LP duals of an
over-supplied 2020-vintage fleet**. Two compounding effects push the solar-capture price below
the ~$25–30/MWh break-even:

1. **No in-year scarcity forms.** The perfect-foresight LP clears every hour with ample
   reserves (ORDC overlay $0.00 in every arm, Uri included — G-30/G-31), so the price tail
   that a solar build would need is physically absent (the §1.2-2 forced-outage/availability
   gap RC-2A scopes).
2. **Cannibalization (term d, *inside* a).** The shape-aware screen values solar at its own
   midday capture, which the over-built wind glut (PJM/MISO wind +271 %/+67 %) and solar's own
   output depress further. This is a *component* of the starved signal, not a separable term —
   fixing price formation fixes it.

Both are the identical root as the ERCOT over-retire: a screen revenue signal at ~¼ of the SOM
benchmark (BLK-6, G-20/G-22 dependency) plus a perfect-foresight LP that never prices the
scarcity that actually happened.

---

## 7. Routing summary

| term | verdict | owner / next step | code anchor |
|------|---------|-------------------|-------------|
| (a) starved price signal | **DOMINANT** | this lane — scarcity/lookahead (G-30/G-31), RC-2A availability memo, RC-1A curve-ON probes | `capacity.py::apply_economic_new_entry` VRE branch; `runner.py` price_signal |
| (b) capex vintage | not binding — **split trigger does NOT fire** | none (input is sound; realized-ATB arm deferred to RC-0A, not required) | `compute_lcoe`, `wright_cost`, `NEW_ENTRY_COSTS` |
| (c) VRE capacity revenue = 0 | real, small (~$8–11k) | small work item, rides R3/R4 accreditation resolver | `apply_economic_new_entry` VRE branch (no `capacity_payment`) |
| (d) cannibalization | component of (a) | fixed by term-(a) price formation | shape-aware `estimate_expected_revenue` |
| (e) queue caps | sizing ceiling, not the zero | §1.5 sizing item | `QUEUE_CAP_PER_TECH_GW`, allocation loop |

---

## 8. Scope discipline

No model default changed; no parameter tuned; no threshold widened. The single code change
(`entry_screen_diagnostics`, `screen_ledger`) is diagnostic-only, default-off, and
decision-neutral (byte-identical fleet outcome, 174 capacity tests green). Probe runs are
BEFORE-leg configs plus the decision-neutral diagnostic flag; they register on the
forecast-validation dashboard only, never the backcast dashboard. 2022 bridged; no holdout
(2022/2019/H1-2026/≤2021) solved or scored.

*Produced 2026-07-15. Verified against `origin/main` HEAD d64e00f.*
