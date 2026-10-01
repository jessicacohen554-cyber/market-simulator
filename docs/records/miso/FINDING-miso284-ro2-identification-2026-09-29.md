# FINDING miso-284 (RO-2): MISO-South load-pocket commitment has a published driver but no published level (ZERO LP)

**Session:** miso-284 (2026-09-29). **Keeper:** `2026-09-28-miso-280-splitremap` (unchanged). **Solves:** none.
**Lane:** RO-2 `scuc_load_pocket_commitment`. It was un-routed by the owner on the miso-283 card and opened by the miso-284 card (*"Park, go to RO-2"*).
**Evidence:** `results/phase0/miso/_miso281_south_steam_oom.json` (re-read); EIA-860 tip (new-build census); a public-source search (§3).

## 1. Answer

The mechanism is **real and located**, but its **level is not identifiable from any admissible input**.
- The measured out-of-merit South steam sits on the units MTEP15 publishes as VLR-eligible.
- It falls as new CCs come online inside the pockets.
- The quantity a floor or constraint needs, **MW of local generation per pocket (or the pocket import limit)**, is set by MISO/Entergy Operating Guides that are **not published**.

## 2. Where the out-of-merit steam sits (measured, 2019–2025)

Out-of-merit (OOM) energy = hours the measured hub RT LMP sits below the plant's own measured cost (miso-281 construction), in TWh:

| Plant | Pocket (MTEP15 list) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ninemile Point 1403 | DSG | 4.87 | 4.32 | 3.48 | 2.54 | 2.35 | 3.78 | 3.11 | 24.45 |
| Sabine 3459 | WOTAB | 2.78 | 4.04 | 2.43 | 1.40 | 2.73 | 3.13 | 2.79 | 19.30 |
| Lewis Creek 3457 | WOTAB / West | 1.76 | 1.82 | 0.92 | 0.98 | 1.01 | 1.51 | 1.35 | 9.35 |
| Little Gypsy 1402 | Amite South | 2.30 | 1.49 | 0.50 | 0.43 | 0.45 | 1.01 | 0.60 | 6.78 |
| Waterford 8056 | Amite South | 0.59 | 0.11 | 0.21 | 0.15 | 0.16 | 0.24 | 0.24 | 1.70 |

- These five eligible plants carry **~62 of ~81 TWh (≈76 %)** of all South OOM steam over the span.
- The rest is spread across Big Cajun 2, Brame, Gerald Andrus, Baxter Wilson and Teche.

**Candidate driver (public, forward-regenerable):** the pocket's local fleet. New in-pocket CCs entered from EIA-860:
- St. Charles PS (Amite South, 2019)
- Lake Charles PS and Washington Parish (2020)
- NOPS (DSG, 2020)
- Montgomery County (WOTAB, 2021)

Little Gypsy's OOM falls 2.30 → 1.49 → ~0.5 TWh across exactly those years. Ninemile and Sabine fall less cleanly. This supports a **pocket local-commitment constraint** over a constant requirement, met by the cheapest local units, so the fleet evolution does the year-to-year work. That is the rule-17 forward story. What that story still lacks is the requirement's level.

## 3. The level: public-source search (this session, plus miso-280 §2)

| Source | Gives | Class |
|---|---|---|
| MISO `Resource_Uplift_by_Commitment_Reason.xlsx` (monthly, Dec-2022 onward) | per-commitment LRZ, MW, reason; **LRZ 9/10 never appear**; post-DA commitments only | outcome |
| MISO `YYYY_Historical_RT_RSG_Commitment.csv` (2023–25) | RT commitments by constraint (`BASE_SETEX` 150 intervals in 2024, `BASE_AMSOIF` 23 in 2025) | outcome, RT only |
| MISO VLR Commercially Significant study (2025–26) | pocket interface **names** (`BASE_AMSOIF`, `BASE_DSGAIF`, `BASE_SETEX`), load shares; **no MW limit** | structure only |
| Entergy LPSC filings (2024–25) | import-capability **increments** (+250 / +500 MW); single-line ratings (Nelson–Richard ~1,700 MW) | deltas, no base limit |
| PUCT 46416 (MTEP15 VLR study) | ~10,850 MW VLR-eligible fleet; unit-by-pocket lists **without MW or requirement** | eligibility, pre-2019 |
| MTEP22 voltage-stability analysis | may carry a transfer limit (Franklin–McKnight, Mt Olive–Hartburg) | **unread: 403 from this container** |
| IMM SOM 2019–2024 | VLR RSG $ | outcome |

VLR interfaces do not appear in the DA binding-constraint history. There is no admissible MW requirement or import limit for any year 2019–2025.

## 4. What an arm would have to use instead, and why each is refused or open

- **Identify the requirement from observed conduct** (e.g. pooled minimum online capacity per pocket): this is the identification route nyiso-97 §5 refused for NYISO. It fits the level to the conduct it is meant to explain (rules 1/13). Not proposed.
- **Own-year floors:** refused (rule 13).
- **Physics from the network** (pocket load vs N-1-G-1 import capability): needs a pocket-level reduced network and published interface limits. Neither exists (§3). The one open lead is MTEP22 (403 here; fetchable from a browser).
- **Ledger it:** C1 ST_GAS 2019 (−8.003 TWh vs an 8.00 band) stays a routed model-class miss. That is its status today.

## 5. Matrix

MISO `scuc_load_pocket_commitment` stays `·`, with this evidence added. No LP test was run, so no verdict is minted.

## 6. Owner ruling (2026-09-29, miso-284 card)

**"Mark blocked, go to night (Recommended)"**. Actions taken:
- MISO `scuc_load_pocket_commitment` moves `·` → **`G`**: identification-blocked. The same bar applies as NYISO's nyiso-97 §5: no published level, and identification from conduct is refused.
- C1 ST_GAS 2019 stays a ledgered, routed model-class miss.
- Next lane: queue item 3, the system night overshoot (`diurnal_price_amplitude`, G, raised by miso-283). No frontier is declared, because the rubric still fails on three routed misses.

What would re-open the cell: a published MW pocket requirement or interface limit. The first thing to check is MTEP22's voltage-stability transfer limits, which need a fetch from a browser.
