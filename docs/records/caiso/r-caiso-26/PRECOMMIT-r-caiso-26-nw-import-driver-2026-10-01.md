# PRECOMMIT — R-CAISO-26: an NW-stress import driver. SCOPING ONLY. Zero LP. Nothing built.

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25), unchanged. No shard, no cell moved.
Probe: `scripts/probes/_rcaiso26_nw_intertie.py` (EIA-930 per-neighbour interchange, committed; CAISO OASIS
`TRNS_USAGE` intertie OTC, fetched live, nothing committed).

## 0. Stated up front (binding before any number)

- **2024-specific.** The 2022 / 2023 gas events carry an event-specific import delta of **−1.2 / −0.75 GW**
  (R-CAISO-22 §2): the model already imports *less* than its offset there. A lever that cuts firm imports
  under NW stress moves those years the wrong way.
- **C3c payoff ≤ 1 hour.** Removing the whole +2.3 GW event-specific excess gives ~1 hour above $200
  (R-CAISO-22 §3). C3c 2024 needs ≥ 18.
- **caiso-150 §H DO-NOT-REDO binds**: no re-measure of the self-schedule ceiling, no import/export split of
  intertie self-schedules, no re-derive of the PNW firm level.
- **Rule 13 test**: the input must be a physical availability quantity (an intertie OTC / outage record),
  never a shadow price, a flow outcome or a neighbour's LMP.

## 1. The question's premise is falsified: imports did not collapse, exports surged

CISO evening interchange (h17–22, EIA-930, MW, + = import into CAISO). Event = Jan 13–16 2024;
baseline = Jan 8–9 and 20–21.

| | Baseline | Event | Δ |
|---|--:|--:|--:|
| **Net** | 2,695 | 443 | **−2,252** |
| Gross import | 4,174 | 3,770 | −404 (18 %) |
| Gross export | 1,480 | 3,327 | **+1,847 (82 %)** |
| BPAT leg | −395 | −1,565 | −1,170 |
| BANC leg (COTP) | −325 | −879 | −554 |
| DSW legs (AZPS, NEVP, SRP, WALC, IID) | 4,120 | 3,741 | −379 |

**82 % of the net-import collapse is CAISO exporting north into the short NW.** Firm-import delivery
fell by ~0.4 GW, and as much on the DSW side as anywhere. R-CAISO-22 §2's "measured net import 0.6–0.8 GW"
is correct as a net, but it is not an import-delivery fact.

## 2. The measured intertie record: real, admissible, and points the other way

CAISO OASIS `TRNS_USAGE` (DAM) publishes, per intertie and direction, the **hourly OTC** (the operating limit
net of forced/planned outage derates), the seasonal TTC, TRM components and scheduled net energy. NW ties
(MALIN500_ISL + NOB_ITC + COTPISO_ITC), evening OPR_HR 18–23, MW:

| Day | Import OTC | Import seasonal TTC | Export OTC | NOB export OTC | DAM sched. net import |
|---|--:|--:|--:|--:|--:|
| Jan 8 | 4,771 | 4,771 | 3,321 | 510 | −649 |
| Jan 9–11 | 3,946 | 4,771 | 2,824 | 510 | +948 → −1,427 |
| **Jan 12–15** | **4,771** | 4,771 | **2,811** | **0** | **−1,727 → −1,907** |
| Jan 16 | 4,739 | 4,771 | 2,581 | 0 | −1,776 |
| Jan 17–18 | 3,968–4,000 | 4,771 | 2,581–2,811 | 0 | −1,722 → −1,333 |

- Over the MLK weekend **N→S import capability was at its full seasonal TTC**. The derates the DMM names
  (forced NOB outage, Oregon outages) cut the **S→N export** side: NOB export OTC 510 → 0.
