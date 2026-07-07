# G-20c — NYISO downstate: locational-RCPF primary-source grounding

**Date:** 2026-07-07. **Branch:** `claude/nyiso-downstate-locational-scarcity-yyy26d`.
**Scope:** the two G-20c goals from `docs/g20-scarcity-price-formation-diagnosis-2026-07.md`
and `docs/nyiso-rcpf-overlay.md`. Goal 1 (downstate load shares) had **already
landed on main** this same day (commit `394e83c`, `nyiso-56-measured-zonal`);
this branch completes the **still-open half** — grounding the locational RCPF
curves against the primary source, closing the `TODO(SENY-MW)` main explicitly
left open.

---

## Where G-20c stood at branch time (already on main)

- **Load shares (goal 1, the named root cause): DONE.** `394e83c` made
  `eia_loader.load_zonal_shares` fall back to parsing the raw NYISO `pal`
  actual-load file directly, so the measured U3 hourly zonal shape reaches the
  solve even without the (gitignored) curated clean parquet. Downstate now peaks
  to its measured ~0.34 NYC / ~0.17 LI coincident share instead of the static
  Gold-Book flat 0.28 / 0.12. Registered as `nyiso-56-measured-zonal`: the
  NYC/SENY pocket tightens and the in-LP locational reserve co-optimization
  fires — 2023 NYC/Hudson LBMP to $1,684, C3c 2023 0→21 h (RT). (This branch
  independently reached the same finding; main's fix supersedes it.)
- **Interfaces (goal 1): measured or D1-blocked.** Central-East is measured DAM
  postings; Long Island is the measured Zone-K LCR/TSL cap (`nyiso_li_lcr_tsl`,
  #1345); UPNY-SENY (5,150) and Dunwoodie-South (3,900) are static Gold-Book
  estimates that bind ≤7 h/yr and are **not** the gating constraint — tightening
  them needs the measured per-interface series (data ask **D1**, unfulfilled).
  Main's doc flags the measured NYC locality import limit (**2,875 MW** vs the
  3,900 MW Dunwoodie energy-TTC) as the next import-discipline lever.

## This branch — goal 2: the locational RCPF curves, primary-source-grounded

`reserve_config.NYISO_RCPF_LOCATIONAL` (shared by the post-solve overlay and the
**live in-LP** `energy_reserve_coopt` path, `_nyiso_design`) carried three
placeholders — East 30-min/$500, SENY at a 1,100 MW nesting midpoint, NYC $500 —
that main left open (`docs/nyiso-rcpf-overlay.md`: "`TODO(SENY-MW)` remains open
pending a manual transcription of that PDF"). The value is not in an unfetchable
PDF: the **NYISO State-of-the-Market report is in-repo**
(`data/raw/NYISO/NYISO-{2023,2024,2025}-SOM-*.pdf`) and states the as-enforced
products verbatim, identically across all three years (2024 p.297):

| Product | placeholder | **SOM (primary)** |
|---|---|---|
| East | 30-min, 1,200 MW, $500 | **10-min, 1,200 MW, $775** |
| SENY | 1,**100** MW, $500 | **≥1,300 MW** all hours, $500 |
| NYC 30-min | 1,000 MW, $500 | 1,000 MW, **$25** |
| NYC 10-min | 500 MW, $500 | 500 MW, **$25** |

Applied in `reserve_config.py` + `data/nyiso_reserve_requirements.py` crosswalk +
`docs/nyiso-rcpf-overlay.md`. The product name sets the in-LP reserve class, so
the corrected **10-minute East** now draws only quick-start {gas_ct, oil}
headroom — the downstate F–K peaker fleet the real market commits for reserve.
Verified live in the co-opt: **7 families (4 now quick-start), ORDC steps
$3–$775** (was 3 quick-start). Rule-12/13 grounding — real published values, not
fitted to residuals — and it fixes three wrong entries, not just the SENY MW.

## Re-solve A/B (single delta on main's recipe)

`nyiso-57-locational-rcpf` = `nyiso-56-measured-zonal` recipe (measured shares +
LI-TSL + v2 rates + downstate CT gas) with the **only** change being the
SOM-corrected `NYISO_RCPF_LOCATIONAL`. Official DA-expressible scorer:

| criterion | nyiso-56 (baseline) | nyiso-57 (+ SOM RCPF) |
|---|---|---|
| price_mean | CAVEAT — 2023 $31.59 | CAVEAT — 2023 **$30.76** (closer to $30.29) |
| price_shape | CAVEAT (2024 NRMSE 0.20) | FAIL (2024 0.20 — boundary flip) |
| price_tail | FAIL — 2023 21 h vs 1 (DA) | FAIL — 2023 **15 h** (less over) |
| determination | NOT-YET | NOT-YET |

**Reading.** The correction is a **grounding**, not a scorecard win: the placeholder
$500 NYC penalty was over-firing (baseline 2023 over-tails 21 h vs the DA-expressible
actual of 1), and the SOM-correct $25 pulls it toward actual (15 h) while the mean
improves slightly. 2024 price_shape tips CAVEAT→FAIL at the 0.20 boundary (both read
0.20 — rounding noise, not a real regression). The deep 2025 tail (18 vs 12 DA / 7 vs
42 RT) is the #1344 residual for both. Determination NOT-YET for both, as for every
prior NYISO keeper. Promotion over nyiso-56 is an owner call on **faithfulness**
(rule 1) — the values are now the published truth, not placeholders — not on MAE.

## The residual — #1344, not transmission or curve values

The 2024/2025 deep >$300 tail stays under (main's measured-zonal: 2025 14 h vs 42
h actual) because the published locational requirements are **static** and
reality's downstate requirement **rises with conditions** (thunderstorm alerts,
contingencies). That is the **#1344 condition-varying-requirement channel**
(`nyiso_dynamic_reserve_requirements` + `data.nyiso_reserve_requirements`), built
and data-blocked on the **Ask-B** measured series
(`docs/handoffs/nyiso-data-asks-2026-07.md`), which needs owner authorization and
touches no holdout. Until Ask-B lands, the deep tail is a ledgered limitation;
forcing it any other way (inflating the requirement, subtracting headroom) is
forbidden (rule 11). With the SOM values now grounded and the SENY placeholder
closed, no downstate-scarcity structural claim rests on an un-grounded number.
