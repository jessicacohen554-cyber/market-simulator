# RESULT — NWPP-NEXT-10: EIA-860 exit-month routing of the CAMPD outage layer — PROMOTED, keeper #16 (owner, 2026-09-29)

**Arm:** keeper #15 (`2026-09-28-nwppnext8-coal-monthly-pile`) plus `unit_outage_exit_ym_from_eia860=true`.
Precommit: `docs/handoffs/PRECOMMIT-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md`.
**Solve:** seven year-isolated shards at pin `0ec8eb79`. Every hard stop passed.
**Registered:** `2026-09-29-nwppnext10-exit-month-routing`, bundle `results/calibration/nwppnext10xy_span`.
**Owner ruling (decision card):** "Promote on structure". It is now keeper #16, and #15 is pruned (rule 35).

## 1. Headline

| | Keeper #15 | Keeper #16 |
|---|---|---|
| Determination | NOT-YET on {dispatch_corr}, 1 record | NOT-YET on {dispatch_corr}, **1 record** (unchanged) |
| Failing record | C4 coal 2023 r 0.695 / NRMSE 0.283 | same (2023 byte-identical) |
| C1 / C2 / C6 / C8 | PASS | PASS |

- **2019 and 2021–2025 are byte-identical to keeper #15** (max |Δ| 0.0 MW in every class-hour). This matches the
  zero-LP prediction and confirms G-DRIFT empirically.
- **2020 only:** 11 of 161 verdict records move, and all stay PASS → PASS.

| 2020 record | Keeper #15 | Keeper #16 |
|---|---|---|
| C4 coal r / NRMSE | 0.762 / 0.157 | **0.772 / 0.152** |
| C4 gas r / NRMSE | 0.831 / 0.180 | 0.830 / 0.171 |
| C1 COAL_PRB | +2.14 TWh | **+4.20 TWh (worse)** |
| C1 CC_REGULAR | +2.22 TWh | **+0.75 TWh** |
| C1 CT_PEAKER | +0.07 TWh | −0.32 TWh |
| C1 CC_CHP | −1.23 TWh | −1.41 TWh |
| C1 COAL_BIT | +1.04 TWh | +1.03 TWh |

P1 class energy 2020: COAL_PRB 29.445 → 31.502 TWh, CC_REGULAR 53.806 → 52.338, CT_PEAKER 3.164 → 2.773,
CC_CHP 4.981 → 4.800.

## 2. What it fixed, and what it did not

- **Fixed:** Colstrip 6076 in 2020 was forbidden from its own measured output (5.855 TWh available against 7.935 TWh
  generated).
  - Retired Units 1–2 carry CAMPD post-exit darkness, 2020-01-02..12-31. Those windows had derated the surviving
    Units 3–4 bin, and the survivors' own windows divided by a retiree-inclusive denominator.
  - Now Colstrip has 7.913 TWh available, and the model dispatches all of the gain (+2.06 TWh). It displaces gas.
- **Not fixed, and exposed:** COAL_PRB 2020 was already +2.14 TWh long. It is now +4.20 TWh.
  - The extra Colstrip energy is physically available, so the remaining over-burn belongs elsewhere in the PRB fleet's
    economics or availability, not in Colstrip's outage input.
  - This is the rule-14 reading: an accurate input exposes a miscalibration; it does not create one.

## 3. Lever 1 (coal inventory-management floor): closed at phase 0

Owner card "Close lever 1, pivot":
- PacifiCorp's per-plant targets are redacted.
- The only public band (2009, Utah-only, "two to three months") does not cover Bridger, and 2023 stocks sat below
  it all year.
- PRECOMMIT §0 has the census.

## 4. Routed (for NWPP-NEXT-11)

1. **C4 coal 2023 (r 0.695), still the only failing record.** It is a PacifiCorp supply-shock and conservation
   year. Measured same-year receipts (NEXT-9, R), S_min (refuted), and a days-of-burn floor (no public
   identification) are all closed. What remains open is an owner-sourced confidential target, or a new structural
   idea with a measured identification.
2. **COAL_PRB 2020 +4.20 TWh.** Which PRB plants over-run once Colstrip is physically right?
   - Zero LP: per-plant `m_mon` against CEMS.
   - Candidates: Wyodak, Dave Johnston, Naughton and North Valmy availability or cost.
3. **Generic coal availability below measured generation** (zero-LP census,
   `scripts/probes/_nwppnext10_coal_availability_census.py`):
   - Naughton 4162 is short by 0.35–0.62 TWh every year 2021–2024.
   - Bridger 8066 is short by 0.92 TWh in 2025.
   - Colstrip is short by 0.05–0.54 TWh in 2021–2025.
   - None of these are retirees; the base 0.89 / 0.97 statistical availability looks tight for high-CF units.
4. **Economic lay-up booked as outage:** Centralia 3845 and North Valmy 8224 show whole spring months at zero
   availability.
5. SNV residual shed, internal-link over-flow, the Bridger coal tranche row, and solve time: carried from
   HANDOFF-nwppnext10.
6. **Environment:** `audit_keepers` E14 warns that the shard containers solved on highspy 1.15.1, pandas 3.0.6,
   pyarrow 25.0.1 and pydantic 2.13.5 against pins 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4. 2021–2025 reproduced keeper #15
   byte-identically regardless.

## 5. Retrievability (rule 34(e))

- **On `main` with this lane's PR:**
  - the keeper bundle `results/calibration/nwppnext10xy_span` (the rule-15 slim set plus `hourly/`);
  - its registry sidecar;
  - its run payload.
- **Leg SHAs (provenance only):**

  | Year | SHA |
  |---|---|
  | 2019 | `377a507b` (retry; the first 2019 shard stalled and was archived) |
  | 2020 | `b43db84f` |
  | 2021 | `f6fcd64a` |
  | 2022 | `57f4b1a6` |
  | 2023 | `610b20ea` |
  | 2024 | `9ed4df46` |
  | 2025 | `5bba8c73` |

- The per-year leg dirs are gitignored. A re-solve would be 7 shards (~40–55 min each, ~145 min for 2019).
