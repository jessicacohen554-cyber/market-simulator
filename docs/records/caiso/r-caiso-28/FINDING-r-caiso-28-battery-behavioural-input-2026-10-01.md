# FINDING (scoping) — R-CAISO-28: per-class behavioural battery input for CAISO. One exists; it cannot re-open R-CAISO-24 §5.

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`), unchanged. **Zero LP, no build, no shard,
no `ScenarioConfig` field, no cell moved.** Probe: `scripts/probes/_rcaiso28_eoh_soc.py` (12 OASIS RTM pulls,
~3 min). Output (gitignored scratch): `results/calibration/_rcaiso28/eoh_soc.json`.

**The bar, stated first.** R-CAISO-24 §0 bounds the price reach of *any* battery representation change at RT
h18: placing the model's h18 battery output **exactly** on the measured fleet lifts SP15 price by **≤ +$0.5/MWh
(2023)** and by **−$0.2 / −$1.5 (2024 / 2025)** — the wrong sign. The bound is on the *outcome* (placement), so a
better input can at most reach it. New evidence re-opens §5 only if it shows either that the bound is wrong or
that a mechanism the bound does not cover (not h18 placement) moves price.

## 0. Result

| Candidate | Grain | 2023–25 coverage | Retention | Rule-13 test | Re-opens §5? |
|---|---|---|---|---|---|
| **OASIS `PUB_RTM_GRP` `MIN/MAXEOHSTATEOFCHARGE`** | **per masked resource, hourly** | 0.2–4.7 % of storage MW (2023), 3–16 % (2024), 16–23 % (2025) | Live from 2023-02 (caiso-281); rolling archive | **Fails as an input**: optional participant-declared bound (DMM 2024 §2.2) encoding its own price view; no forward driver. Report-only. | **No** |
| OASIS `PUB_DAM_GRP` | per masked resource, hourly bid curve | full | gitignored, re-fetch ~2 h | Admissible as an offer input; caiso-178 found no battery offer parameter | No (spent, caiso-176/178) |
| CAISO Daily Energy Storage Report (held) | system, LESR/HYBD; SOC stand-alone only | 2023–25 | quarterly xlsx | `bid_stack` $15 buckets; SOC is an outcome | No (spent, caiso-176) |
| CAISO Today's Outlook (held) | fleet total, 5-min | 2021–25 | daily history | Outcome; comparator only | No (it *is* the bound's comparator) |
| DMM Battery Special Reports 2023/2024 | fleet charts; co-located vs stand-alone; no duration split | annual | PDF figures only, no data | Fig 2.26 SOC-outage (% of charging range lost, quarterly) is a **physical availability** quantity — admissible in form, aggregate, digitize-only | No (aggregate; bound covers it) |
| EIA-860 3_4 (held) | per unit MW / MWh / coupling | full | annual | Physical; admissible | No (structure, not behaviour — R-CAISO-24 §3) |
| FERC EQR | contract rows | — | quarterly bulk | CAISO battery energy settles RTO-priced; no SOC or bid | No |
| CPUC RA (NQC list, slice-of-day) | per resource NQC MW; tariff windows | 2023–25 | annual list | Structural obligation, admissible; carries no behaviour | No |

## 1. The one new input: RT end-of-hour SOC bounds

The EOH SOC bid parameter (ESDER 4, FERC-approved May 2021) is an **optional, real-time-only** hourly
[min, max] MWh range a scheduling coordinator submits for an NGR (DMM 2024 Special Report §2.2). It is published,
masked, in `PUB_RTM_GRP` and is empty in every DAM row (confirmed on 2024-07-10).

| Date | Storage resources (EN curve spans −/+) | Storage injection MW | Submitting EOH SOC | MW share | Implied duration p10 / p50 / p90 (h) |
|---|--:|--:|--:|--:|---|
| 2023-02-15 | 68 | 5,732 | 1 | 0.2 % | 1.1 / 1.1 / 1.1 |
| 2023-08-15 | 86 | 7,426 | 3 | 4.6 % | 1.0 / 3.1 / 3.8 |
| 2024-05-15 | 134 | 10,247 | 26 | 13.7 % | 2.1 / 4.0 / 4.2 |
| 2024-08-15 | 144 | 11,472 | 27 | 15.5 % | 2.1 / 4.0 / 4.3 |
| 2025-08-15 | 195 | 16,780 | 52 | 20.5 % | 2.0 / 3.8 / 4.3 |
| 2025-11-15 | 206 | 16,984 | 58 | 22.6 % | 1.8 / 4.0 / 4.1 |

(All 12 sample days in the JSON. Implied duration = max(MAX bound) / max injection MW; it lands at 4 h, so the
bound is in MWh and its ceiling is the resource's energy capacity.)

**What it shows.** The fleet-summed MIN bound rises through the morning, peaks at h13–16 PST (2024-08-15: 1.4–3.0
GWh against a 5.5 GWh ceiling; 2025-08-15: ~3.1 GWh against ~12.7) and is released by h18–20. Participants that
use it hold energy through the solar hours **and release it into the evening ramp**.

**Why it does not re-open §5.**
1. **Sign.** Its behavioural content pushes discharge *into* h17–20. In 2024–25 the model already discharges
   *less* than measured at h18 (−131 / −766 MW, R-CAISO-24 §0). More evening discharge deepens the under-price.
   That is the R-CAISO-24 result again, read from the bid side.
2. **Reach.** Even a perfect match is capped by the bound: ≤ +$0.5 (2023).
3. **Coverage.** 0.2–5 % of storage MW in 2023, ~15 % in 2024. A self-selected subset cannot identify a
   per-class parameter for the fleet.
4. **Rule 13.** The bound is a conduct choice encoding each participant's expected evening price and RA
   position. It has no forward driver. As an LP floor it would pin the SOC shape to an observed outcome. Reading it
   as an aggregate "hold share" would be a fitted shape. **Admissible only as a report-only diagnostic.**

## 2. DO-NOT-REDO (new)

- Using RT EOH SOC bounds as a dispatch input or as a per-class battery parameter (§1: rule 13, coverage, sign).
- Re-opening R-CAISO-24 §5 on any input whose effect is to move h18 battery placement toward measured. The
  bound is on placement, so no placement input can exceed it.
- Re-scanning `PUB_DAM_GRP` for SOC: the EOH columns are RT-only by design.

## 3. Owner ruling

Decision card, 2026-10-01 (multi-select). Two of four options selected:

1. **Queue a report-only intake of the RT EOH SOC bounds** (`PUB_RTM_GRP`, 2023–25) as a storage diagnostic
   for the Run Explorer. **Never a solve input** (§1 point 4). Queued as **link 13, R-CAISO-31**.
2. **Queue scoping of the DMM SOC-outage series** (Battery Special Report Fig 2.26: quarterly mean share of the
   fleet's charging range lost to SOC outages/derates) as a candidate **physical availability** input. It is
   aggregate and digitize-only, and its price reach sits inside the same R-CAISO-24 bound. Queued as
   **link 14, R-CAISO-32**.

Not selected: re-opening §5 (it stays closed; no field, no cell). "Close link 10 → link 11" was not ticked, but
the chain goes on to link 11 under the standing direction, with the two new links queued after link 12.
