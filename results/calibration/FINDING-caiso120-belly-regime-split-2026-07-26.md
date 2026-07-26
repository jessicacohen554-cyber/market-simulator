# FINDING — caiso-120 FRESH-EYES REGIME SPLIT: the belly defect is CONCENTRATED in the actual market's SURPLUS regime (RT ≤ $20, ~half of belly hours), where reality is a hub-priced NET EXPORTER and the keeper is a 2.6–3.5 GW importer priced $7–14 ABOVE the hub; in the firm regime (RT > $20) the keeper's price is nearly right (+$1.5–3.8) but it still over-imports ~2 GW — the SILENT half of C5a; measurement-only, keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED (2026-07-26)

**Measurement-only, NO SOLVE, nothing registered, no mechanism armed.** All
inputs are committed bytes: the netrev keeper's own hourly sidecars
(`results/calibration/caiso_netrev_margin/hourly/`) + measured RT LMP + measured
WECC hub LMP + raw EIA-930 CISO interchange. Instrument (committed):
`scripts/probes/_caiso120_price_regime.py`. Fresh re-score of the keeper bundle
at current HEAD confirms the fail set **{C3c, C4 (2023 ONLY), C5a}** — note C4
now fails a single year (2023 gas r 0.838 / NRMSE 0.329; 2024–25 PASS), which is
exactly the CEMS-vs-930 benchmark-basis artifact caiso-115 (fresh-look)
escalated and nobody has acted on.

---

## Inv 1 — the compression, at the distribution grain (Table 1)

Belly = hod 10–15 (lane convention), model = demand-weighted CA-zone λ from the
keeper sidecars, actual = measured RT hourly:

| year | series | mean | ≤$0 | ≤$10 | ≤$20 | >$35 |
|---|---|---|---|---|---|---|
| 2023 | model  | $40.0 |  6.8% | 19.5% | 27.0% | **65.4%** |
| 2023 | act RT | $32.8 | 13.5% | 22.2% | 37.0% | 38.9% |
| 2024 | model  | $23.0 | 18.7% | 30.1% | 33.6% | **35.5%** |
| 2024 | act RT | $15.8 | 27.4% | 36.9% | 51.0% | 20.5% |
| 2025 | model  | $21.8 | 17.8% | 32.1% | 38.7% | **36.7%** |
| 2025 | act RT | $17.5 | 21.0% | 31.9% | 49.2% | 20.7% |

The model **does** now form a negative/zero belly tail (2024: 18.7% of belly
hours ≤$0 vs actual 27.4%; all-hours ≤$0 525 h vs actual 868 — the 2026-06-19
import-ladder diagnosis era was 14 vs 868). The compression's mass error is in
the **upper half**: the model prices >$35 in 35–65% of belly hours where reality
does in 20–39%. Evening mirror: model >$100 in 9.9/1.2/0.0% of evening hours vs
actual 14.7/2.4/0.3%, and 0 hours >$200 anywhere (C3c: actual 47/35/0).

## Inv 2 — the NEW fact: split belly hours by the ACTUAL market's regime (Table 2)

Regime = measured RT ≤ $20 ("surplus": the curtailment/oversupply-priced half)
vs > $20 ("firm"). `act GW` / `mdl GW` = measured EIA-930 CISO net import vs the
keeper's import class; `actexp%` = share of the regime's hours where reality
NET-EXPORTS; `m-hub` = model λ minus the raw measured min-hub (min of MALIN,
PALOVRDE):

| yr | regime | n | act RT | model | m−a | min-hub | m−hub | act GW | mdl GW | act exp% |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | surplus ≤20 |  810 |   2.8 | 14.3 | **+11.5** |  5.3 |  +4.4 | **−0.44** | 2.14 | **56.8%** |
| 2023 | firm >20    | 1368 |  50.5 | 54.3 | +3.8 | 34.4 | +10.1 | 0.93 | 3.63 | 33.3% |
| 2024 | surplus ≤20 | 1116 |  −5.2 |  7.0 | **+12.2** | −6.7 | +13.6 | **−0.12** | 3.35 | **50.9%** |
| 2024 | firm >20    | 1074 |  37.7 | 39.7 | +2.0 | 28.0 | +11.7 | 2.30 | 4.51 | 12.6% |
| 2025 | surplus ≤20 | 1077 |  −0.1 |  7.2 | **+7.3** | −0.8 |  +8.0 | 0.52 | 3.13 | **40.3%** |
| 2025 | firm >20    | 1113 |  34.5 | 36.0 | +1.5 | 25.7 | +10.3 | 2.41 | 4.35 | 18.1% |

Reading:

1. **In the surplus regime the actual CAISO price IS the raw min-hub price**
   (act − min-hub = −2.5/+1.5/+0.7 $/MWh): CAISO is long, net-exports in 40–57%
   of these hours (mean net interchange ≈ 0 to −0.4 GW), and its internal price
   rides the West hub, negative included. The keeper, in exactly these hours,
   **imports 2.1–3.4 GW (a 2.6–3.5 GW signed interchange error)** and clears
   **$4–14 above the min-hub** — it never net-exports a single hour in any year
   (the caiso-112 P1 export-clamp fix `caiso_wecc_export_floor` is in the tree
   but default-off after the caiso-113 L1a′ rejection, and the netrev keeper
   recipe predates it — the flag is ABSENT from its run_config).
