# FINDING — capx D75: the PJM VRE accreditation vintage — the card is REAL and its repair is fully identified from published data, but the ratings on disk for DY 2024/25 are SUPERSEDED, the scope is one year too narrow, and the one operand the charter fenced does not exist in PJM's published record

**Lane:** capx D75, executing `FINDING-capx-d66-2026-09-06.md` §8 card B. Branch
`claude/capx-d75-pjm-vre-elcc-x1lilr`, fresh off `origin/main` **2fa2f23a**.
**ZERO LP — no solve of any kind was run.** **NOTHING BUILT, NOTHING ARMED**: no `ScenarioConfig`
field, no registry vintage axis, no default, no cache-key change, no matrix cell, no registration,
no bundle (§7). Instrument: `docs/handoffs/d75/vre-elcc-vintage-phase0-2026-09-06.{py,json}`;
ex-ante record: `PRECOMMIT-capx-d75-pjm-vre-elcc-vintage-2026-09-06.md` (pushed `1cd1fc95`,
corrected `715eb278` — §1.4). **DATA PROFILE: pjm.**

---

## 0. The answer in one paragraph

Card B's object is real, its direction is confirmed, and its repair is fully identified from
published PJM data — but it cannot be built as chartered. **The measurement first:** correcting
PJM's VRE accreditation to each delivery year's own published ratings moves the model's accredited
VRE **DOWN in every in-scope year, at every candidate solar mix** — 2023/24 **−754.6**, 2024/25
**−332.9**, 2025/26 **−148.3 MW** at PJM's own published mix, window total **−1,235.8 MW** — and
the position residual **widens** in 2024/25 and 2025/26, exactly as card B pre-declared (§3, §4).
Rule 14's point stands. **What does not survive is the magnitude and the scope**, for three reasons,
each a primary-document fact. **(1)** The DY 2024/25 ratings the charter names — wind 0.16, solar
0.36/0.54 — are PJM's **December 2021 preliminary** set. The 2024/25 BRA was delayed and re-executed
(FERC ER23-729), PJM re-ran the study, and the December 2023 ELCC Report states in terms that *"only
the 2024/2025 values are final"*: **wind 0.21, solar 0.33 fixed / 0.50 tracking** (§1.1). Those are
the ratings that auction cleared on, and they **halve the effect** (−664.0 → −332.9 MW at PJM's
mix), which is the whole reason the chartered 0.6–1.4 GW band is missed. **(2)** PJM's ELCC regime
began with the **2023/2024** BRA, not 2024/25 — ratings posted 2021-12-16 — so the scope limit is one
year too narrow, and the excluded year turns out to have the **largest** footprint of the three and
to land squarely inside the pre-declared band at every mix (§1.2). **(3)** DY 2025/26 is not already
correct either: it is a marginal-ELCC year with its **own** published ratings (38/10/14) that differ
from the wired 2026/27 set (41/8/11), so a vintage axis stopping at the reform boundary leaves a
fourth gap open (§5). Finally the one new operand the charter fenced — the fixed-tilt / tracking MW
split — is **not obtainable**: PJM publishes no installed-MW-by-class pairing for any pre-reform
vintage, in any of seven primary documents (§2). The chartered STOP fires. §8 states the one ruling
needed and what a successor lane can build without it.

**One claim this lane made and withdrew before any solve or build** is recorded at §1.4 rather than
quietly dropped: the first push asserted D66's accreditation pools were wrong. They are not.

---

## 1. Corrections to the charter's premises, from the primary record

Every document below was fetched in-session, its sha256 recorded, and its text read. None is in the
repository today except where noted.

### 1.1 The DY 2024/25 ratings on disk are SUPERSEDED — and this is the whole magnitude story

