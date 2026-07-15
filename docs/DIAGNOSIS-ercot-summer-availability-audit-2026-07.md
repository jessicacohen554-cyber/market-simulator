# DIAGNOSIS — ERCOT summer availability audit: outage overlay EXONERATED, the phantom-evening defect is the storage capability basis (2026-07-14)

**Task (owner ask, follow-on to
`docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md` §3
items 2–3).** Execute the storage-energy audit chartered in §2a-1 and the
demand-response charter (§2a-2) for the keeper
`2026-07-12-ercot63-gas-bridge`'s tight-week evening over-amplitude (Aug 18–20
2024 VOLL saturation; Jul 30–31 / Aug 18–25 2025 phantom $250–1,944 plateaus).

**Verdict in one line: every hypothesis in the §2a-1 charter was tested and
the causal chain REWRITES — the storage power/energy envelope is feasible
against measured dispatch (power +0.5–1 GW slack at the measured peak, energy
marginal), the CEMS-inferred outage overlay is GROUND-TRUTH FAITHFUL against
the 60-Day disclosure (its big 2025 dark windows — Sommers, Braunig, Cedar
Bayou 2, Sandy Creek, Limestone, Parish 8 — are all telemetered `OUT`; the
model's thermal availability is in fact ~+2 GW RICHER than ERCOT's telemetered
capability in BOTH years) — and the real defect is the model's **storage
capability basis**: the EIA-860-derived battery fleet runs ~2 GW below ERCOT's
registered non-OUT storage capability in both summers (5.8 vs 7.7 GW Aug-2024;
10.6 vs 12.5 GW Jul-2025) and the measured AS award subtraction removes another
~3–3.5 GW from the evening scarcity margin, so the model's total capability at
the phantom hours sits ~3 GW below reality's and the reserve co-opt prices
shortage where the real market had cushion.**

No LP was solved. Every number below is measured data or the keeper's own
fleet reconstruction (`run_year(fleet_only=True)` off the bundle `meta.json` —
the `derive_ordc_overlay.build_availability` recipe).

## 1. What was tested and what each test found

### 1a. Storage dispatch envelope vs measured 2025 dispatch — FEASIBLE (not the defect as charted)

Measured EIA-930 battery discharge vs the model's constraint envelope
(EIA-860 ramped fleet power − measured hourly AS withholding,
`reserve_storage_as_power`):

- Power: measured peak discharge 6.3–6.4 GW on the phantom evenings sits
  *inside* the model's available power (6.9–7.3 GW at those hours). Across all
  8,760 hours of 2025 only 2 hours (May) violate the envelope.
- Energy: measured discharge on the phantom days is 18.1–20.5 GWh/day vs
  Jul/Aug fleet energy caps 15.9/16.4 GWh — reproducible only with a midday
  recharge cycle (which `storage_daily_cycling` permits: it pins SOC across
  day boundaries, not cycles within a day). Marginal, not infeasible.
- The 25 % 2025 throughput under-cycling (4.11 vs 5.46 TWh) stays the
  ERCOT-60 incentive-bound finding
  (`docs/DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md` §7) — nothing here
  reopens the AS-release window (rule 19).

### 1b. Outage overlay — EXONERATED by disclosure ground truth

The unit-event overlay (`campd-unit-outages.csv`) carries 6.3–7.4 GW out in
the 2025 phantom windows vs 1.6–3.1 GW in the same 2023/2024 weeks — the
prima-facie suspect (economic-idle-vs-unavailable confusion in a soft year).
Ground-truthed against the 60-Day DAM disclosure Gen_Resource `Resource
Status` (in-repo, `data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_
Data_2025_Aug-Sep.parquet`, deliveries 2025-06-02→08-01, covering the Jul
30–31 phantom days):

- **Faithful `OUT` at the phantom hours:** Sommers 1–2 (892 MW), Braunig 1–3
  (894 MW; 1–2 are the NSO-confirmed suspensions in the confirmed-retirements
  registry), Cedar Bayou 2 (765 MW), Sandy Creek (1,008 MW, telemetered OUT
  1,440/1,464 hrs), Limestone LEG_G2 (957 MW), Parish WAP_G8 (654 MW, seven
  peers ON — a real forced outage). ≥5.2 GW of the window confirmed genuinely
  unavailable. The 2025 fleet really did lose ~5 GW of old steam to
  suspensions/mothballs/long outages; reality cleared $243 without them.
- Residual ambiguity ~0.5 GW (T H Wharton CC configs telemetered `OFF` =
  startable while the overlay zeroes THW51–56) + ~1.4 GW unresolved name
  mappings (Magic Valley, Barney Davis, Oak Grove) — second-order.
- **System-level closure:** measured available thermal-ex-nuclear (config-
  collapsed non-OUT HSL) at Jul 30 2025 HE20–21 = **55.0–55.2 GW** vs the
  keeper's reconstructed thermal availability 62.5 GW incl. nuclear ⇒
  **57.4 GW ex-nuclear — the model is +2.2–2.4 GW RICHER than ERCOT's own
  telemetry**. Same sign in 2024 (Aug 19: model 66.6 incl-nuc ⇒ 61.7 ex-nuc
  vs measured 59.7–59.9). The 2024→2025 −3.4 GW availability drop the model
  carries is real fleet attrition, not overlay fabrication.