2. **In the firm regime the price is nearly right** (+$1.5–3.8, and only
   +$1.5–2.0 in 2024/25) **but the volume is still wrong**: model 3.6–4.5 GW vs
   actual 0.9–2.4 GW import. This ~2 GW rides in at approximately the correct
   price, displacing the gas reality runs — the *silent* half of the C5a
   substitution, invisible to every price gate.
3. Essentially the ENTIRE belly price error lives in the surplus regime
   (+$7–12 there vs +$1.5–3.8 in firm hours). The caiso-117 "belly over-priced
   $12–15" headline is the surplus-regime error diluted across all belly hours.

## Inv 3 — what this reframes about the two blocked belly mechanisms

- **Why the standalone belly cap broke C3a (caiso-117):** capping total belly
  import fixes the *volume* but the model still cannot *price* the surplus
  regime — with imports capped, the next domestic unit (full-MC gas ~$28) sets
  λ in surplus hours where reality prints hub-negative. The cap is volume-right
  and price-wrong **because the surplus-regime price behaviour (export at the
  hub / curtailment-marginal) is missing**, not because volume and price are
  inherently opposed.
- **Why L1a′ broke C3a (caiso-113):** it restored the export *sign* but priced
  exports at the fixed measured hub in ALL hours — over-pricing the belly from
  the export side. The regime split says the export conduct is a
  *surplus-regime* behaviour; an export path priced at the (low/negative)
  surplus-hour hub prints the RIGHT price there by construction (act ≈ min-hub).
- **The firm-regime ~2 GW over-import is a different lever** — it has no price
  signature, so no price-side mechanism can see it. It is the committed-gas
  displacement caiso-118b pointed at (honest size per caiso-119: ~0.5–1.3 GW
  diurnal redistribution, plus the CT_PEAKER 4 TWh evening hole).

**Gate implication for the joint belly delta (the caiso-117 redirect):** score
it on the REGIME-CONDITIONAL quantities, not the belly aggregate — (i) surplus
regime: signed interchange goes long (net-export hours appear, toward the
measured 40–57%), λ − min-hub → ~0; (ii) firm regime: import → measured
0.9–2.4 GW with gas filling; (iii) C3a then holds by construction because each
regime is individually right instead of two errors cancelling. A belly delta
gated on aggregate import volume alone will keep reproducing the
caiso-113/117 C3a breaks.

## Inv 4 — attribution limit (honest)

WHICH unit sets the model's surplus-regime λ (min-hub + $8–14) is not
resolvable from the committed sidecars: candidates are the carbon-paying
import rung (border adder ≈ $13–16 ≈ the observed wedge), domestic gas at a
floor, or the storage-charge opportunity cost. That is a unit-level question —
a keeper replay for the dispatch parquet is justified for it (the
rule-15 keeper-replay clause) and should be the FIRST step of the joint-delta
session, since the mechanism choice (export path vs clean-tranche depth vs
committed-state) hangs on it.

## Housekeeping executed with this finding (same session)

1. `docs/calibration-log/caiso.md` repaired: the caiso-112/113 entries
   (merged to main by PR #2792 on 2026-07-22, then lost to a full-file
   overwrite — the "phantom merge" the caiso-114/116 handoffs flagged) are
   restored verbatim from the PR head blob; the caiso-114/115(fresh-look)/116
   entries merged from their handoff docs; compact caiso-117/118 entries added
   from their FINDINGs/handoff. The log now runs 103→120 unbroken.
2. `results/calibration/caiso_netrev_margin/metrics.json` refreshed
   (`calibration_verdict.py --write-metrics`): the committed snapshot predated
   the bundle's attestation/diagnostics files and said C6 UNATTESTED / C7 C8
   SKIPPED; the live status shard (`frontend/data/backcast/status/CAISO.js`)
   was already correct (C6/C7/C8 PASS), so this only brings the bundle-local
   snapshot in line with the scorer — determination NOT-YET {C3c, C4, C5a}
   unchanged.

## Open items this finding does NOT touch (carried)

- **C4-2023 CEMS-basis escalation** (caiso-115 fresh-look): scorer-only,
  owner-decision; would clear C4 entirely (2024/25 already PASS on CEMS; 2023
  is 0.271 PASS on the same basis vs 0.333 FAIL on the corrupted-cell 930).
- **`caiso_ra_min_load_frac`**: keeper recipe still carries the condemned
  fitted 0.26; the measured 0.570 (caiso-119, near-inert, no KILL) is "KEPT"
  by disposition but lives only in the rejected probe — the next keeper
  candidate must carry 0.570 (rule 14/18).
- **CT_PEAKER priced out** (caiso-119 R4): the C3c lane's live lever —
  obligation-keyed RA must-offer commitment for peakers, D-4 window required.

Reproduction: `python3 scripts/probes/_caiso120_price_regime.py`.