`data/raw/capacity-market/elcc/pjm/pjm.csv` carries a 2024/25 tranche labelled *"2024/2025 BRA (Dec
2021 ELCC Report, predecessor/narrower methodology)"*. That set was PJM's final rating for the
2024/25 BRA **as then scheduled**. The auction was delayed and re-executed — the repo's own
`demand-curve/pjm/README.md` records the compressed 17-month schedule and FERC Docket ER23-729-002 —
and PJM re-ran the ELCC study. **December 2023 ELCC Report, Introduction, p.1, verbatim:**

> *"For the December 2023 ELCC Report, ELCC Class Ratings are calculated for each delivery year in
> the period 2024/2025 – 2033/2034 but only the 2024/2025 values are final (the results for the rest
> of the delivery years are preliminary)."*

| class | Dec-2021 (in repo; what the charter quotes) | **Dec-2023 — FINAL for DY 2024/25** |
|---|---:|---:|
| Onshore Wind | 16 % | **21 %** |
| Offshore Wind | 37 % | **47 %** |
| Solar Fixed Panel | 36 % | **33 %** |
| Solar Tracking Panel | 54 % | **50 %** |
| 4-hr Storage | 82 % | 92 % |
| Hydro Intermittent | 46 % | 36 % |

Wiring the Dec-2021 set would put a superseded number on the accreditation path — rule 14
`[R-ACCURATE]` forbids that as squarely as it forbids an estimate. The repo's 2024/25 tranche needs
**re-intaking as two vintages**, not replacing: the Dec-2021 set is a real published artifact and
should be kept, labelled preliminary/superseded.

### 1.2 PJM's ELCC regime began with the 2023/2024 BRA, and that year has the largest footprint

The charter's scope limit reads *"PJM's ELCC regime BEGAN with the 2024/25 BRA; 2022/23 and 2023/24
sit in a pre-ELCC regime this repo has not intaken."* Half of that is wrong. PJM posted
`elcc-class-ratings-for-2023-2024-bra.pdf` on **2021-12-16** — Onshore Wind **15 %**, Solar Fixed
**38 %**, Solar Tracking **54 %** — and the December 2021 report's own Table 3 is titled
*"Comparison of ELCC Class Ratings, 2024/2025 BRA vs 2023/2024 BRA"*. **DY 2023/24 is in scope**, its
delta is the largest of the three (§3), and it is the one year that lands inside the chartered band
at every mix. Only 2022/23 and earlier are genuinely pre-ELCC, and those stay out of scope exactly
as chartered.

The charter's supporting evidence for the break — *"wind offered 2,595 → 1,608 → 1,396 UCAP on a
growing fleet"* — is unaffected and still reads as a regime break; it simply straddles the
**2022/23 → 2023/24** boundary (pre-ELCC → ELCC) rather than the 2023/24 → 2024/25 one.

### 1.3 Document identities

| document | pages | sha256 |
|---|---:|---|
| `elcc-report-december-2021.ashx` | 15 | `1305626c975de30d5787482cf24b7f170f2aff7b03eeb1120e86f6fdb9610c84` |
| `elcc-class-ratings-for-2023-2024-bra.pdf` (posted 2021-12-16) | 1 | `c50890fb525dd0eb98eae29df68cabdd13c8bd390379c5028135e953745f2f69` |
| `elcc-report-december-2022.pdf` | 15 | `f01eab0e77d4136710dbefeeb0f32eaa00ea84ef26e87bf435c402c23eb787ac` |
| `elcc-report-december-2023.pdf` | 16 | `192ea596b8f3ff1c7b55e0c7eb916d6629ed54a462bf5bee5ea9a152f53ea1f9` |
| `elcc-class-ratings-for-2024-2025.pdf` (posted 2023-12-29) | 1 | `f3fb54dbe98d19e1e2b0181c7da5dca798b836f0f4c4e6d0865c56a8589fc994` |
| `2025-26-3ia-elcc-class-ratings.pdf` (posted 2025-03-12) | 1 | fetched in-session (§5) |
| `2026-27-bra-elcc-class-ratings.pdf` | 1 | already sourced in `elcc/pjm/pjm.csv` |

