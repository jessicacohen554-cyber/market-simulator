# FINDING — closeout-PJM-w3 phase 0: the Elliott probe's load shed comes from a double-counted baseline, not missing DR or imports (ZERO LP)

Lane `closeout-PJM-w3` (branch `claude/closeout-pjm-w3`, from `90cea720`), desk lever (4). Probe
`scripts/probes/_closeoutpjmw3_elliott_supply_identity.py`. It reads the Elliott probe's 2022 leg
(`claude/closeout-pjm-elliott-2022` @ d4ea021f), the keeper's 2022 sidecars, the digitised GADS series, eDART
planned and maintenance outage, and EIA-930 PJM interchange. **This bears on the pending Elliott promotion card.**

## 1. Emergency DR and emergency imports are not the missing supply

- **DR is already in the demand.** PJM's report gives about 1,100 MW of actual Load Management reduction on
  23 Dec (from 18:00) and about 2,400 MW on 24 Dec (from about 06:00) (report pp. 41–42). EIA-930 demand, which is
  the model's demand row, is metered load, so it already nets those reductions. PJM's own "131,113 MW peak" adds
  DR back in; EIA-930 does not. Adding DR as supply would count it twice.
- **PJM was exporting, not importing.** EIA-930 shows PJM a **net exporter** of 5.6–10.7 GW through the 23 Dec
  hours where the probe sheds load. On 24 Dec it exported 0.5–3 GW in most shed hours and imported only around
  11:00–15:00 (4–5.5 GW). The report confirms "PJM did not load emergency imports on Dec. 24".
- **The model exports less than PJM did.** In those hours the probe exports 0.4–1.0 GW on 23 Dec (the
  `pjm_external_net_position_cut` p95 floor) and holds about ±0.5 GW on 24 Dec. Matching real interchange would
  make the shortage deeper, not shallower.

## 2. The real cause: the increment form stacks on a baseline that is ~13.5 GW too deep

Model thermal unavailable MW (Σ max-cap − cap) against the measured total (GADS forced and derate, hourly, plus
eDART planned and maintenance, daily):

| | 23 Dec 00–04 (pre-front) | shed-hour mean (19 h) |
|---|---|---|
| keeper | 31.3 GW | 34.0 GW |
| Elliott probe | 31.6 GW | 58.9 GW |
| measured total | 18.0 GW | 45.4 GW |
| **probe − measured** | **+13.6 GW** | **+13.5 GW** |

The excess is **constant across all 72 hours**: it is exactly the pre-event baseline excess, carried through the
event by the increment form (measured rise net of the model's own rise). The pre-front breakdown by fuel:

| fuel | model | GADS forced |
|---|---|---|
| gas CC | 13.4 GW | 3.7 GW (all gas) |
| gas ST | 5.5 GW | (included in gas above) |
| coal | 11.8 GW | 8.3 GW |

This is the pjm-161 over-assertion again: the CAMPD envelope declares more outage than PJM publishes, and wrongly
so in the hours that set price.

## 3. What follows

- **The 55,952 MWh of unserved energy is mostly an artifact.** With outage at the measured level, the probe's
  shed hours carry about 13.5 GW more supply. The probe's mean shed is 2.9 GW.
- **The C3a/C3b 2022 gain may not hold on structure.** The keeper's headroom in those hours (w2 census: 20.8–21.7
  GW on 23–24 Dec) minus the measured-level increment (keeper 34.0 → measured 45.4 GW, about +11.4 GW) leaves about
  10 GW. That means no reserve shortage, so prices fall back toward a few hundred dollars and 2022 C3a moves back
  toward about −15 %. *Estimate; it has not been solved.*
- **The other half of the real tightness is exports.** Real PJM exported 5.6–10.7 GW on the 23 Dec evening, against
  the model's 0.4–1.0 GW. Those were firm schedules and emergency sales to TVA and Duke, not price-driven exports.
  The model's export is a p95 statistical floor. An hourly measured interchange pin would break rule 13 (it pins an
  output). There is no admissible measured *driver* for the export schedule on disk.
- **The structurally faithful form is the level form,** with fleet outage equal to the measured total in the
  window, not the increment. On the arithmetic above it does not create the shortage on its own. Real PJM's
  shortage came from the measured outages **plus** firm exports that the model does not carry.

## 4. Asks

1. **Promotion card (owner, via desk).** The Elliott probe's price gain rides partly on a ~13.5 GW double count of
   baseline outage. Recommendation: **hold the card**. I can phase-0 a level-form overlay
   (`pjm_elliott_measured_outage_overlay` grain switch: increment → level, rule 19) and quantify it before the owner
   rules. If the level form loses the C3a fix, the honest reading is that the firm-export schedule is the missing
   structure, which is data-limited.
2. **Data (owner download).** A measured export-schedule driver would make the export half simulable: PJM tagged
   firm interchange schedules or OASIS reservations for 23–24 Dec 2022 (PJM Data Miner "Scheduled interchange" /
   `rt_scheduled_interchange`, if public).
