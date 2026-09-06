# FINDING — capx D75: the PJM VRE accreditation vintage — the card is REAL, its data is published, and every number the charter pre-declared is wrong, because D66 §4.5 read the 2021 base-year pools and a SUPERSEDED rating set

**Lane:** capx D75, executing `FINDING-capx-d66-2026-09-06.md` §8 card B. Branch
`claude/capx-d75-pjm-vre-elcc-x1lilr`, fresh off `origin/main` **2fa2f23a**.
**ZERO LP — no solve of any kind was run, and none was authorized once phase 0 failed its gate.**
**NOTHING BUILT, NOTHING ARMED**: no `ScenarioConfig` field, no registry vintage axis, no default,
no cache-key change, no matrix cell, no registration, no bundle (§7). Instrument:
`docs/handoffs/d75/vre-elcc-vintage-phase0-2026-09-06.{py,json}`; ex-ante record:
`PRECOMMIT-capx-d75-pjm-vre-elcc-vintage-2026-09-06.md`, pushed before this document.
**DATA PROFILE: pjm.**

---

## 0. The answer in one paragraph

Card B's object is real and its repair is fully identified from published data: PJM's VRE ELCC
ratings **do** break by delivery year and the model **does** apply one vintage to all of them. But
the card cannot be built as chartered, for three reasons, each a primary-document fact rather than a
modelling judgement. **(1)** The DY 2024/25 ratings the charter names — wind 0.16, solar 0.36/0.54 —
are PJM's **December 2021 preliminary** set. The 2024/25 BRA was re-executed (FERC ER23-729), PJM
re-ran the study, and the December 2023 ELCC Report states in terms that *"only the 2024/2025 values
are final"*: **wind 0.21, solar 0.33 fixed / 0.50 tracking** (§1.1). **(2)** PJM's ELCC regime began
with the **2023/2024** BRA, not 2024/25 — those ratings were posted 2021-12-16 — so the scope limit
is one year too narrow and only 2022/23 and earlier are genuinely pre-ELCC (§1.2). **(3)** D66 §4.5
attributes pools of 10,153.9 / 4,549.8 MW to DY 2024/25; those are the **2021 base-year** pools, held
frozen by an instrument bug, and the model's own resolver puts DY 2024/25 at model year 2024, pools
**11,653.9 / 6,990.4 MW** (§1.3). Correct all three and the phase-0 measurement inverts: DY 2024/25's
accredited VRE moves **UP** +277.9 MW at PJM's own published solar mix (bracket −767.7 … +420.6), so
the pre-declared "DOWN 0.6–1.4 GW" **fails on sign and magnitude** (§3) — and it fails because that
band is the right answer to **DY 2023/24**, which the corrected table still lands at −667 … −1,395 MW.
The UP direction is not the bug the charter anticipated: both classes move **toward** PJM's published
accreditation (wind 3.42× → 1.75× of published; solar 0.18× → 0.79×), and on both of D66 §1.2's
frames the position residual **narrows** in two of three years and narrows in total at every
candidate mix (§4) — reported as a measurement, never as the reason to arm (rule 1). Finally, the
one new operand the charter fenced — the fixed/tracking MW split — is **not obtainable**: PJM
publishes no installed-MW-by-class pairing for any pre-reform vintage, in any of seven primary
documents (§2). The chartered STOP fires. §8 states what the director must rule on, and what a
successor lane can build without further data.

---

## 1. Three corrections to the charter's premises, from the primary record

Every document below was fetched in-session, its sha256 recorded, and its text read. None is in the
repository today except where noted.

### 1.1 The DY 2024/25 ratings the charter names are SUPERSEDED

`data/raw/capacity-market/elcc/pjm/pjm.csv` carries a 2024/25 tranche labelled *"2024/2025 BRA (Dec
2021 ELCC Report, predecessor/narrower methodology)"*. That set was PJM's final rating for the
2024/25 BRA **as then scheduled**. The auction was delayed and re-executed (the repo's own
`demand-curve/pjm/README.md` records the compressed 17-month schedule and FERC Docket
ER23-729-002), and PJM re-ran the ELCC study. **December 2023 ELCC Report, Introduction, p.1,
verbatim:**