### 1.4 One claim this lane made and WITHDREW, recorded rather than dropped

The first push of the PRECOMMIT (`1cd1fc95`) carried a third correction: that D66 §4.5's
accreditation pools were the 2021 base year's, frozen by an instrument bug, and that DY 2024/25's
pools are model year 2024's ledger values. **That was wrong on both halves and was withdrawn in
`715eb278`, before any solve or build.** D66's instrument does roll its pools forward
(`supply-census-2026-09-06.py` L182–L185, immediately after the `pinned` dict this lane had stopped
reading), and — decisively — the census is accredited on `prior_results`, not on the current year's
ledger: `runner.py` L2037–2039 / L2116–2124 pass `prior_results["wind_cap_mw"]` /
`["solar_cap_mw"]` with `accreditation_year=year`, and `retirements.py` L3567 threads those same
pools into `_settle_capacity_supply_clearing` → `accredited_firm_capacity_mw`. So

> delivery year Y/Y+1 ⟸ model year Y ⟸ the pools recorded in `evolution_{Y-1}`

and D66's roll-forward reconstructs exactly that. The rebuilt instrument reproduces D66's pinned
rows to **0.021 MW** — DY 2024/25 4,163.099 / 484.099 against its 4,163.1 / 484.1; DY 2025/26
4,778.099 / 743.779 against its 4,778.1 / 743.8 — carried as `instrument_check` in the phase-0 JSON,
the charter's own step-1 discipline. **D66 §3.2/§3.3/§4.5 need no correction on this point and none
is proposed.** §1.1 and §1.2 are unaffected: both are facts about which ratings PJM published for
which delivery year, independent of the pools.

---

## 2. The one new operand — **NOT OBTAINABLE.** The chartered STOP fires

The model carries one `solar` class; PJM rates two (Solar Fixed Panel / Solar Tracking Panel).
Blending them needs a fixed-tilt / tracking **MW split**. The charter: *"comes from PJM's own Table 5
mix, source doc + page, NEVER chosen; if the table is not in-repo, intake it additively and STOP
rather than estimate (rule 14)."*

**PJM publishes no such split for any pre-reform vintage.** Seven primary documents, read:

| document | what it publishes | MW by class? |
|---|---|---|
| Dec-2021 ELCC Report | Tables 1–3 — assumptions, 2024/25 ratings, a 2023/24-vs-2024/25 comparison | **no** |
| Dec-2022 ELCC Report | Tables 1–4 — ratings for 2023/24 3IA, 2025/26 and 2026/27 BRA + a 2023–2032 preliminary series | **no** |
| Dec-2023 ELCC Report | Tables 1–4 — FINAL 2024/25 ratings + a 2024–2033 preliminary series | **no** |
| `elcc-class-ratings-for-2023-2024-bra.pdf`, `-for-2024-2025.pdf` | the rating table alone (1 page each) | **no** |
| 2024/2025 BRA Report | offered / cleared UCAP by resource type — **"Solar" is ONE type** | **no** |
| 2025 PJM ELCC/RRS Table 5, pp.16–17 | installed MW paired with ratings — **2026/27 and 2027/28 ONLY** | yes, wrong vintage |
| 2022 / 2023 / 2024 ELCC/RRS | — | **do not exist**; every URL pattern soft-404s and PJM's ELCC page lists no RRS before the 2025 study |

So there is **nothing to intake**: the operand is not in the repository *and not published*. No
additive intake resolves it, and estimating it is what rule 14 forbids.

**The bracket instead of a number.** Every delta below is reported over five candidate mixes, **none
adopted**: PJM's two published Table-5 mixes (12.01 % / 11.40 % fixed — post-reform vintages, the
only pairings PJM publishes at all), an explicitly-labelled EIA-860 footprint proxy (22.81 % fixed,
PJM-member states, all vintages — a *sanity check on the bracket*, not a candidate operand, since six
of those states are only partly in PJM), and both arithmetic bounds.

