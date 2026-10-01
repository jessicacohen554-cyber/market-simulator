# FINDING — capx D28: "the capacity curve pays $0 exactly where the model sits" is characterized across all four capacity-market ISOs — the curves are (with one MISO-specific exception) published-faithful; what is wrong is WHERE THE MODEL SITS and WHAT A CLEARING PRICE IS, and the census splits 2 confirmed / 1 hindcast-confirmed / 1 latent

**Lane:** capx D28 (Phase-0), charter `docs/handoffs/capx-director-prompt-pack-2026-08.md`
§D28 (r#25 reconstruction; a running session's own prompt governs — this session ran the
identical text). **Docs only, ZERO solves**: every number below is read from a committed
artifact or computed by the repo's own committed instrument
(`scripts/validate_capacity_prices.py`) on committed ledgers and committed published-data
rows — the D17 K2 evidence class. The instrument's output is committed as
`docs/handoffs/d28/pass2-instrument-run-2026-09-01.json` (invocations + bundle provenance
inside). No mechanism, no `ScenarioConfig` field, no matrix cell, no keeper/board/verdict/
marker write. Collision check at write: D27 (the MISO T1-H HEAD re-measure) has NOT landed
as of `3c1f9642` — the committed FFR-2B record remains the current MISO-residual context and
is cited as such.

## 0. Verdict (one paragraph)

The charter's object — *a modelled capacity-demand curve that pays nothing exactly where the
model sits* — is real in every ISO measured, but it is **not one curve defect in four
places**. Decomposed, it is (a) **a position defect**: in the $0 screen years the model's
accredited position sits **6–22 points of reserve ratio LONGER than the real market's
cleared position in the same delivery years** (PJM +9 to +14 pts over 2021–2025; NEISO
+21/+6/+7 pts in its three $0 crossover years, −3/+1 in the dip/rebound; MISO +11 pts at
the one year with a committed measured comparison),
and it **oscillates** (long → mass screen failure → exit wave → dip inside the curve →
pay/reverse) where every real market's position is **stable at 1.00–1.06**; plus (b) **a
missing clearing half**: every one of these auctions produces a price from **supply meeting
the curve** — de-list bids (ISO-NE), sell offers (PJM/NYISO), the marginal offer against a
vertical requirement (MISO pre-2025) — so the real record contains **no $0 clearing at all**
(while-long floors in the in-repo record: NEISO $24.0/kW-yr, PJM $10.6/kW-yr, NYISO
$19.3/kW-yr, MISO $0.55/kW-yr — the 2017-18 all-zones $1.50/MW-day print),
while the model evaluates the demand curve alone at a census quantity and reads $0 whenever
that quantity is past the zero-cross. The curve SHAPES themselves adjudicate **innocent for
NEISO** (re-derived from published auctions, RC-R R2; within −22 %…+24 % at the auctions'
own positions), **exact for NYISO** (machine-precision reproduction of three spot outcomes) and
**exact-where-published for PJM** (+0.002 % at 2026/27); **MISO alone also carries a shape
defect** — its RBDC cap/zero x-positions (0.97/1.05) are documented first-order stand-ins,
and at the market's own measured PY 2025-26 position (+1.7 % long) the model curve pays
$52.1/kW-yr against a real $79.1/kW-yr with 78 % of it concentrated in summer, a
concentration the documented ONE-POSITION LIMIT makes unreachable. Census: **MISO and NEISO
confirmed** (the two chartered ISOs), **PJM confirmed in the hindcast window** (its forecast
sits on the SHORT side, and from delivery 2028/29 PJM's published design carries a FERC
price floor that makes $0-at-long impossible by construction), **NYISO latent** (its default
posture prices a flat $110/kW-yr — the curve is not consulted — and the committed curve-ON
probe pair shows why the flip is withheld: arming the curve moved hindcast retirements 1.036
→ 3.318 GW against 1.488 actual). Rule 25 holds throughout: one defect *class*, four
per-ISO repair identifications, no shared fix.

## 1. The modelled object at HEAD (what exactly pays $0, and when it is live)