> *"For the December 2023 ELCC Report, ELCC Class Ratings are calculated for each delivery year in
> the period 2024/2025 – 2033/2034 but only the 2024/2025 values are final (the results for the rest
> of the delivery years are preliminary)."*

| class | Dec-2021 (in repo, and what the charter quotes) | **Dec-2023 — FINAL for DY 2024/25** |
|---|---:|---:|
| Onshore Wind | 16 % | **21 %** |
| Offshore Wind | 37 % | **47 %** |
| Solar Fixed Panel | 36 % | **33 %** |
| Solar Tracking Panel | 54 % | **50 %** |
| 4-hr Storage | 82 % | 92 % |
| Hydro Intermittent | 46 % | 36 % |

Wiring the Dec-2021 set would put a superseded number on the accreditation path. Rule 14
`[R-ACCURATE]` forbids that as squarely as it forbids an estimate; the repo's 2024/25 tranche needs
re-intaking as **two** vintages, not replacing.

### 1.2 PJM's ELCC regime began with the 2023/2024 BRA

The charter's scope limit reads *"PJM's ELCC regime BEGAN with the 2024/25 BRA; 2022/23 and 2023/24
sit in a pre-ELCC regime this repo has not intaken."* Half of that is wrong. PJM posted
`elcc-class-ratings-for-2023-2024-bra.pdf` on **2021-12-16** — Onshore Wind **15 %**, Solar Fixed
**38 %**, Solar Tracking **54 %** — and the December 2021 report's own Table 3 is titled
*"Comparison of ELCC Class Ratings, 2024/2025 BRA vs 2023/2024 BRA"*. **DY 2023/24 is in scope**, and
it is the year with the largest measured footprint (§3). Only 2022/23 and earlier are pre-ELCC, and
those stay out of scope exactly as chartered.

The charter's supporting evidence for the break — *"wind offered 2,595 → 1,608 → 1,396 UCAP on a
growing fleet"* — is unaffected and still reads as a regime break; it simply straddles the
**2022/23 → 2023/24** boundary (pre-ELCC → ELCC) rather than the 2023/24 → 2024/25 one.

### 1.3 D66 §4.5's pools are the 2021 base year's, held frozen by an instrument bug

The model's own resolver is authoritative: `capacity_deliverability.resolve_delivery_year("PJM", Y)
== f"{Y}/{Y+1}"`, and every D48 call site passes `accreditation_year=year`, the model calendar year.
So **model year 2024 is DY 2024/2025.** D66's own §1.1 and §1.4 use that mapping correctly (its
§1.1 verifies `evolution_2022.json` against the published 2022/23 row; its §1.4 puts census 172,159
at DY 2024/25, which is model year 2024's ledger).

`docs/handoffs/d66/supply-census-2026-09-06.py` L139–L163 then does something its own comment says
it does not:

```python
# ... the pool ENTERING screen year Y is the base year's pool plus every
# addition decided in 2021..Y-1.
base = json.loads((CONTROL / "evolution_2021.json").read_text())
pools = {"wind": base["wind_cap_mw"], "solar": base["solar_cap_mw"]}
...
    "wind":  pools["wind"]  * credits["wind"],     # same value every year
    "solar": pools["solar"] * credits["solar"],