---

## 3. Phase 0 — the measurement

Zero LP. Pools are `evolution_{Y-1}`'s, per §1.4; PJM's persistent fleet carries no wind or solar
units and PJM has no internal-supply accounting ratio, so Δ accredited VRE flows 1:1 into `census_mw`.

| DY | model yr | regime | wind pool | solar pool | published W / F / T | **Δ net, full bracket** | **Δ @ PJM Table-5 mix** |
|---|---:|---|---:|---:|---|---:|---:|
| 2022/23 | 2022 | pre-ELCC | 10,153.9 | 4,549.8 | — | — | out of scope |
| **2023/24** | 2023 | class-avg | 10,153.9 | 4,549.8 | 15 / 38 / 54 % | −1,395.2 … −667.2 | **−754.6** |
| **2024/25** | 2024 | class-avg | 10,153.9 | 4,549.8 | **21 / 33 / 50 %** | −1,013.4 … −240.0 | **−332.9** |
| **2025/26** | 2025 | marginal | 11,653.9 | 6,990.4 | 38 / 10 / 14 % | −394.4 … −114.7 | **−148.3** |
| | | | | | **window total** | −2,803.0 … −1,021.9 | **−1,235.8** |

*(DY 2023/24's pools are D66's roll-forward — `evolution_2022` emits the screen and clearing blocks
but not the adequacy block, so its recorded pools do not exist. That year's `renewable_additions` is
empty, so the reconstruction is the 2021 base pool exactly; the gap in the ledger is routed at §6.)*

**The pre-declared SIGN HOLDS, unconditionally.** DOWN in every year at every candidate mix, and DY
2024/25's sign is not mix-contingent at all: the break-even blend is **0.5527**, above PJM's own
tracking rating of 0.50, so the implied fixed share is **negative (−0.310)** — outside the admissible
range entirely. No choice of the blocked operand can flip it.

**The pre-declared MAGNITUDE band (DOWN 0.6–1.4 GW) is missed on DY 2024/25**, and the cause is
§1.1 alone — the pools are not in dispute:

| basis (DY 2024/25, same pools, PJM's 2026/27 Table-5 mix) | Δ net MW |
|---|---:|
| D66 §4.5 / the charter — **superseded** Dec-2021 ratings | **−664.0** |
| PJM's **operative** Dec-2023 ratings | **−332.9** |
| *rating-vintage leg* | *+331.2* |

The charter's basis reproduces D66 §4.5's bracket to the MW — **−1,384.6 … −565.7** against its
published *"−1,384.7 to −565.7"* — which is the check that this is their arithmetic and not a straw
man. **The operative ratings halve the effect.** The year the band actually fits is **DY 2023/24**:
in scope per §1.2, largest footprint of the three, and inside 0.6–1.4 GW at *every* mix.

---

## 4. The position at full magnitude, in both of D66 §1.2's frames

Frame B is the like-for-like whole-RTO comparator (published cleared RPM + committed FRR over PJM's
RTO Reliability Requirement); Frame A is D57/D61's RPM-only comparator (cleared RPM over
`RelReq adj FRR + EE add-back`). Both requirement operands are re-read from the in-repo
`demand-curve/pjm/pjm.csv` rather than taken on trust. Gap convention is D66's: **published −
model**. Model column is incumbent → vintaged at PJM's 2026/27 Table-5 mix.

| DY | pub pos B | pub pos A | model pos | **gap B, pt** | **gap A, pt** | |
|---|---:|---:|---|---:|---:|---|
| 2023/24 | 1.05172 | 1.05520 | 1.08814 → **1.08345** | −3.642 → **−3.174** | −3.293 → **−2.825** | **narrows** |
| 2024/25 | 1.05395 | 1.05551 | 1.03206 → **1.03007** | +2.188 → **+2.388** | +2.345 → **+2.544** | **widens** |
| 2025/26 | 1.00992 | 1.00489 | 0.96613 → **0.96513** | +4.379 → **+4.479** | +3.877 → **+3.976** | **widens** |
| | | | **Σ\|gap\|** | 10.209 → **10.041** | 9.515 → **9.345** | |