- So the physical record cannot reduce firm-import delivery. Applied as a rule-13 availability input on the
  model's PNW link, it is **inert on imports** (OTC 4.8 GW vs the model's 2.4 GW firm floor) and **inert on
  exports** (the model's export sinks dispatch 0 MW, caiso-121/167).
- Coverage: `TRNS_USAGE` returns data from **mid-2023** onward (present 2023-07-01, empty 2023-06-01 and
  every 2022 / Jan-2023 day tried; start not bisected). It is a rolling OASIS retention, so 2022 is not
  recoverable from OASIS, and the earliest months will roll off. **Interties only**: no Path 15 / Path 26
  rows, so it does not serve link 9.

## 3. What the real mechanism is, and why it is not admissible here

The event is the NW pulling energy out of CAISO (Malin $230–255 above the CA stack, R-CAISO-22 §3). The
structural object is an **export sink priced by NW scarcity**. That is the corridor/export family:
`caiso_p1_export_sink_seam` R, `caiso_corridor_export_path` R, `caiso_node_export_constraint` G
(caiso-142/143), closed again on the import half at caiso-167.

| Candidate state variable | Verdict |
|---|---|
| Measured intertie OTC / outage derate (`TRNS_USAGE`) | **Admissible input, wrong direction.** Import OTC unconstrained in the event (§2). Inert on the keeper. |
| Firm-floor cut keyed to NW stress | **Not a real mechanism** (rule 1). Gross import fell 0.4 GW; cutting the floor to reach the net would imitate an export with an import haircut. Also 2024-only in sign (§0). |
| Export sink valued at measured Malin / Mid-C | A neighbour's LMP is a market outcome (rule 13). Its forward analogue needs an NWPP price, which this lane does not have. Re-enters an R/G family; the only new evidence is one winter event worth ≤ 1 C3c hour. |
| NW load–resource balance (EIA-930 BPAT / NW BAs) | Measured, but realised NW interchange is an outcome. Regenerates forward only from a joint NWPP solve, not a CAISO input. |

**No admissible, structural, measured lever.** No cell tested, so no cell moves. C3c 2024 stays a lone
ledgered, non-downgrading caveat (rule 22 `[R-C3C]`).

## 4. Side observation (not a lever)

`TRNS_USAGE` is a measured hourly intertie OTC, the physical quantity behind the model's corridor caps (today
the p95 envelope of measured flows, caiso-162/280). Rule 14 would prefer it as the cap basis where it covers
the years. Caveats: it is mid-2023+ only, and caiso-280 found the envelope binds **above** actuals, so no fit
gain is expected. Evidence for a possible intake, not a proposal.

## 5. Decision

Owner decision card (§6). Recommendation: close link 8 with no build, and go to link 9.

## 6. Owner ruling

Decision card, 2026-10-01. Two of three options were selected:

1. **Close link 8, go to link 9.** No build. C3c 2024 stays a lone ledgered, non-downgrading caveat.
   R-CAISO-27 (Path-15 derate-data scoping) is next, then links 10 and 11.
2. **Queue an intertie-OTC intake** as a new link (link 12, R-CAISO-30), after link 11. Data-only: OASIS
   `TRNS_USAGE` hourly intertie OTC / TTC by direction, mid-2023 onward, through the data-intake contract.
   Evidence for a rule-14 corridor-cap basis; no fit gain expected (caiso-280). Note the rolling OASIS
   retention: the earliest months roll off while it waits.

Not selected: re-opening the export-sink family.

## Sources

- EIA-930 BA-to-BA interchange, CISO: `data/raw/eia-930-interchange/CISO interchange hourly.parquet`.
- CAISO OASIS `TRNS_USAGE`: `https://oasis.caiso.com/oasisapi/SingleZip?queryname=TRNS_USAGE&market_run_id=DAM&startdatetime=20240108T08:00-0000&enddatetime=20240119T08:00-0000&version=1&resultformat=6`
- CAISO DMM, Winter Market Performance Report Jan 2024 (via R-CAISO-25).

## Retrievability (rule 34(e))

Nothing was solved. The probe re-reads the committed EIA-930 file and refetches OASIS live.