```

`pools` is bound once and never updated, so **every** delivery year's Wind and Solar row is the 2021
base pool, 10,153.9 / 4,549.8 MW. The ledgers already carry the right number per year — the same
`wind_cap`/`solar_cap` arrays feed `accredited_firm_capacity_mw(..., accreditation_year=year)` at
`runner.py` L4694 and the ledger fields at L4796, so a ledger's pools × its own credits **is** the
accredited VRE that year counted.

| model yr | DY | wind pool | solar pool | accredited VRE, incumbent |
|---:|---|---:|---:|---:|
| 2021 | 2021/22 | 10,153.9 | 4,549.8 | 4,647.2 |
| 2023 | 2023/24 | 10,153.9 | 4,549.8 | 4,647.2 |
| 2024 | **2024/25** | **11,653.9** | **6,990.4** | **5,521.9** |
| 2025 | 2025/26 | 11,653.9 | 9,431.0 | 5,781.6 |

**Scope of the defect.** §1.4's four-year table is unaffected (it reads `capacity_clearing`
per year). The affected rows are the **pinned** VRE/storage rows in §3.2/§3.3 and all of §4.5.
Corrected, on each year's own pools (D66's row convention, published cleared − model):

| DY | row | D66 | **corrected** | shift |
|---|---|---:|---:|---:|
| 2024/25 | S9 Wind | −2,767.1 | **−3,382.1** | −615.0 |
| 2024/25 | S2 Solar | +3,747.9 | **+3,488.2** | −259.7 |
| 2024/25 | *supply-leg net* | | | **−874.7** |
| 2025/26 | Wind | −1,545.1 | **−2,160.1** | −615.0 |
| 2025/26 | Solar | +852.9 | **+333.5** | −519.4 |
| 2025/26 | *supply-leg net* | | | **−1,134.4** |

Both shifts are absorbed by S10, the residual bucket — the row D66 §8 card C already names as
unattributable without a `fleet_only` rebuild. **This does not disturb D66's headline** (the
requirement leg at 78 % / 67 % is untouched; it reconciles to zero residual against PJM's own FPR
and never uses these pools), and it is **routed, not patched from here** (§6).

### 1.4 Document identities

| document | pages | sha256 |
|---|---:|---|
| `elcc-report-december-2021.ashx` (Dec-2021 ELCC Report) | 15 | `1305626c975de30d5787482cf24b7f170f2aff7b03eeb1120e86f6fdb9610c84` |
| `elcc-class-ratings-for-2023-2024-bra.pdf` (posted 2021-12-16) | 1 | `c50890fb525dd0eb98eae29df68cabdd13c8bd390379c5028135e953745f2f69` |
| `elcc-report-december-2022.pdf` | 15 | `f01eab0e77d4136710dbefeeb0f32eaa00ea84ef26e87bf435c402c23eb787ac` |
| `elcc-report-december-2023.pdf` | 16 | `192ea596b8f3ff1c7b55e0c7eb916d6629ed54a462bf5bee5ea9a152f53ea1f9` |
| `elcc-class-ratings-for-2024-2025.pdf` (posted 2023-12-29) | 1 | `f3fb54dbe98d19e1e2b0181c7da5dca798b836f0f4c4e6d0865c56a8589fc994` |
| `2025-26-3ia-elcc-class-ratings.pdf` (posted 2025-03-12) | 1 | fetched in-session; see §5 |
| `2026-27-bra-elcc-class-ratings.pdf` | 1 | already sourced in `elcc/pjm/pjm.csv` |

---

## 2. The one new operand — **NOT OBTAINABLE.** The chartered STOP fires

The model carries one `solar` class; PJM rates two (Solar Fixed Panel / Solar Tracking Panel).
Blending them needs a fixed-tilt / tracking **MW split**. The charter: *"comes from PJM's own Table 5
mix, source doc + page, NEVER chosen; if the table is not in-repo, intake it additively and STOP
rather than estimate (rule 14)."*

**PJM publishes no such split for any pre-reform vintage.** Seven primary documents, read:

| document | what it publishes | MW by class? |
|---|---|---|
| Dec-2021 ELCC Report | Tables 1–3 — assumptions, 2024/25 ratings, 2023/24-vs-2024/25 comparison | **no** |
| Dec-2022 ELCC Report | Tables 1–4 — ratings for 2023/24 3IA, 2025/26 and 2026/27 BRA + a 2023–2032 preliminary series | **no** |
| Dec-2023 ELCC Report | Tables 1–4 — FINAL 2024/25 ratings + a 2024–2033 preliminary series | **no** |
| `elcc-class-ratings-for-2023-2024-bra.pdf`, `-for-2024-2025.pdf` | the rating table alone (1 page each) | **no** |
| 2024/2025 BRA Report | offered/cleared UCAP by resource type — **"Solar" is ONE type** | **no** |
| 2025 PJM ELCC/RRS Table 5, pp.16–17 | installed MW paired with ratings — **2026/27 and 2027/28 ONLY** | yes, wrong vintage |
| 2022 / 2023 / 2024 ELCC/RRS | — | **do not exist**; every URL pattern soft-404s and PJM's ELCC page lists no RRS before the 2025 study |

So there is **nothing to intake**: the operand is not in the repository *and not published*. There is
no additive intake that resolves it, and estimating it is what rule 14 forbids.

**The bracket instead of a number.** Every delta in §3–§4 is reported over five candidate mixes,
**none adopted**: PJM's two published Table-5 mixes (12.01 % / 11.40 % fixed — post-reform vintages,
the only pairings PJM publishes at all), an explicitly-labelled EIA-860 footprint proxy (22.81 %
fixed, PJM-member states, all vintages — a *sanity check on the bracket*, not a candidate operand,
since six of those states are only partly in PJM), and both arithmetic bounds.

---

## 3. Phase 0 — the measurement, and the pre-declared gate

Zero LP, from the D57 arm-A committed ledgers. PJM's persistent fleet carries no wind or solar
units and PJM has no internal-supply accounting ratio, so Δ accredited VRE flows 1:1 into `census_mw`.

| model yr | DY | regime | wind pool | solar pool | published W / F / T | **Δ net, full bracket** | **Δ @ PJM Table-5 mix** |
|---:|---|---|---:|---:|---|---:|---:|
| 2021 | 2021/22 | pre-ELCC | 10,153.9 | 4,549.8 | — | — | out of scope |
| 2022 | 2022/23 | pre-ELCC | *ledger omits the pool fields* | | — | — | out of scope |
| 2023 | **2023/24** | class-avg | 10,153.9 | 4,549.8 | 15 / 38 / 54 % | −1,395.2 … −667.2 | **−754.6** |
| 2024 | **2024/25** | class-avg | 11,653.9 | 6,990.4 | 21 / 33 / 50 % | −767.7 … **+420.6** | **+277.9** |
| 2025 | **2025/26** | marginal | 11,653.9 | 9,431.0 | 38 / 10 / 14 % | −410.0 … −32.7 | **−78.0** |
| | | | | | **window total** | −2,572.9 … −279.3 | **−554.7** |

**The chartered gate — "the delta must land inside the pre-declared band (DOWN 0.6–1.4 GW) before any
solve" — FAILS on DY 2024/25, on both legs.** Measured −767.7 … +420.6 MW; not DOWN at any
PJM-published mix. **Under the charter that is where the card stops, and it does.**

**Why the pre-declaration read as it did, decomposed exactly** (at PJM's 2026/27 Table-5 mix; the
instrument reports all five):

| basis | Δ net MW | leg |
|---|---:|---:|
| D66 §4.5 / the charter — 2021 base pools + Dec-2021 ratings | **−664.0** | — |
| + DY 2024/25's own pools (§1.3) | −33.5 | **+630.5** |
| + PJM's operative Dec-2023 ratings (§1.1) | **+277.9** | **+311.5** |

The charter's basis reproduces D66 §4.5's bracket to the MW — **−1,384.6 … −565.7** against its
published *"−1,384.7 to −565.7"* — which is the check that this is their arithmetic and not a straw
man. Both corrections push the same way and the **pool-year leg is the larger**. The band is not bad
arithmetic; it is the right answer to **DY 2023/24**, and the corrected table still lands that year
at −667 … −1,395 MW, DOWN at every mix.

### 3.1 The charter's bug-test, applied honestly

The charter says *"a lane that finds the census moving UP has a bug, not a result."* The strongest
available test of that is whether each class moves toward or away from PJM's own published
accreditation. On DY 2024/25, against PJM's cleared UCAP (2024/25 BRA Report Table 9, p.14):

| class | model, incumbent | model, vintaged | PJM published | ratio |
|---|---:|---:|---:|---|
| Wind | 4,778.1 | **2,447.3** | 1,396 | 3.42× → **1.75×** |
| Solar | 743.8 | **3,352.4** | 4,232 | 0.18× → **0.79×** |

**Both classes move toward the published record, by a wide margin.** The census rises because — once
the right pools are used — the solar leg was under-credited by more than the wind leg was
over-credited. That is rule 14's signal behaving normally. The UP direction is a result, not a bug.

---

## 4. The position at full magnitude, in both of D66 §1.2's frames

Frame B is the like-for-like whole-RTO comparator (published cleared RPM + committed FRR over PJM's
RTO Reliability Requirement); Frame A is D57/D61's RPM-only comparator (cleared RPM over
`RelReq adj FRR + EE add-back`). Both requirement operands are re-read from the in-repo
`demand-curve/pjm/pjm.csv` rather than taken on trust. Gap convention is D66's: **published −
model**. Model column is the incumbent → vintaged at PJM's 2026/27 Table-5 mix.

| DY | pub pos B | pub pos A | model pos | **gap B, pt** | **gap A, pt** |
|---|---:|---:|---|---:|---:|
| 2023/24 | 1.05172 | 1.05520 | 1.08814 → **1.08345** | −3.642 → **−3.173** | −3.293 → **−2.825** |
| 2024/25 | 1.05395 | 1.05551 | 1.03206 → **1.03373** | +2.188 → **+2.022** | +2.345 → **+2.178** |
| 2025/26 | 1.00992 | 1.00489 | 0.96613 → **0.96560** | +4.379 → **+4.432** | +3.877 → **+3.929** |
| | | | **Σ\|gap\|** | 10.209 → **9.627** | 9.515 → **8.932** |

The incumbent column reproduces D66 §1.4's gaps (−3.64 / +2.19 / +4.38 pt) exactly.

**Card B's pre-declaration that "the residual WIDENS" does not survive either.** It narrows in two of
three years, and the Σ|gap| narrows **at every one of the five candidate mixes, in both frames**
(Frame B 10.209 → 9.565–10.080; Frame A 9.515 → 8.870–9.384). The mechanism is not signed the way
the card assumed because it is not one-sided: 2023/24's model position is *above* published and the
repair lowers it, while 2024/25's is *below* and the repair raises it.

**This is reported as a measurement and is NOT the reason to arm anything** (rule 1 `[R-STRUCT]`).
The reason to prefer the vintaged ratings is rule 14: they are the ISO's own published accreditation
for the delivery year each auction cleared on. Had the residual widened at every mix, the
recommendation in §8 would be identical.

---

## 5. A fourth vintage gap the charter would have left open: DY 2025/26

The charter fixes *"DY ≥ 2025/26 reads the marginal-ELCC ratings already wired."* The reform boundary
is right — PJM's `2025-26-3ia-elcc-class-ratings.pdf` (p.1) gives *"the Final ELCC Class Ratings for
the 2025/2026 Delivery Year"* and rates the thermal classes too (Nuclear 95 %, Coal 83 %, Gas CC
78 %), confirming D48's `THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] = "2025/2026"`.
But the **values** differ from the wired 2026/27 set:

| class | DY 2025/26 published | wired (2026/27) |
|---|---:|---:|
| Onshore Wind | 38 % | 41 % |
| Fixed-Tilt Solar | 10 % | 8 % |
| Tracking Solar | 14 % | 11 % |

The model's DY 2025/26 pools clamp to the wired endpoints (wind ≥ 3,956 MW → 0.41; solar 9,431 MW ≤
9,902 MW → 0.1064), so the year is accredited at the wrong vintage by −33 … −410 MW. Small, but it is
the same defect, and a vintage axis that stops at the reform boundary does not close it.

**One open item, deliberately not resolved here:** this is the **3IA** rating set (posted
2025-03-12), PJM's final for the delivery year. The 2025/26 **BRA** (held July 2024) cleared on the
ratings current then, and the 2025/26 BRA Report's own tables are images that do not extract. A
successor lane must fix which vintage a hindcast screen should read — the auction the census is
compared against (BRA) or the delivery year's final (3IA) — **before** it wires the year, and state
it in its PRECOMMIT. The same question arises for DY 2024/25 and is answered there by the Dec-2023
report's explicit "final" language plus the auction's own delay.

---

## 6. What this lane routes rather than absorbs

1. **D66 §3.2/§3.3/§4.5's frozen VRE/storage pools** (§1.3). The corrected rows are given above; the
   fix belongs to whoever next touches that instrument, together with the storage row this lane did
   not recompute. D66's headline and its requirement leg are unaffected.
2. **The repo's PJM ELCC intake needs two vintages where it has one** (§1.1): the Dec-2021 tranche
   must be relabelled *preliminary/superseded* and the Dec-2023 FINAL 2024/25 set added, plus the
   2023/24 tranche (§1.2) and the 2025/26 3IA set (§5). That is an additive `data-intake` job on
   `data/raw/capacity-market/elcc/pjm/pjm.csv` with source doc + page per row — no code, no gate.
3. **The blocked operand** (§2) — the only item that needs a ruling rather than work.
4. **`evolution_2022.json` emits the screen and clearing blocks but not the adequacy block**
   (`wind_cap_mw` / `solar_cap_mw` / `renewable_credit_applied` / `storage_firm_mw` absent), while
   2021 and 2023–2025 carry it. DY 2022/23 is out of scope here so it blocked nothing, but the
   asymmetry is unexplained and worth one look by a lane that owns the ledger.

---

## 7. Matrix, records, collision

* **Matrix (rule 28 `[R-MECH-MATRIX]`): NO CELL WRITTEN.** No mechanism was tested — no field, no
  gate, no solve. The cell this card would create does not exist yet and is created by the PR that
  adds the field (duty (c)), not by this one.
* **Registration (rule 15 `[R-DASHBOARD]`): nothing to register.** No bundle was produced. No screen
  or control bundle exists, so rule 29 clause (c)'s delete-before-merge is vacuous here.
* **Holdout (rule 22 `[R-HOLDOUT]`): untouched.** No solve, no scoring, no registration of any year.
* **Collision:** none taken. The D67 lane owns the requirement seam
  (`resolve_adequacy_requirement_mw`) and D74 the bar/offer seam; this card's seam is
  `resolve_renewable_capacity_credit` + `RENEWABLE_ELCC_CURVES_BY_ISO`, and neither was edited.
* **G-DRIFT:** LIVE, per the charter and `FINDING-capx-d67-2026-09-06.md` §2.2
  (`DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` 0.036 → 0.064645). Form 4 is void; a screen would have
  had to buy its own control at HEAD. Not re-litigated. The arm-A ledgers remain valid as a *read*
  of what the model accredited, which is all §3 uses them for.

---

## 8. Recommendation

**Card B should be re-chartered, not abandoned.** The object is real, the repair is fully identified
from published PJM data, and the only thing standing in the way is one operand and three corrected
premises. In descending order:

**(a) RULE NEEDED — the fixed/tracking split.** PJM does not publish it for any pre-reform vintage
(§2), so the chartered "intake it additively" route does not exist. Three ways out, for the
director to choose; this lane takes none of them:

  1. **Carry PJM's own published Table-5 mix** (12.01 % fixed) as a documented cross-vintage
     reconciliation under rule 14's misalignment exception — a published PJM number on the wrong
     vintage, stated as such. Cheapest, one line of provenance.
  2. **Derive the split from the model's own solar fleet** via EIA-860's `Fixed Tilt?` /
     `Single-Axis Tracking?` fields. This is the only route that regenerates forward and responds to
     modelled build (rule 13's test) — and the only one with real cost: PJM-footprint attribution
     and a mapping from EIA technology codes to PJM's ELCC classes, which is a reconciliation, not
     an identity. A `data-intake` card in its own right.
  3. **Accept the bracket.** §3–§4 show the *conclusion* is mix-insensitive: DY 2024/25 turns DOWN
     only above a **35.4 % fixed-tilt** share (break-even, exact), three times PJM's published
     share; the window total is negative and the Σ|gap| narrows at **every** mix in **both** frames.
     A gate could ship on PJM's published mix with the bracket recorded as the sensitivity.

  **Recommended: (1) now, (2) as a separate card if the director wants the forward-regenerating
  form.** (3) is the honest fallback and is already measured.

**(b) The intake first, whatever is ruled on (a).** §6 item 2 — relabel the Dec-2021 tranche and add
the 2023/24, FINAL 2024/25 and 2025/26 3IA rows. Additive, no code, no gate, and it is a
prerequisite for any build: today the repository's only 2024/25 rating set is the superseded one.

**(c) The successor card's scope should be FOUR delivery years, not one.** 2023/24 (largest
footprint, −667 … −1,395 MW), 2024/25 (−768 … +421), 2025/26 (−33 … −410, the vintage-within-the-
reform gap of §5), with 2022/23 and earlier genuinely out of scope. Its pre-declared signs are in
the PRECOMMIT §6, recorded before any lane measures against them.

**(d) Its phase-0 gate must be re-stated, and stated per year.** A single window-wide band hid a
sign flip between two adjacent years. The right pre-declaration is the per-year table of §3 with the
break-even share named, which is what this lane leaves behind.

**Not chartered, by name:** any solar credit, wind derate or blend weight sized to the position
residual; and any use of PJM's own cleared solar UCAP to back out the model's blend — that would be
deriving an input from the outcome the census is compared against, which rule 13 forbids however it
is motivated.