The incumbent column reproduces D66 §1.4's gaps (−3.64 / +2.19 / +4.38 pt) exactly.

**Card B's pre-declaration holds where it matters.** The residual widens in 2024/25 and 2025/26 —
the two years the card is about, where the model's position sits *below* PJM's published. It narrows
in 2023/24, where the model sits *above*, so the census falling moves it toward the published
position; that is a sign of the mechanism being two-sided, not of it being wrong. Σ|gap| across the
window falls slightly (10.209 → 10.041 Frame B), because 2023/24's improvement is the largest single
move.

**None of this is a reason to arm or not arm anything** (rule 1 `[R-STRUCT]`). The reason to prefer
the vintaged ratings is rule 14: they are the ISO's own published accreditation for the delivery
year each auction cleared on. Had the residual moved the other way the recommendation in §8 would be
identical.

---

## 5. A fourth vintage gap the card as chartered would leave open: DY 2025/26

The charter fixes *"DY ≥ 2025/26 reads the marginal-ELCC ratings already wired."* The reform boundary
is right — PJM's `2025-26-3ia-elcc-class-ratings.pdf` (p.1) gives *"the Final ELCC Class Ratings for
the 2025/2026 Delivery Year"* and rates the thermal classes too (Nuclear 95 %, Coal 83 %, Gas CC
78 %), confirming D48's `THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] = "2025/2026"`. But
the **values** differ from the wired 2026/27 set:

| class | DY 2025/26 published | wired (2026/27) |
|---|---:|---:|
| Onshore Wind | 38 % | 41 % |
| Fixed-Tilt Solar | 10 % | 8 % |
| Tracking Solar | 14 % | 11 % |

The model's DY 2025/26 pools clamp to the wired endpoints (wind 11,653.9 ≥ 3,956 MW → 0.41; solar
6,990.4 ≤ 9,902 MW → 0.1064), so the year is accredited at the wrong vintage by −115 … −394 MW.
Small, but it is the same defect, and a vintage axis that stops at the reform boundary does not close
it.

**One open item, deliberately not resolved here:** this is the **3IA** rating set (posted
2025-03-12), PJM's final for the delivery year. The 2025/26 **BRA** (held July 2024) cleared on the
ratings current then, and the 2025/26 BRA Report's own tables are images that do not extract (D66
§1.2 records the same obstacle). A successor lane must fix which vintage a hindcast screen should
read — the auction the census is compared against (BRA) or the delivery year's final (3IA) —
**before** it wires the year, and state it in its PRECOMMIT. The same question arises for DY 2024/25
and is answered there by the Dec-2023 report's explicit "final" language plus that auction's own
delay.

---

## 6. What this lane routes rather than absorbs

1. **The repo's PJM ELCC intake needs four vintages where it has two.** Relabel the Dec-2021 tranche
   *preliminary / superseded*, add the Dec-2023 FINAL 2024/25 set (§1.1), the 2023/24 set (§1.2) and
   the 2025/26 3IA set (§5). Additive `data-intake` work on
   `data/raw/capacity-market/elcc/pjm/pjm.csv` with source doc + page per row — no code, no gate. It
   is a **prerequisite for any build**: today the repository's only 2024/25 rating set is the
   superseded one.
2. **The blocked operand** (§2) — the only item needing a ruling rather than work.
3. **`evolution_2022.json` emits the screen and clearing blocks but not the adequacy block**
   (`wind_cap_mw` / `solar_cap_mw` / `renewable_credit_applied` / `storage_firm_mw` absent), while
   2021 and 2023–2025 carry it. It forced a reconstruction for DY 2023/24 here (§3) and the same gap
   would bite any lane measuring that year. Unexplained; worth one look by a lane that owns the
   ledger.

