# ERCOT-94 diagnosis — the 2023-summer-LMP miss is a scarcity-tail (ORDC) collapse, not an offer-wall level

**Verdict: the ERCOT-94 season-conditioned offer wall is NOT a keeper for the
2023-summer-LMP objective. Do not promote it.** It is a structurally valid
mechanism for the *winter* cold-snap over-pricing (the ERCOT-93 zero-spurious
trip), but it is orthogonal to what actually blocks the ERCOT keeper. The real
lane is ORDC / reserve scarcity-pricing recalibration (see ERCOT-95 handoff).

## The objective (owner)

"We're really just trying to fix 2023 summer LMP." The ercot91 keeper
(`2026-07-20-ercot91-seasonal-drag-fullspan`) is **NOT-YET**, blocked by
**C3c price-tail FAIL**; **C3a-2023 = −32.5%** (load-weighted) is a ledgered
caveat sharing the same root. Fixing 2023 summer LMP = restoring the scarcity
tail.

## The decisive evidence (ercot91 committed 2023 sidecar; rule 15, no re-solve)

C3c counts hours the model LMP (settlement = energy dual + ORDC/reserve overlay)
exceeds $200/MWh vs the committed RT actual tail:

| C3c price_tail | model | actual (RT) | ratio |
|---|---|---|---|
| 2023 | 40 h | 181 h | **0.22×** (FAIL) |
| 2024 | 13 h | 53 h | 0.25× |

Decomposing `results/calibration/ercot91_seasonal_drag_fullspan/hourly/system_2023.parquet`
(P1 pass, system = max zonal dual):

- **The ORDC adder fires in only 3 hours all of 2023** (max $1920/MWh,
  annual-mean contribution **$0.27/MWh**). The overlay is effectively inert.
- The 40 model >$200 hours are the **energy LP dual hitting HCAP** ($3,000–5,051)
  in genuine shortage — **not** the ORDC overlay (39 of 40 are energy-only >$200,
  ordc=0).
- Model price-band histogram: **[50,100) = 236 h**, **[100,200) = 9 h**,
  [200,1000) = 11 h, [1000,9999) = 29 h.

The ~141 missing tail hours (181 − 40) are **not** sitting just below the
threshold — the near-miss [100,200) band is only **9 hours**. The model prices
those hours **~$50–100** while reality was **>$200**. That is a scarcity-*pricing*
gap of $100–$1,900/MWh, not an energy-offer-level gap of a few percent.

## Why the season-conditioned offer wall cannot close it

The ERCOT-94 MEASURE (`scripts/probes/_ercot94_season_offer_gap.py`, full-year
corpus) quantified the DJF-vs-JJA offer-level split per net-load bin:

- Season-conditioning is mostly a **winter-cheaper** signal (fixes the Jan-14/15
  cold-snap over-pricing). For **summer** it barely moves: ST b4 pooled 29.5 → JJA
  32.5 (~+10%), b5 34.9 → 35.6 (~+2%); CC/CT JJA ≈ pooled (summer already
  dominates the high bins).
- **b6 — the scarcity tail bin — has zero DJF coverage in 2023** (2156 JJA
  intervals, 0 DJF): it is *already* pure-summer, so season-conditioning changes
  it by nothing.
- Offer multipliers top out ~30–50× delivered gas ≈ $90–150/MWh outside genuine
  shortage. A 2–10% bump on a $150 offer is $165 — it **cannot** manufacture the
  $200–$2,000 hours that ORDC/reserve scarcity pricing produces on tight summer
  afternoons.

So the offer wall (season-conditioned or not) operates on the energy merit-order
mid-band, which is orthogonal to the missing tail. Enabling the ERCOT-93 steam RT
wall (which season-conditioning would make winter-safe) only "improves mid-band
fill" per that handoff — it does not add >$200 tail hours either.

## Root cause (the ercot91 attestation says it directly)

> "SCARCITY-TAIL COLLAPSE ON THE CORRECTED AVAILABILITY ENVELOPE … on the
> corrected, measured envelope the tail stays collapsed because the offer/scarcity
> calibration predates the correction."

The ercot80/82 availability correction removed the phantom fleet tightness the
deposed ercot76 keeper used to trigger the tail. On the corrected/measured
envelope the model's operating reserves stay high, so the ORDC LOLP term ≈ 0 and
the adder is inert. `src/market_sim/config/scenarios.py` states it in-line: *"the
over-supplied-fleet ORDC overlay stays inert (reserves …)."*

## The real lane (→ ERCOT-95)

Recalibrate the ERCOT ORDC / reserve scarcity representation
(`src/market_sim/results/scarcity.py`: `ordc_adder`, `lolp`, `reserve_headroom`,
`load_lolp_params`; knobs `ordc_voll`, `ordc_mcl_mw`, `ordc_lolp_sigma_mw`,
`ordc_lolp_mu_mw`, `ordc_lolp_shift_sigma`, `ordc_multistep_floor`,
`ordc_as_plan_mw`) so the tail regenerates from **measured** reserve/LOLP drivers
— never a fitted availability haircut / phantom tightness (that was ercot76,
rejected; rules 1/11). Central question: why does modeled `reserve_headroom` stay
so high on the 181 actual 2023 tail hours that LOLP≈0? Cross-check against ERCOT
PRC / RTORPA published series. Measure-first, then a 2023 throwaway A/B (rule 16),
then full-span 2023-2025 in one bundle.

## Byproducts delivered this session

- **Offer-wall artifacts re-derived on the full-year NP3-965 corpus** (they were
  stale sample-day, CC/CT wall had no 2023): `ercot_sced_offer_wall_condbinned.json`,
  `ercot_sced_offer_wall_steam_condbinned.json`,
  `ercot_shoulder_online_span_steam_condbinned.json`. The keeper consumes the CC/CT
  wall, so **the ercot91 keeper should be re-solved on these refreshed walls** as
  part of the ERCOT-95 lane (it stays NOT-YET on C3c regardless).
- ERCOT-93 core wiring (`docs/handoffs/ercot93-core-mechanism.patch`) applies
  cleanly on main; the 11 steam-RT tests pass with it applied. Left as a patch
  (fleet.py/scenarios.py exceed push_files' size limit); not needed for this
  diagnosis.

## Data-integrity note for the owner (corpus defect)

`data/raw/ercot/2026-02.part0001–0009.parquet` (an out-of-band "Add files via
upload" batch, Dec 3–9 2025 delivery) are in a different schema variant **missing
the `HASL` column** (they carry "AS Awards/Capability" instead of the "Ancillary
Service *" responsibility columns, HASL, LASL, "Telemetered Net Output"). They
crash all three offer-wall derives on year 2025. They were quarantined this
session (`git update-index --skip-worktree`) so the derives run on the clean
corpus — which is consistent with the derives' own documented design ("2025 Nov
partial and Dec absent"). **Recommend re-intaking that batch with HASL or removing
it.** part0000 does carry HASL but is a non-representative fragment of the same
7-day partial upload, excluded with the batch for consistency and to reproduce the
prior byte-identical artifacts.
