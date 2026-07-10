# MISO coal offer redesign — SOM conduct adjudication (2026-07-10)

**Status: PROBE (miso-53), not a keeper.** Keeper promotion is an owner
decision; `keepers.json` is untouched. This is the root-cause session the
miso-52 attestation queued: *"adjudicate the sigmoid deep-discount premise
against measured MISO IMM/Potomac SOM coal offer-to-cost markup data — if
real MISO coal offers near cost, the premise (not its parameters) is the
wrong market structure for 2023-2025."*

## 1. The question

After miso-50/51/52 (+ two zero-forcing ablation twins), the MISO coal
over-run — COAL_PRB +30/+25/+26 TWh, COAL_BIT +14/+15/+18 TWh vs actual
(2023/24/25), mirrored by CC_REGULAR −11/−17/−26 — was demonstrated robust
to five independent interventions (measured sigmoid params, daily gas
granularity, sigmoid key timescale, hydro completeness, all merchant floors
off) and is pure economic merit: ~70% of PRB capacity sat in
mustrun/committed tranches the gas-keyed sigmoid offered at ~$15-20/MWh —
below CC at every observed gas price, so the merit order never flips. The
remaining structural suspect was the sigmoid MECHANISM's premise: that
contracted coal discounts deeply below delivered cost to hold merit.
`results/calibration/FINDING-miso-burndown-2026-07.md` Evidence 2 already
showed the real market prices marginal coal at full delivered cost (actual
RT mean LMP $30.8 ≈ marginal coal's measured F923 SRMC $30.4, 2024).

## 2. The measured evidence (datatype `som-competitive-conduct`)

Intaken this session (rule 13-admissible market-conduct measurements;
transcription `data/raw/som-competitive-conduct/som_competitive_conduct.csv`,
PDFs `data/raw/MISO/`, freeze test
`tests/test_curate_som_competitive_conduct.py`; train-window years only per
rule 22 — the SOMs' 2018-2022 columns and the Winter-2026 quarterly
(Dec-2025..Feb-2026, H1-2026 locked window) are deliberately NOT
transcribed):

| statistic | 2023 | 2024 | 2025 | source |
|---|---|---|---|---|
| System price-cost mark-up (actual offers vs reference levels) | **+3.0%** | **−2.5%** | n/a (SOM pending) | SOM body PDF p.112 / p.120 |
| Output gap (economic withholding, low threshold) | 0.1% of load | 0.06% of load | 22/59/71 MW/hr (spring/summer/fall ≈ 0.03-0.09% of ~80 GW load) | SOM bodies; IMM quarterlies p.3 |
| Regulated coal starts offered economically (Table 7) | 44% | 47% | n/a | SOM Table 7, PDF p.67 / p.71 |
| Regulated coal starts must-run (self-commit), profitable + not | 42% + 14% = **56%** | 38% + 15% = **53%** | n/a | same |
| Merchant coal starts offered economically | 93% | 74% | n/a | same |
| Regulated coal net revenue | $5.75/MWh | $8.01/MWh | n/a | same |

The IMM's own reading: *"the mark-up was very small... the markets were
highly competitive overall"*; the output gap is *"effectively de minimis"*;
and *"MISO's regulated utilities often continue to operate their units as
'must-run', running them regardless of the price."* The 2024 appendix
(PDF pp.150-151) documents the mark-up methodology — actual offers vs
cost-based reference levels — and reports a −5% average under the appendix
aggregation (monthly range +6.2% to −17%); the body headline −2.5% is
carried as canonical, the variant noted on the row.

## 3. Adjudication

**The deep-discount premise is refuted for MISO 2023-2025.** Two distinct
phenomena were conflated in the sigmoid design:

1. **Energy offers** (the $/MWh bid of capacity above minimum load): the SOM
   measures these AT reference levels ≈ short-run marginal cost — mark-up
   ~0, economic withholding de minimis. Real MISO coal does **not** discount
   its incremental energy 30-50% below delivered cost; it offers it at
   delivered cost. The sigmoid — and the ERCOT-fitted sub-1.0 offer-curve
   band multipliers underneath it (COAL_PRB econ_low 0.77, committed
   0.90-0.95, COAL_WC 0.85) — priced MISO coal $15-20/MWh, below every
   observed CC SRMC, which is exactly the demonstrated-robust C1/C4/C3a
   failure signature (baseload-flat coal that never flips vs load-following
   coal at ~$30).
2. **Commitment** (whether the unit is online at all): here the
   non-economic behaviour is real and measured — must-run (self-commit)
   status on 56%/53% of regulated coal starts, 15% of starts unprofitable
   outright. This is the phenomenon the fuel-free `_mustrun` band
   represents, and the SOM **corroborates** that mechanism.

**Design consequence (rule 1: right structure first):** for MISO, the
gas-keyed sigmoid passthrough is REPLACED by near-cost offers; the
self-commit floor stays. Concretely (miso-53):

- `coal_prb_passthrough_sigmoid=False`, `coal_bit_passthrough_sigmoid=False`,
  `coal_prb_passthrough_tiered=False` (the follower tier rides the sigmoid).
  Every coal tranche above must-run passes **1.0 × measured F923 delivered
  fuel** (`coal_plant_monthly_pricing` stays on) — the SOM-measured discount
  depth, which is ~none. Registry-visible run flags, recorded in
  `run_config.json` (rule 24).
- The MISO COAL_* offer-curve bands are SOM-grounded in
  `_MISO_OFFER_CURVE` (`src/market_sim/pipeline/backcast_config.py`):
  every sub-1.0 heat-rate band multiplier is raised to exactly **1.00**
  (offers AT reference/cost; mark-up ~0 measured both signs, +3.0%/−2.5%),
  and every band already ≥ 1.0 (the rising incremental heat-rate shape,
  econ_high 1.19/1.10/1.15/1.02, peak 1.48/1.45/1.55/1.20) is kept
  byte-identical. This also retires MISO's silent inheritance of the
  ERCOT-fitted generic coal bands — the same rule-25 cross-ISO leak the
  sigmoid byte-copy was (G-26/#1347). Other ISOs' curves are untouched
  (verified: NEISO/PJM resolve identically before/after).
- The `_mustrun` band keeps its per-plant CAMPD sizing
  (`coal_mustrun_per_plant=True`, `thermal_tranches_MISO.csv` `mustrun_pct`,
  cap-weighted fleet mean ~24%) and its fuel-free price-taker bid — the
  representation of "runs regardless of the price".

### The tranche-share question (task step 2b) — resolved by dimension, not dodged

The task asked whether the mustrun/committed SHARES should re-derive from
the SOM self-commitment share instead of the CAMPD CF-based shares. The SOM
measures self-commitment as a share of **starts** (commitment decisions):
56%/53% regulated. A start-share is not a capacity share and cannot size a
tranche directly. More importantly, the CAMPD all-hours observed floor
(`mustrun_pct` ≈ Pmin × fraction-of-year-held-online, per plant) **is
already the realized self-commitment floor at plant granularity** — an
always-on self-committer keeps ~its Pmin, an economically-offered cycler
reads ~0. Replacing 44 per-plant measured floors with one fleet-level
start-share smeared over every plant would *lose* measured granularity
(rule 14) and manufacture a floor level no real unit operates at (rule 17
spirit). So: the SOM share **corroborates the mechanism and its magnitude**
(it says self-commitment is pervasive-but-partial and gently declining —
consistent with a ~24% cap-weighted fuel-free floor vs the fleet's ~36% CF
and with `committed`+`econ` now offered at cost), and the per-plant CAMPD
floors remain the sizing input. With committed/econ at 1.0 × SRMC the
committed-vs-econ boundary is price-degenerate, so no share re-derivation
is required for the offer level at all. If the owner wants a SOM-share
mechanism regardless, the honest construction would be
`floor = Pmin × selfcommit_share(owner_class, year)` with the
regulated/merchant split from EIA-860 sector — logged as an option, not
implemented (it stacks a second floor mechanism on a phenomenon the CAMPD
floor already carries, rule 19).

### Rule-19 reconciliation inventory (what floors/discounts MISO coal after miso-53)

| mechanism | state | phenomenon |
|---|---|---|
| `_mustrun` fuel-free band (per-plant CAMPD `mustrun_pct`) | **KEPT** | self-commitment (SOM Table 7) |
| gas-keyed passthrough sigmoid (PRB/BIT + follower tier) | **OFF for MISO** | (premise refuted: offers are near-cost) |
| sub-1.0 COAL band HR multipliers (generic inheritance) | **RAISED to 1.00 for MISO** | (same evidence: mark-up ~0) |
| ≥1.0 COAL band shape (econ_high/peak) | kept byte-identical | rising incremental heat rate |
| `coal_plant_monthly_pricing` (F923 delivered cost) | kept | measured fuel input (rule 13) |
| `commitment_screen_coal` (P0-pattern screen) | kept (inherited recipe, unchanged) | commitment scaffolding |
| `coal_takeorpay_from_data` / `coal_sync_srmc_tranche` / `coal_mustrun_online_pmin` | stay OFF (not stacked into this probe) | alternative contract/sync representations |
| `coal_econ_srmc_bound` | stays OFF (no-op here: with sigmoids off and bands ≥ 1.0 the ≥ 1.0 × SRMC property holds by construction) | — |

No mechanism was added; two discount surfaces were removed/re-grounded on
one measured anchor. C8 forced-energy exposure is unchanged by construction
(the redesign touches offer LEVELS, not floors; coal read 0.1-0.2% forced
through miso-50/51/52).

### Governance notes

- **Rule 23:** the re-grounding cites its source data (the SOM statistics,
  now an in-repo datatype with a freeze test). It responds to a
  measured-conduct publication, not to the residual — and it is registered
  whatever it scores (rule 15).
- **Rule 25:** per-ISO by provenance — MISO's own SOM grounds MISO's bands;
  the generic/other-ISO curves and `COAL_SIGMOID_DEFAULTS` entries for
  other ISOs are untouched. Their SOMs are separate adjudications.
- **Rule 26 (deleted means deleted):** `COAL_SIGMOID_DEFAULTS[MISO,*]` rows
  are NOT deleted: they are measured f.o.b.-derived values (frozen derive +
  freeze test, #1803), not residual-fitted knobs, and miso-50/51/52's
  registered bundles reproduce through them. What is retired for MISO is
  the *mechanism flag* in the recipe. If the owner wants the MISO sigmoid
  rows removed outright once miso-53 supersedes those probes, that is a
  follow-up decision.
- **2025 evidence gap:** the 2025 MISO SOM is unpublished as of 2026-07-10;
  the 2024 mark-up (~0) is carried into 2025 supported by the de-minimis
  2025 quarterly output gaps. The 2025 SOM's publication is the rule-23
  re-derive trigger (see the raw README's DATA NEEDED).

## 4. Results (miso-53 vs miso-52 / keeper miso-49)

*Filled in after the solve + scoring — see the registered bundle
`results/calibration/miso53_som_coal_offers` (+ `-ablation` twin) and the
dashboard entry `2026-07-10-miso-53-somcoal`.*

## 5. Deliverables

- Datatype: `som-competitive-conduct` (schema, raw CSV + README, curation
  script, tmp-CLEAN_DIR test, `regenerate_clean.py` + dictionary
  registration, reader `src/market_sim/data/som_conduct.py`).
- Raw PDFs: `data/raw/MISO/` (2023/2024 SOM bodies, 2024 appendix,
  Spring/Summer/Fall-2025 IMM quarterlies).
- Offer surface: `_MISO_OFFER_CURVE` COAL entries
  (`src/market_sim/pipeline/backcast_config.py`).
- Probe driver: `scripts/probes/_miso53_som_coal_offers.py` (main +
  zero-forcing ablation twin, rule 20).
- Bundles + dashboard registration per rule 15.