---

## 7. Matrix, records, collision

* **Matrix (rule 28 `[R-MECH-MATRIX]`): NO CELL WRITTEN.** No mechanism was tested — no field, no
  gate, no solve. The cell this card would create does not exist yet and is created by the PR that
  adds the field (duty (c)), not by this one.
* **Registration (rule 15 `[R-DASHBOARD]`): nothing to register.** No bundle was produced, so rule 29
  clause (c)'s delete-before-merge is vacuous here.
* **Holdout (rule 22 `[R-HOLDOUT]`): untouched.** No solve, no scoring, no registration of any year.
* **Collision:** none taken. D67 owns the requirement seam (`resolve_adequacy_requirement_mw`) and
  D74 the bar/offer seam; this card's seam is `resolve_renewable_capacity_credit` +
  `RENEWABLE_ELCC_CURVES_BY_ISO`, and neither was edited.
* **G-DRIFT:** LIVE, per the charter and `FINDING-capx-d67-2026-09-06.md` §2.2
  (`DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` 0.036 → 0.064645). Form 4 is void; a screen would have
  had to buy its own control at HEAD. Not re-litigated. The arm-A ledgers remain valid as a *read* of
  what the model accredited, which is all §3 uses them for.

---

## 8. Recommendation

**Card B should be re-chartered, not abandoned.** The object is real, the direction is confirmed at
every candidate mix, and the repair is fully identified from published PJM data. In descending order:

**(a) RULE NEEDED — the fixed/tracking split.** PJM does not publish it for any pre-reform vintage
(§2), so the chartered "intake it additively" route does not exist. Three ways out; this lane takes
none of them:

  1. **Carry PJM's own published Table-5 mix** (12.01 % fixed) as a documented cross-vintage
     reconciliation under rule 14's misalignment exception — a published PJM number on the wrong
     vintage, stated as such. Cheapest, one line of provenance.
  2. **Derive the split from the model's own solar fleet** via EIA-860's `Fixed Tilt?` /
     `Single-Axis Tracking?` fields. The only route that regenerates forward and responds to modelled
     build (rule 13's test), and the only one with real cost: PJM-footprint attribution plus a
     mapping from EIA technology codes to PJM's ELCC classes, which is a reconciliation, not an
     identity. A `data-intake` card in its own right.
  3. **Accept the bracket.** §3 shows the *conclusion* is mix-insensitive: the sign is DOWN in every
     year at every mix and DY 2024/25's break-even fixed share is **negative**, so no admissible mix
     flips it. A gate could ship on PJM's published mix with the bracket recorded as its sensitivity.

  **Recommended: (1) now, (2) as a separate card if the director wants the forward-regenerating
  form.** (3) is the honest fallback and is already measured.

**(b) The intake first, whatever is ruled on (a)** — §6 item 1. Additive, no code, no gate, and a
hard prerequisite: the only 2024/25 rating set in the repository today is the superseded one.

**(c) The successor card's scope should be THREE delivery years, not one.** 2023/24 (largest
footprint, −667 … −1,395 MW), 2024/25 (−240 … −1,013), 2025/26 (−115 … −394, the vintage-within-the-
reform gap of §5), with 2022/23 and earlier genuinely out of scope. Its pre-declared signs are in
PRECOMMIT §6, recorded before any lane measures against them.

**(d) Its phase-0 gate should be per year, and on the sign, not the magnitude.** The window-wide
band this lane inherited was derived from a superseded rating set and would have killed a correct
arm on a number that halved for a reason having nothing to do with the mechanism. The sign is the
robust pre-declaration — it survives the entire admissible operand range — and the per-year table of
§3 is what this lane leaves behind in the band's place.

**Not chartered, by name:** any solar credit, wind derate or blend weight sized to the position
residual; and any use of PJM's own cleared solar UCAP to back out the model's blend — that would be
deriving an input from the outcome the census is compared against, which rule 13 forbids however it
is motivated.