### 1c. The defect: storage capability basis (measured, both years)

The same disclosure gives ERCOT's registered non-OUT storage (PWRSTR) HSL:

| evening (HE20–21) | measured storage HSL | model effective storage power¹ | gap |
|---|---|---|---|
| Jul 30 2025 | **12.5 GW** | ~7.0–7.3 GW | **−5.2 to −5.5 GW** |
| Aug 19 2024 | **7.7 GW** | ~2.8–3.0 GW | **−4.7 GW** |

¹ EIA-860 ramped fleet (10.6 GW Jul-2025 / 5.8 GW Aug-2024) minus the
measured storage up-AS award (~3.5 GW / ~3.0 GW at those hours).

Two measured components:

1. **Fleet power basis ~2 GW low in both years** (EIA-860 energy-storage
   schedule + monthly COD ramp vs the disclosure's registered capability:
   5.8 vs 7.7 GW Aug-2024; 10.6 vs 12.5 GW Jul-2025). COD-month lag and
   schedule coverage (hybrid battery halves) are the candidate mechanisms; the
   disclosure is the market-faithful registry of what ERCOT could actually
   call on.
2. **AS-award subtraction at the scarcity margin (~3–3.5 GW).** The award MW
   is real (batteries did clear it) — but in the real co-optimization that
   capability still stands as *reserve supply*. The model subtracts it from
   the storage power cap (`storage_as_commitment`) and separately credits it
   to the reserve products (`ercot_storage_as_product_credit`); the balance
   arithmetic below says the net effect at the phantom hours still leaves the
   model ~3 GW short of reality's margin — the credit-vs-subtraction wiring
   at the ORDC/total-reserve margin needs a targeted audit.

### 1d. The balance arithmetic (why this closes the phantom-evening question)

Jul 30 2025, HE20–21 (actual RT max $243; model $1,944 at the aligned hour):

|  | thermal (incl. nuc) | storage | total capability² | demand | margin |
|---|---|---|---|---|---|
| measured | 60.1 | 12.5 | ~78.6 | ~74 | **~+4.6 GW** → mild tightness |
| model | 62.5 | ~7.0 | ~75.5 | same | **~+1.5 GW** → reserve shortage → $1,944 |

² + identical measured wind HSL (~6 GW) and solar (~0) on both rows.

Aug 19 2024 HE20 (actual $3,060; model $5,000): measured margin ≈ +3.2 GW
(deep ORDC, no shed — matches $3,060); model margin ≈ +0.3 GW (shed → VOLL).
Same decomposition: storage −4.7 GW, thermal +1.9 GW. **One mechanism, both
years, both signs of event:** the model's evening scarcity margin is
systematically ~3 GW below reality's, entirely attributable to the storage
capability basis, and the summer weeks where the margin crosses zero are
exactly the over-amplitude/phantom windows.

## 2. Dispositions (rules 13/14/15/19)

1. **Outage overlay: no change.** Ground-truth faithful; its 2025 windows are
   real. The §2a-1 hypothesis (economic-idle conflation) is refuted for these
   windows and recorded here so it is not re-opened on the same evidence.
2. **Storage fleet power basis — measured-input correction chartered.**
   Replace/reconcile the backcast battery fleet power with the 60-Day
   disclosure's registered PWRSTR capability (config trivial, unit-resolved,
   same source family and admissibility as the ERCOT-57 thermal
   DAM-availability intake; rule 14: prefer the measured number). EIA-860
   remains the energy (MWh) and zone-assignment basis. Blocked on: extending
   the disclosure intake to the 2025 Oct-Nov/Dec publication files (deliveries
   Aug–Dec 2025, needed for the Aug-2025 window and year-end; 2025 is a
   training year — no quarantine issue) and a `derive_*` script with the
   frozen-against-residuals contract (rule 23).
3. **AS-award credit-vs-subtraction wiring — targeted audit chartered.**
   Verify at the co-opt margin that the withheld award MW enters the reserve
   supply the ORDC/total-reserve construction sees; if the arithmetic in §1d
   still shorts the margin after the fleet-basis fix, this is the remaining
   lever. No parameter change without that trace (rule 19 — one mechanism per
   phenomenon; the award subtraction and product credit must reconcile, not
   stack).
4. **Storage energy (MWh) / duration:** EIA-860 basis stands (envelope
   feasible); re-check only after the power basis lands.
5. **May-2024 / G-22 lanes: untouched** (already filed; nothing here moves
   them).

## 3. Effect on the demand-response question (§2a-2)

The charter investigation narrows sharply: in **backcast** mode the measured
EIA-930 demand already embodies realized price response, and §1d shows
reality's cushion on the phantom evenings was storage capability, not load
relief — so a backcast DR mechanism is NOT the fix for these windows and must
not be built as one (it would stack a second mechanism on the storage-basis
defect, rule 19). The surviving DR scope is the **forecast-mode elasticity
gap** plus the **extreme-tail emergency products** — chartered separately in
`docs/handoffs/ercot-demand-response-charter-2026-07.md`.