One seam prices adequacy for all three capacity screens (retirement, thermal entry, storage
entry): `MarketDesign.capacity_price_per_firm_mw_yr`
(`src/market_sim/config/capacity_market.py:715`), evaluated at
`capacity_reserve_position = accredited_firm_capacity_mw / resolve_adequacy_requirement_mw`
(`src/market_sim/model/capacity_evolution/adequacy.py:346`), computed once per year on the
entering fleet. The retirement screen threads `iso` and `year`
(`src/market_sim/model/capacity_evolution/retirements.py:859-861`), so the per-delivery-year
vintage table (`MARKET_DESIGN_VINTAGES`, `capacity_market.py:1599`) governs. What each ISO's
curve pays at a long position, at HEAD:

| ISO | vintage(s) | zero-cross (position) | past it pays | provenance of the zero |
|---|---|---|---|---|
| MISO | 2021-22 … 2024-25 | 1.0 + 1e-6 (vertical step) | $0 | published design — vertical curve, FERC ER23-2977 / 187 FERC ¶ 61,202 (demand-curve README) |
| MISO | 2025-26+ (seasonal RBDC, hold-last) | 1.05, all four seasons | $0 | **FIRST-ORDER, not published** (`capacity_market.py:1006-1008`) |
| NEISO | 2020-21 … 2027-28 (hold-last) | 1.0582 (FCA 13 published tail zero; FCA 11 geometry zeroes 1.0874) | $0 | published (RC-R R2 intake) |
| PJM | 2021/22 … 2027/28 | 1.064–1.074 per vintage (2026/27+: 1.045) | $0 | published VRR points |
| PJM | 2028/29+ (hold-last) | **none — FERC floor** | 0.537 × net-CONE ($63.9/kW-yr) | published (ER26-1556 collar) |
| NYISO | 2023-24+ | 1.12 | $0 | published 12 % Demand Curve Length |

**When it is live.** The FF-2C default (`ScenarioConfig.capacity_market_clearing_by_iso =
{PJM, MISO, CAISO, NEISO: True}`, `scenarios.py:3697-3704`) makes the curve THE default
adequacy price for those four ISOs in forecast/hindcast mode. NYISO is deliberately absent
→ its screens price the FLAT legacy anchor $110/kW-yr in every default run (its curve fires
only in explicit probe arms). Backcasts coerce the mapping to `None` and run no capacity
evolution (`scenarios.py:13940-13941`) — **no backcast keeper is touched by this object.**

Two stale docstrings found en route (routed, not edited — this lane writes no code files):
`capacity_price_per_firm_mw_yr`'s "only storage new entry threads [year]" (retirement and
thermal entry now thread it too), and `resolve_demand_curve_vintage`'s example "a MISO year
before PY2025-26 gets the 2025-26 RBDC" (pre-2021 years now hold-first to the 2021-22
VERTICAL vintage).

## 2. Where the model sits vs where the zero is — the claim made exact

Method: the repo's own P-2A/CR-2 instrument, Pass 2 (model-ledger position → HEAD curve →
vs published clearing), run read-only on the committed bundles; full rows in the committed
evidence extract. Positions are `firm_mw / requirement_mw` on HEAD's requirement resolution
(MISO factor 1.00715 × peak — the S-123 basis; NEISO 1.02861; PJM published FPR from
2025/26, composite 0.87102 × peak before). Ledger `reserve_margin` is firm/peak − 1
(`runner.py:4209`); the screens see the entering fleet, the ledger the post-evolution one,
so in exit years the deciding screen's position was HIGHER than the row shown.

**MISO** (`miso-2021-2025-realized-cmc-probe` ledgers; identical under restated and
adopted bases; ledger firm pre-dates the S-2 external tie, so a HEAD solve sits ≈ +2.9 pts
LONGER still):

| delivery yr | model position | model curve pays | real PRA (in-repo) |
|---|---:|---:|---|
| 2021/22 | 1.2383 | $0 | ≤ $5/MW-day in 10 of 11 zones (≤ $1.8/kW-yr) |
| 2023/24 | 1.1326 | $0 | $3.65/kW-yr seasonal sum (LRZ 9 separated higher) |
| 2024/25 | 1.1026 | $0 | $7.33/kW-yr (LRZ 5 at seasonal CONE, 872 MW deficit) |
| 2025/26 | 1.1296 | $0 | **$79.07/kW-yr** seasonal sum; summer $666.50/MW-day |

