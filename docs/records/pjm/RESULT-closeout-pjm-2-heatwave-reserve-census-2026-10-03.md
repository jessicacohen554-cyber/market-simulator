# RESULT — closeout-PJM-2 step 4: June 23–25 2025 heat-wave reserve census (zero LP)

The readings were pre-fixed in `PRECOMMIT-closeout-pjm-2-heatwave-reserve-census-2026-10-03.md`, pushed at `75c888f5`
before any number below existed. The probe is `scripts/probes/_closeoutpjm2_heatwave_reserve_census.py` →
`results/phase0/pjm/_closeoutpjm2_heatwave_reserve_census.json`. Keeper `w0_pjm_span`, 2025 leg. No LP, nothing
armed, no cell moves.

**Window.**
- `H` is Jun 23–25, 12:00–22:00: 33 hours.
- `H*` is the subset where real system RT is at least $400: 9 hours. Real RT peaks at $1,830, and W0 prices those
  same hours at $103–465.
- The W0 reserve dual is 0 in all 33 hours.

## Readings, applied as fixed

| id | result | verdict |
|---|---|---|
| R1 | `G` over `H*`: min −181, median **767**, max 1,588 MW | **Near-binding** by the letter. But see the nesting correction below. |
| R2 | `ΔU(d) = U_p − U_m`: −7,378 / −5,575 / −7,713 MW (Jun 23 / 24 / 25). The model already carries **5.6–7.7 GW more** unavailable capacity than PJM's published outages (U_m 23.4–25.1 GW vs U_p 16.6–17.8 GW). 0 of 9 `H*` hours have `ΔU ≥ G`. | **NOT CONFIRMED** |
| R3 | Of the pool headroom in `H*`: **99.2 %** sits on offline units, 87.4 % on CT/oil, and 87.3 % on offline CT/oil | Offline share ≥ 50 % |

**Nesting correction** (stated, not a re-read).
- The PRECOMMIT defined `G` against the sum of the two family requirements:
  - `pjm_primary`, RTO: 3,868 MW;
  - `pjm_primary_mad`, MAD: 2.6–2.8 GW.
- MAD is a locational sub-requirement nested inside the RTO family. MAD-held MW also count toward the RTO, so the sum
  double-counts. (Hour 4171 reads `G` = −181 with a zero dual, which shows the double count.)
- Against the RTO requirement alone, `G` over `H*` is min 2,625, median **3,571**, max 4,396 MW. That is **not**
  near-binding at the 2,000 MW bar.
- R2 and R3, and the decision, are unchanged by the correction.

## Decision (the pre-fixed branch)

**R2 NOT CONFIRMED, and R3 offline share ≥ 50 %.**
- **Why the dual stays at $0.** In the `H*` hours the pool headroom is 6.5–8.2 GW against the 3.9 GW RTO requirement,
  leaving 2.6–4.4 GW spare. Almost all of it is **offline** CT/oil capacity, which the not-online-gated pool counts
  as reserve.
- **Not an availability gap.** The model already removes more capacity than PJM's outage tickets: on the
  outage-ticket basis, which is a bound (the model's `pmax − cap_mw` also carries ambient and seasonal derates).
- **The open object is reserve-pool formulation**, i.e. whether offline quick-start capacity should count against
  PJM's synchronized/primary requirement in extreme-heat hours. That object's prior verdicts:
  - `pjm_reserve_pergen_sync` is R (pjm-h3, the online-gated synchronized split);
  - `reserve_deliverability_scoping` is I;
  - `ordc_scarcity_overlay` is G.
- This census adds an hour-level measurement of the 2025 heat-wave window. pjm-h3 refuted the sync leg on a
  fleet-wide nonzero-dual-hours bar (1.22 % of hours against 20 %). Whether this is "new evidence" enough to re-open
  the R cell is the owner's call.
- **Recommendation to the desk.** Record 2025 C3a/C3b as a documented FAIL with this census as its frontier
  candidate: heat-wave reserve scarcity on a pool where offline quick-start capacity counts as reserve. No lever is
  proposed.

## Limits

- **Published outages are daily** (lead-0 tickets, RTO). The model's are hour means over the window.
- **The two bases differ.** PJM tickets are on the ICAP basis; the model's are on the seasonal-pmax basis. The model
  also carries ambient derates.
- **Headroom is per unit.** It is `min(cap_mw − mw, ramp10)` per unit, with no tier or deliverability split. MAD's
  own locational margin was not computed.
