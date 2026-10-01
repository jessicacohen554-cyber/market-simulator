# CHARTER — ERCOT price-responsive demand & emergency products (2026-07-14)

**Status: chartered, not built.** Scoped by the 2026-07-14 summer-availability
audit (`docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md` §3), which
REMOVED the original motivation ("phantom 2025 evening plateaus") from this
charter's scope — those are the storage capability basis, its own lane. What
survives here is real market structure the model lacks, with the honest
statement of where it can and cannot move a score.

## 1. Why backcast DR is out of scope (read this before building anything)

The backcast demand input (EIA-930 `ERCO hourly` Demand) is *metered* load —
it already contains every MW of 4CP avoidance, large-flexible-load (LFL)
curtailment, ERS deployment and conservation that actually happened at the
actual prices. A backcast DR mechanism would double-count realized response,
and the audit's balance arithmetic shows the 2024–2025 evening residuals are
supply-side (storage capability), not demand-side. **No backcast DR mechanism
may be justified by the summer-evening residual** (rules 13/19). The single
backcast-legitimate sliver is §3 (emergency products above the realized price).

## 2. Leg A (forecast-critical): price-elastic demand for forward years

**Gap.** Forecast-mode demand is a fixed hourly series; the LP must clear the
last MW at VOLL. Real ERCOT peak demand is increasingly price-elastic: 4CP
transmission-charge avoidance, LFL (data-center/crypto) economic curtailment
(~2–6 GW registered and growing, Far West-concentrated), industrial DR. A
forward year solved with inelastic demand will manufacture exactly the
VOLL-saturation signature the audit documents in backcast — overstating
forecast scarcity rent, summer prices, and battery/peaker entry signals. This
is first-order for the model's purpose (forecasting 2026–2050).

**Mechanism shape.** Demand-side offer steps in the LP (negative-load
variables with price floors), NOT a post-hoc haircut: `D_flex(z,t)` MW
curtailable at bid `p_curtail`, entering the energy balance like any other
resource. Rising offer ladder: LFL curtailment (breakeven-priced), 4CP
avoidance (priced at the avoided 4CP $/kW-mo over the coincident-peak-risk
hours), ERS (deployment-priced near the cap), each with its own window/driver.

**Identification (measured, forward-regenerating — rule 13 test):**
- LFL MW: ERCOT's published Large Flexible Load interconnection/registration
  totals (the LFL Task Force series), curtailment breakeven from the same
  public economics ERCOT/IMM cite. Enrollment-trajectory forward analogue,
  exactly like the built `ercot_lr_rrs_enrolled_mw` seam (G4 precedent:
  `docs/ercot-load-resource-rrs-forward-2026-06.md`).
- 4CP: tariff mechanics; MW from ERCOT's published 4CP load-response studies;
  window = the 4CP-risk hours (Jun–Sep, afternoon coincident-peak candidates)
  — a declared driver window per rule 17.
- ERS: procured MW by season (published), deployment price by protocol.
- The adequacy construction already nets 5.8 % of gross peak for these
  programs (`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`, ERCOT CDR-cited) —
  the dispatch mechanism must RECONCILE with that netting (one phenomenon,
  one mechanism: the CDR fraction is the adequacy-side shadow of the same
  programs), not stack on it.

**Scoring/adjudication.** A forecast-mode mechanism cannot be scored against
backcast years by construction. The honest harness is the rule-22 **crossover
window** (2024–H1-2026 scored in both modes against the same actuals):
forecast-mode solves with Leg A on/off, judged on whether the forecast side's
summer tail stops overshooting the backcast side's. Leave-one-year-out within
2023–2025 applies to any parameter shared with backcast paths. No tuning to
locked-test years (2019, H1-2026 backcast) — quarantine unchanged.

## 3. Leg B (backcast-legitimate sliver): emergency products above the realized price

**Gap.** On REAL scarcity evenings the model saturates at VOLL where reality
topped out ~$3,000 (Aug 19 2024: measured margin +3.2 GW → $3,060; model
+0.3 GW → $5,000). Most of that gap closes with the storage capability fix
(audit §2). IF a residual VOLL-saturation remains after it, the admissible
cushion is the emergency ladder that in reality stands between deep ORDC and
firm load shed: ERS (procured MW, deployed at EEA under protocol), TDSP load
management, voltage reduction — all published, procured quantities with
protocol deployment order (rule 13: measured market-design inputs with
forward analogues; the same rows the CDR nets at 5.8 %).

**Order of operations (hard gate):** do NOT build Leg B until the storage
capability basis has landed and the Aug-2024/Jul-Aug-2025 windows re-scored —
the audit predicts the VOLL saturation largely disappears. Building the
emergency ladder first would bury the storage-basis error under a new
mechanism (rule 11/19 violation).

> **Re-score (2026-07-15, ERCOT-66):** the storage basis landed and the
> windows re-scored — the audit's prediction verified: Aug-2024 VOLL
> saturation ELIMINATED (model max 2,859, no shed, vs actual 3,060) and the
> Jul-2025 phantom collapses (1,944 → 251 vs actual 243). What remains in
> Aug-2025 is 14 marginal $210-307 hours (actual max 175) sitting in the
> EXPOSED 2024/25 scarcity-formation lane (see the ERCOT-66 calibration-log
> entry), not an emergency-product window. Leg B stays parked until that
> exposure lane resolves; nothing here suggests a DR mechanism owns the
> residual.

## 4. Explicitly out of scope

- Any backcast evening/peak "DR adder" or demand haircut (double-counts
  metered response; residual-fitting by construction).
- Voluntary conservation appeals (no formulaic MW — rule 26 precedent).
- Re-opening the storage AS-release window (ERCOT-60 adjudication stands).

## 5. Sequencing

1. Storage capability basis fix + AS credit wiring audit (the availability
   audit's §2 items 2–3) — owns the 2024/2025 summer windows.
2. Re-score; only then decide whether Leg B has a residual to own.
3. Leg A proceeds independently on the forecast side (crossover-window
   harness); it does not touch backcast bytes, so it can be built in parallel
   without keeper churn.