The scored FFR-2B pipeline leg (the exact run behind D17's object) shows the same shape on
its own committed margins (tie-exclusive ledger basis, HEAD requirement): ≈ 1.26 (2021),
1.21 (2023), 1.21 entering 2024 → 1.11 after the 11.9 GW wave, 1.21 (2025) — every screen
year past every zero-cross. Forward, at HEAD (`results/ff-t1f-s123/verify` ledgers): 1.083
(2026) → 1.070 → 1.063 → **1.022 (2029, curve pays ≈ $45/kW-yr)** → 1.004 (2030, ≈ $73) —
the position enters the curve only after three $0 screen years, the same span in which
those ledgers land their non-coal exits (gas_st decides 2027, oil executes 2029 — D17 §2).

**NEISO** (`neiso-2023-2027-crossover-rcrepair` ledgers — the RC-R treatment itself):

| delivery yr | model position | model curve pays | real FCA cleared (pos → $/kW-yr) |
|---|---:|---:|---|
| 2023/24 | 1.2594 | $0 | FCA 14: 1.0451 → $24.01 |
| 2024/25 | 1.1035 | $0 | FCA 15: 1.0406 → $31.33 (Rest-of-Pool) |
| 2025/26 | 1.0051 | **$81.19** | FCA 16: 1.0368 → $31.09 (Rest-of-Pool) |
| 2026/27 | 1.0490 | $15.11 | FCA 17: 1.0351 → $31.08 *(instrument-locked row: label-year ≥ 2026; the auction itself cleared 2023-02)* |
| 2027/28 | 1.0982 | $0 | FCA 18: 1.0329 → $42.96 |

This is the two-sided form of the defect in one table: the model pays **$0 when it is long
and 2.6 × reality when it dips** — the oscillator, not a one-signed under-payment. The
NEISO golden (`ff-t3-neiso-golden/bau`) carries the same oscillation through the horizon:
positions 1.132 (2026) → 1.013–1.031 (2027–29, inside the curve) → 1.061/1.092 (2031–32,
$0 side) and onward.

**Real markets do not oscillate.** The five real FCA positions span 1.033–1.045 over five
years (σ ≈ 0.005); PJM's cleared positions 2021–2025 span 1.004–1.056; MISO's one
measurable committed year is 1.017. The model's positions span 1.005–1.259 (NEISO) and
1.10–1.24 (MISO) over the same windows.

## 3. Where the real markets sat and what they paid (all in-repo)

- **NEISO** — FCAs 14–18 cleared ON the system demand curve (verified exactly by the R2
  re-derivation) at 3.3–4.5 % surplus, $24.0–43.0/kW-yr
  (`data/raw/capacity-market/auction-price/neiso/neiso.csv` + demand-curve rows). The
  charter's premise "real FCAs cleared $24–43/kW-yr [where the curve pays $0 past 8.3 %]"
  carries RC-R's own correction: they cleared at 3.3–4.5 % surplus, **never at ≥ 8 %**, and
  the published curve genuinely pays $0 past 5.8 % — the $0 is a POSITION artifact, not a
  curve artifact (`FINDING-capx-neiso-rc-phase0-2026-08-30.md` §10.1, §10.4(2)).
- **PJM** — BRAs cleared at 1.004–1.056, **inside** every vintage's published zero
  (1.064–1.074): $51.1 (2021/22), $18.3, $12.5, $10.6, then $98.5/kW-yr at 1.005 (2025/26)
  and the cap at 0.99 (2026/27) (`auction-price/pjm/pjm.csv`; positions = cleared MW ÷ the
  vintage curves' own published requirement denominators).
- **MISO** — pre-RBDC PRAs were **vertical-curve auctions**: price = the marginal offer at
  the fixed requirement when long ($1.50–$34.10/MW-day system rows, 2017–2025;
  `data/raw/miso-pra/miso_pra_clearing_prices_2023-2026.csv`), CONE when short (2022-23:
  $236.66/MW-day across most zones — reality was SHORT the year the model sat 1.13–1.24
  long). The IMM's retrospective (FERC 187 FERC ¶ 61,202 at p.5, quoted in the demand-curve
  README): an efficient sloped price would have been ~$100–175/MW-day in 2019/20–2021/22
  against actual < $7 — i.e. the *published design itself* suppressed long-position prices
  ~15–25×, which is what the model's vertical vintage faithfully reproduces, minus the
  marginal-offer floor. PY 2025-26 (first RBDC year): committed 137,559.3 MW vs initial
  PRMR 135,213.4 (**position 1.0174**) clearing $666.50/MW-day summer / $79.07/kW-yr
  annual (`auction-price/miso/miso.csv`; the PRMR pair is the committed S-123 operand
  documentation, `capacity_market.py:2596-2630`).
- **NYISO** — NYCA spot cleared $1.61–4.28/kW-mo ($19.3–51.4/kW-yr) every capability year
  2020-21 … 2025-26 (`auction-price/nyiso/nyiso.csv`, SOM tables) — small, positive, never
  $0, at positions the committed Pass-1 reconstructs as 0.998–1.051.

## 4. Adjudication per ISO — shape, zero-cross, surplus measurement, or real?

**NEISO — position, in two named halves; the curve is exonerated.** Pass 1B (committed,
`results/capacity-price-validation/ff2b-neiso-pass1b.md`, reproduced at HEAD): at the
auctions' own positions the implemented curve pays within −22 %…+24 % of the real clearing
— errors of design-family approximation, not sign. The defect is the position: model
1.26/1.10 in the screen years that shaped the composition, against real 1.045/1.041. Two distinguishable halves, both
already routed by RC-R §10.4(2), sharpened here: (i) **surplus measurement** — the
accreditation basis (claimed-capability ⇒ firm = nameplate for every thermal unit, no
seasonal-claimed-capability haircut, non-FCM participants counted) and the requirement
operands; (ii) **equilibrium quantity** — even a correctly-accredited census fleet is the
QUALIFIED quantity, while the FCA price forms at the CLEARED quantity, where de-list bids
have withdrawn supply up the curve. Reality's position is curve-*endogenous*; the model's
is curve-*exogenous*. Half (ii) is what makes "evaluate the curve at the fleet census" a
category error even with perfect accreditation, and it is the cross-ISO half.

**MISO — three stacked defects, one of them shape.** (i) **Position**, same class as
NEISO: +11.2 pts at the one committed measured year (1.1296 vs 1.0174), with local
shortfalls (LRZ 5/9 at CONE) in years the model reads system-long — candidate causes are
the accreditation basis (the ledger counts the whole EIA-860 operable fleet at 1 − EFORd;
MISO's real supply is offered/cleared SAC from PRA participants) and are MISO's to
adjudicate. Note the pass-2 positions above EXCLUDE the S-2 tie the HEAD ledger now adds —
the position defect at HEAD is ~3 pts LARGER than the table shows. (ii) **Vertical-era
clearing floor** (2021–24 delivery years): the model's vertical step is design-faithful on
the demand side ($0 interior is the published design), but the real auction's price is the
marginal OFFER — $3.4–7.3/kW-yr while long — which the demand-curve-only evaluation cannot
produce. Against gas bars of $21–35/kW-yr this is exactly the D17 §4.2 "small but
structurally non-zero" gap; it is bounded (≲ $7/kW-yr) and vanishes with the design from
PY 2025-26. (iii) **RBDC-era shape + the ONE-POSITION LIMIT**: the cap/zero x-positions
are first-order stand-ins (`capacity_market.py:1006-1008` says so); the committed seasonal
Pass-1 back-solves the four PY 2025-26 seasonal prints to implied model-curve positions
0.9885/1.0291/1.0424/1.0340 — reality's binding-summer concentration needs the four
seasonal positions to differ, which one annual position cannot express (the documented
limit, `capacity_market.py:1036-1056`); and at the measured real position (1.0174) the
model curve pays $52.1/kW-yr flat-across-seasons against the real $79.1 concentrated
78 % in summer. The model needs a SHORT position (0.988) to reproduce a print reality
produced while 1.7 % LONG — the shape is too steep and zeroes too early, in the one ISO
whose shape was never published-parameter-grounded.

**PJM — confirmed in the hindcast window; self-resolving in the published forward design.**
Hindcast (instrument default bundle): model 1.14–1.20 vs published zeroes 1.064–1.074 ⇒
$0 in all four measured screen years, against real $10.6–98.5/kW-yr — and the FFR-2B PJM
compare shows the same downstream signature as MISO (91–92 GW `entry_capped`, a 14.8 GW
one-year exit wave, 6.4 GW reversal). Real positions were inside the curve every year.
Forecast (s6 ledgers): positions 1.029 → 0.964 by 2030 — the SHORT side; no $0. And from
delivery 2028/29 PJM's own published curve carries the ER26-1556 floor: a long position
earns 0.537 × net-CONE ≈ $63.9/kW-yr by design. Adjudication: position defect (hindcast) —
the curve, anchors and zero-crosses are published and reconcile (+0.002 % at 2026/27).
Any cross-ISO repair must preserve the 2028/29+ floor's consequence: for PJM the
$0-at-long object CEASES TO EXIST in the published forward design.

**NYISO — latent; the flip gate is the live object.** The curve reproduces three published
spot outcomes to machine precision at the published positions (committed Pass 1 rows,
errors ~1e-13) — NYISO's spot literally administers price = curve(supplied UCAP), so the
one ISO whose real mechanism IS "evaluate the curve at a census quantity" is the one ISO
whose curve validates exactly. The model's T1-F positions reach the 1.12 zero only at the
forward edge (1.097/1.094/1.091/1.131/1.127, 2026–2030). But the default posture never
consults the curve: NYISO prices the flat legacy $110/kW-yr — 2.2 × its own current
published ARV anchor ($50.55) and 2–6 × every observed spot year — an OVER-payment defect
of the opposite sign. The committed probe pair (`nyiso-2021-2025-fixed` vs `-curve`,
2026-07-18) brackets the stakes: retirements 1.036 GW (fixed, −30 % vs actual) → 3.318 GW
(curve-ON, +123 %). The withheld FF-3D/FF-2C flip is therefore working as intended, and
this finding is direct evidence for that flip decision, not for a curve repair.

## 5. Sign discipline (rule 14 `[R-ACCURATE]`) — where it bites, stated so it cannot be traded

- **MISO:** every repair here (position audit shortening the long position is the
  exception below; the offer floor, the RBDC shape, the seasonal grain) moves capacity
  revenue UP at the positions the screens actually saw, which makes retirements HARDER —
  i.e. D17's headline (non-coal exits 0.0 vs 3.9 GW, total −16.5 %) moves the WRONG way.
  That is not a reason to withhold any of it: each is identified from a published source
  and enters formulaically. Symmetrically, a position-audit repair that SHORTENS the
  model's position moves revenue up too (closer to the curve) — same wrong-way residual
  push. Nothing here may be sized, tuned, or sequenced by what it does to the exit
  residual; if the accurate inputs worsen it, the remaining error is elsewhere (D17 R1's
  re-measure, thread (i-a) energy margins) and stays open on its own evidence.
- **The S-123 exhibit, recorded because it is the pattern in miniature:** the S-123
  requirement correction — unambiguously right under rule 14 — moved MISO's positions
  ~+9 pts FURTHER past the zero-cross (the 2025 screen's entering fleet read ~1.018 on the
  pre-S-123 basis — the annual RBDC paid ≈ $51/kW-yr there, D17 §4.2's "the 2025 screen
  pays" mechanism — where the corrected basis reads the same fleet ~1.11 → $0). An
  accurate requirement made the
  capacity-revenue $0 MORE prevalent. Requirement accuracy and revenue accuracy are
  separate questions; fixing one exposed the other. This finding is that exposure,
  characterized.
- **NEISO:** the position/clearing repair direction is NOT one-signed: it removes revenue
  in dip years (model $81 vs real $31 at 2025/26) and adds it in long years ($0 vs
  $24–43). Its honest description is "kills the oscillator", not "more capacity revenue" —
  and RC-R already recorded that the reachable-basis exit level is +24 % OVER, so the
  naive "more revenue helps the residual" reading is wrong there in BOTH directions.
  Neither reading may drive the repair.
- **NYISO:** arming the accurate curve at the current position basis makes retirements
  much WORSE (+123 % probe). That is the discovered-bug signal working: the position
  basis must be right BEFORE the accurate curve can be armed, which is precisely the
  standing flip-gate logic.

## 6. What each repair is identified FROM (never the residual)

Per ISO, per rule 25 — one defect class does not license one shared parameterization.

1. **MISO position audit** — identified from MISO's own PRA supply accounting: the PRA
   Results Posting p.22 "Summer Supply Offered and Cleared Comparison Trend" category rows
   (Generation / External / BTMG / DR / EE, already the S-123 operand source) vs the
   zonal-results System committed row and Initial PRMR (p.18) — offered-and-cleared SAC by
   category, per planning year. The 2023/2024/2025 PY postings' URLs are recorded in-repo;
   `misoenergy.org` is 403-blocked to this environment, so completing the per-year series
   is an intake decision for the owner (the Q23 "no more data" ruling was FC-5-scoped, but
   its posture suggests presenting this as the tightly-scoped ask it is: ~5 numbers × 3
   postings, one source, already the anchor-vintage document class).
2. **MISO RBDC shape** — identified from the published RBDC construction: the ER23-2977
   filing / 187 FERC ¶ 61,202, the RAN BPM-011 curve definition, or the PRA posting's RBDC
   chart (noted "403-blocked" at the PY2026-27 vintage attempt, `capacity_market.py:1759`).
   Until intaken, the honest state is what the code already documents: first-order
   x-positions, reconciliation test asserting only the anchor and cap fraction. The
   committed measured point (1.0174 → $666.50 summer) is a VALIDATION point for any future
   shape, never a fit target for the current one.
3. **MISO vertical-era offer floor** — identified from the in-repo PRA clearing record
   itself (`miso-pra` CSV): a hindcast-window market-design input of the same class as the
   vintage curves (the design's price-when-long WAS the marginal offer; it regenerates for
   vertical-era years only and is superseded by the RBDC forward). Whether to represent it
   at all is a rule-13 adjudication for the repair lane — it is bounded ≲ $7/kW-yr and may
   not be worth a mechanism; this lane only names the source.
4. **NEISO position** — two identifications, both named by RC-R §10.4(2) and both with
   in-repo starting material: the accreditation basis (Seasonal Claimed Capability /
   Qualified Capacity vs nameplate — `data/raw/capacity-market/accreditation-filings/neiso/`
   exists), and the cleared-vs-qualified quantity gap (each FCA's published qualified,
   cleared and de-list MW — the FCA results class the R2 intake already draws on).
5. **The cross-ISO clearing half (supply side of the capacity auction)** — if the director
   charters it as a mechanism question, its identification is each ISO's published
   offered/qualified-vs-cleared quantities (PJM BRA Table 2/7 offered & cleared UCAP —
   in-repo rows carry cleared; ISO-NE FCA qualified/de-list; MISO p.22 offered=cleared
   category rows; NYISO supplied-vs-requirement in the SOM tables). Parameters would still
   be per-ISO (rule 25); what is shared is only the question "at what quantity is the curve
   evaluated".
6. **PJM** — no curve repair identified or needed; the position audit folds into any PJM
   capacity lane (same PRA-analogue sources: BRA reports, in-repo). The 2028/29 floor is
   already implemented and is the forward boundary condition any cross-ISO change must
   leave intact.
7. **NYISO** — the object is the FF-3D/FF-2C flip decision plus one anchor reconciliation:
   the flat 110.0 legacy anchor vs the published ARV series already in-repo
   (`demand-curve/nyiso/nyiso.csv`; the 2026-27 vintage note says the fixed anchor is what
   the shipped posture actually pays). Identified from the DCR parameter series; decided at
   the flip gate, not in a curve lane.
8. **Doc-sync (cheap, code-docstring only):** the two stale docstrings in §1, routed to
   any next session that touches `capacity_market.py` under its normal model assignment.

## 7. The four-ISO census (charter item 4)

| ISO | signature "$0 where the model sits" | where | real floor in-repo | verdict |
|---|---|---|---|---|
| MISO | YES — every committed screen year 2021-2025 and forecast through 2028 | hindcast + forward, default posture | $0.55–7.3/kW-yr (vertical-era long years); $79.1 (PY25-26) | **CONFIRMED** (+ shape defect, MISO-only) |
| NEISO | YES — 3 of 5 crossover years; golden oscillates across the zero through 2050 | hindcast + forward, default posture | $24.0–43.0/kW-yr | **CONFIRMED** (position; curve exonerated) |
| PJM | YES in hindcast (4/4 measured years); NO forward (short side; 2028/29+ published floor pays $63.9 at long by design) | hindcast only | $10.6–98.5/kW-yr | **CONFIRMED-HINDCAST / self-resolving forward** |
| NYISO | Curve never consulted at default (flat $110 — over-pays 2–6×); curve-ON probe shows the signature would arm at +123 % retirements | latent (probe arms only) | $19.3–51.4/kW-yr | **LATENT** — flip-gate evidence, not a curve defect |

## 8. Routed recommendation (for the director — no repair lands in this lane)

- **R1 — MISO capacity-revenue repair lane** (position audit §6.1 + the RBDC-shape intake
  decision §6.2 + the one-position limit; the vertical-era floor §6.3 carried as an
  adjudication item, not a commitment). **Sequence AFTER D27** — D27 re-measures the MISO
  T1-H leg at HEAD and will refresh both the residual context and the hindcast positions
  this lane would arm against; same surfaces, hard collision. The Q23 posture on any
  intake ask applies (§6.1).
- **R2 — NEISO position lane** (RC-R §10.4(2) executed: accreditation basis + cleared-vs-
  qualified). No collision with D26 (FC-6 instrument) or the golden-re-solve card, but the
  golden card's decision would be informed by this lane's outcome — flag on its sitting.
- **R3 — the cross-ISO clearing-half question** (§6.5) is a single mechanism-class charter
  the director may open ONCE (it is the D17 §5 "shared shape" question, now with the
  mechanism named: the curve is evaluated at a census quantity where every real market
  clears supply against the curve); per-ISO parameters and verdicts stay separate. D6
  (FC-3 curve-ON over-fire, HELD behind D27+D28) is most plausibly THIS object wearing an
  FC-3 gate label — this finding is chartering input for D6, and D6 should not be scoped
  as a curve-shape hunt.
- **R4 — NYISO**: no lane; attach §4's probe-pair evidence to the standing FF-3D/FF-2C
  flip-gate record and the anchor reconciliation (§6.7) to whichever session next holds
  the NYISO capacity surface.
- **PJM**: no dedicated lane; position audit folds into the next PJM capacity session;
  the 2028/29 floor is a boundary condition on R3.

## 9. Governance attestation

**ZERO solves.** The two instrument invocations are `validate_capacity_prices.py` at HEAD
on committed ledgers + committed raw rows (comparison-only by its own charter; output
committed as the §0 evidence extract with bundle provenance and the conservative-basis
caveats inside). No LP, no bench, no re-score, no registration; rule 15 does not fire (no
run produced). No out-of-training year touched: ledgers read are committed 2021–2025
hindcast/crossover and 2026+ forecast artifacts; auction records are raw published data;
the one instrument row labeled 2026 is reported with its lock flag, excluded from every
verdict here as there. Docs only: the only files this lane adds are this finding and its
evidence JSON — no `src/`, no matrix shard, no board/verdict/keeper/marker file (rule 28
not triggered; the stale-docstring items are ROUTED, §6.8, not edited). Rule 25 held: four
per-ISO adjudications, four per-ISO identification sources, no verdict or parameter
transferred. Rule 14 discipline written into §5 where it bites, both directions. D27
collision re-checked at push (not landed); the D17/FFR-2B record is cited as current.
