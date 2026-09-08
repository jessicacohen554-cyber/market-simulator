# FINDING — THE SCENARIO CAMPAIGN, STAGE C (POLICY): a clean-attribute price does not buy renewables in this model, it buys carbon capture — and the one ISO with no state RPS ceiling is the only one where it buys wind and solar at all

**Lane** SCN-WS5A-POLICY-SYNTH (Stage C synthesis) · **Model** Opus (`claude-opus-5`, rule 27
`[R-PUSH]`) · **Date** 2026-09-08 · **Branch** `claude/scn-ws5a-policy-stage-c-ia1e8c` ·
**Data profile** `code` · **Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`,
`reference_case: REF` · **THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` ·
**Deliverable** plan §3 WS-5 **Stage C**, `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md`.

**ZERO LP.** Nothing was solved, nothing new was registered, no `src/`, `scripts/`, `configs/`
or `tests/` file was touched. Every number below is read from a committed artifact or computed
from one, and the arithmetic is reproducible from the four files in
`results/scn-campaign-policy-2026-09-06/_rollup/`.

**Predecessors — six per-ISO Stage-A FINDINGs, all on `main`, none re-derived here:**
`FINDING-scn-ws5a-policy-{caiso,ercot,miso,neiso,nyiso,pjm}-2026-09-0*.md`, plus
`ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md`. Where this memo differs from one of them it
says so and shows the artifact.

**Audit at HEAD, re-run by this lane, not quoted from the desk:**
`python3 scripts/check_forecast_invariants.py --sidecar-dir` →
**177 sidecars with an invariants block · 2,478 records · 217 declared FAILs · EXIT 0.**

---

## 0. Bottom line

1. **THE HEADLINE IS NOT "THE CES ROW IS NOT WIRED TO ENTRY". IT IS A THRESHOLD, AND THE DESK'S
   OWN FRAMING OF IT WAS WRONG.** The desk carried "the entry screen folds
   `attr = max(EAC, rps_credit_for_zone, clean_credit)` with **no fuel gate** on the RPS leg".
   That is false and is retired here. Both entry folds gate the RPS leg on
   `_RENEWABLE_NEW_FUELS = {"wind", "solar"}` —
   `src/market_sim/model/capacity_evolution/new_entry.py:121`, applied at `:1190-1197` and
   `:1474-1483`, verified against the code by this lane. The consequence is **sharper**, not
   weaker: a campaign level at or under the state ACP is invisible **to a VRE candidate only**,
   and was fully visible from $10 up to every other eligible technology, whose RPS leg is `0.0`
   and whose legacy EAC is `$0.00`. Landed independently by NEISO §2.6.1 and PJM §5a.1 and
   confirmed by MISO §7.1.
2. **THE THRESHOLD IS NOW BRACKETED ON BOTH SIDES IN FIVE ISOs, AND THE ORDERING BY ACP DOES NOT
   HOLD.** Ruling S15's `CES-P60` leg ran on the five masked ISOs. VRE entry is **+0.0 MW against
   REF at every rung on four of them, including at $60 — 20 % above CAISO's and NEISO's ceiling,
   33 % above PJM's, 100 % above MISO's.** The one masked ISO whose VRE entry ever moves is
   **NYISO** (+156.6 MW of solar at 2030, at $50 and at $60, against a $40 ACP). So the mask is
   real, it is measured, and in four of five ISOs **it was never the binding constraint** (§3, §4).
3. **THE TECHNOLOGY THAT ACTUALLY MOVES IS THE ONE THAT WAS NEVER MASKED: NUCLEAR.** Every masked
   ISO's clean-attribute response is new nuclear, and in four of five it lands **exactly on that
   ISO's own annual queue cap** — CAISO / MISO / PJM +1,000.0 MW against a 1.0 GW/yr cap, NEISO
   +500.0 MW against 0.5 GW/yr. The campaign therefore measures the **sign and the cap** of the
   nuclear entry response, **not its elasticity** (§4).
4. **THE CES PREMIUM'S REAL CHANNEL IS THE CCS RETROFIT, AND THE CES TARGET ROW CANNOT REACH IT
   AT ALL — IN FIVE OF SIX ISOs, MEASURED.** `CES-T80`'s $50 ACP buys **exactly +0.0 MW** of
   `gas_cc_ccs` on CAISO, MISO, PJM, NYISO and NEISO, while a **$10** premium buys +8,378 MW on
   MISO and +6,733 MW on PJM. The cause is a code seam, not a level: `ccs.py:475-476` prices the
   retrofit uplift with `effective_eac_price_for_unit = max(legacy eac_price_*, premium × credit)`
   and **never reads `clean_attribute_price_by_fuel`**, where a target-row dual lives and which
   both `new_entry.py` and `retirements.py` do read. **A target case and a premium case are
   therefore not one instrument at two levels**, and any table that ranks them as such
   under-states the target row. Found by NYISO; generalised to the whole footprint here (§5).
5. **THE 3 GW/yr RETROFIT CAP IS THE BINDING CONSTRAINT ON THE ENTIRE CES PREMIUM AXIS, IN FIVE
   OF SIX ISOs, AT THE LOWEST RUNG TESTED.** At $10 the retrofit already sits within 0.4 % of the
   cumulative cap (3,000 / 6,000 / 9,000 MW) on ERCOT, MISO, PJM and NEISO; CAISO's **REF** is at
   98.7 % of it before any policy. The $10 → $60 separation is +0.3 MW (MISO) to +15.5 MW (PJM).
   **The campaign does not identify a CES-premium elasticity anywhere except NYISO**, the one ISO
   with real headroom (REF at 69.5 % of cap), where the ladder is monotone: +779.6 / +1,475.8 /
   +1,506.8 / +1,634.4 MW at $10/$20/$30/$60 (§6).
6. **THE VOLUNTARY AXIS IS INERT EVERYWHERE IT WAS MEASURED, AND THE TWO REASONS ARE DIFFERENT
   FINDINGS.** Six-ISO CO2 moves **−0.084 Mt on 1,203 Mt** at 2030. On ERCOT and MISO the row
   *escapes at its $7.00 ceiling* — the level is the reason, and a higher ceiling is a live
   question. On CAISO the row prices at **−0.0 with escape 0** — it is slack, and the level is
   *not* the reason. NYISO is the strongest null in the campaign because it moves the *volume* by
   35 % (1.82 → 6.39 TWh between the two committed paths) and still returns byte-identical
   headline, by-fuel and curtailment frames (§7).
7. **CAISO IS THE FIRST AND ONLY ISO IN THE CAMPAIGN TO MEET THE FEDERAL TARGET IN A YEAR.**
   `CES-T80`'s row escapes at the ACP **$50.0000 exactly** in 2026–2029 and goes **strictly
   interior at 6.9465** in 2030, with credited generation **178.915 TWh** against an obligation of
   **178.912 TWh** — measured from CAISO's committed `duals.json`, not inferred (§8).
8. **THE SIX-ISO ROLLUP.** REF 2030 = **1,223.07 Mt**. The CES premium ladder cuts
   **−50.90 / −52.45 / −56.33 Mt** at $10/$20/$30 (−4.2 % / −4.3 % / −4.6 %) and is **exactly zero
   before 2028**, the year the retrofit gate opens — which is the cleanest possible confirmation of
   §0.4. The CES *target* cuts **−24.62 Mt**, less than half. High load adds **+243.06 Mt**; the
   coherent policy corner `ALL-CLEAN` claws back **−58.54 Mt of it (24.1 %)** and still lands
   **+184.52 Mt above REF** (§9).
9. **THE CAMPAIGN IS AT ONE EFFECTIVE PIN, VERIFIED RATHER THAN ASSUMED.** Four `basis_sha` values
   appear across the twelve reference legs; the three non-pin shas are descendants of the pin whose
   `git diff <pin> <sha> -- src/market_sim scripts configs data/raw` is **empty**. The plan's "the
   campaign sits at two declared pins" caveat is **retired**, as is the ERCOT contamination caveat,
   which `ADDENDUM B` closed by re-solving ERCOT's reference legs at the pin (§10.1, `_rollup/PROVENANCE.md` §2).
10. **THREE CORRECTIONS TO THE STATE OF THE RECORD, AGAINST THIS LANE'S OWN BRIEF.** (a) `CES-P60`
    is registered on **five** ISOs, not six — ERCOT was never owed one and correctly never ran one,
    because ERCOT has no `STATE_RPS_ACP` row and therefore no mask to bracket. (b) **SPP does have
    scenario base YAMLs** at HEAD (`configs/scenarios/spp_scenario_base_{2026_2030,2026_2050}.yaml`,
    landed 2026-09-07 by SPP-38); it is still outside the campaign and the system total, but for a
    different reason. (c) The invariant audit at HEAD reads **177 / 2,478 / 217**, not 176 / 2,464 / 217 (§10.4).

---

## 1. What was solved, what is registered, and the two roots reconciled

### 1.1 The ragged tree, resolved explicitly

| root | contents | committed `full_horizon_summary.json` |
|---|---|---|
| `results/scn-campaign-policy-2026-09-06/` | the policy legs | **65** — CAISO 8 · ERCOT 11 · MISO 13 · NEISO 10 · **NYISO 12** · PJM 11 |
| `results/scn-campaign-load-2026-09-06-r2/` | the campaign's reference legs, re-solved by SCN-WS5A-RESOLVE after capx D77 | **16** — `REF` + `LOAD-HI` for all six, `LOAD-HI-ORGANIC` for CAISO / ERCOT / MISO / NYISO |

NYISO's twelve include its own copies of `REF` and `LOAD-HI`; CAISO's eight do not. The two
copies carry the **same `cache_key`** (`f10cc93084b4c0db`, `c2ceaefa4afafcda`) and **byte-identical
`trajectory` arrays** as the r2 originals, differing only in `campaign`, `run_config_path` and the
wall-clock/RSS block, so they are duplicates of the same solve and are deduplicated in the rollup.
**Union after deduplication: 79 summaries.**

**Which `REF` each ISO's deltas are taken against: the r2 root's, for all six ISOs, in every table
in this memo and in every row of `_rollup/`.** No delta anywhere here is taken against a pre-r2
bundle — RESOLVE measured the pre-repair CO2 levels overstated by up to **57 %**, and the error does
not cancel out of a delta because the two arms re-screen the retrofit fleet differently.

### 1.2 Registered legs: 63, and why that is not 65

63 sidecars exist as `frontend/data/hindcast/<iso>-2026-2030-scn-campaign-policy-2026-09-06-<case>.json`
— **CAISO 8 · ERCOT 11 · MISO 13 · NEISO 10 · NYISO 10 · PJM 11.** The two-leg gap against the 65
committed summaries is exactly NYISO's `REF` and `LOAD-HI` copies, which are registered under the
**load** campaign, not the policy one. There is no unregistered policy leg.

### 1.3 `CES-P60` is on five ISOs, and that is correct

Ruling S15 adds the bracketing leg **"where the mask binds"**. ERCOT has **no `STATE_RPS_ACP`
entry** (`capacity_market.py:5132-5138` lists CAISO / NYISO / NEISO / PJM / MISO only) and its
`rps_dual` is **0.0 in every year of every leg**, so there is no mask to bracket and no leg was
owed. Neither the ERCOT FINDING nor ADDENDUM B mentions `CES-P60`, consistent with that. **This
strengthens the campaign rather than weakening it**: ERCOT is the unmasked control (§3.3), and a
control does not need the bracket that exists to lift a mask it never had.

### 1.4 The pin, audited at zero cost

| leg set | `git.basis_sha` | solve-path diff vs the pin |
|---|---|---|
| ERCOT, NEISO, NYISO, PJM `REF` (+ all 65 policy legs) | `bdfb3095e9fa…` | — (is the pin) |
| CAISO `REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` | `c538ecfb0176` | **empty** (adds 1 file: its own PRECOMMIT) |
| MISO `REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` | `95ad76d4cd81` | **empty** (adds 1 file: its own PRECOMMIT) |
| PJM `LOAD-HI` | `9ef06cf8a760` | **empty** (adds 41 doc / sidecar / results files, 0 solve-path) |

`git diff bdfb3095e9fa <sha> -- src/market_sim scripts configs data/raw` returns an empty diffstat
for all three, and all three are descendants of the pin. **One effective pin.** This retires the
plan §5.1 Load-HI cell's "the campaign sits at two declared pins" and does it the rule-29
`[R-SCREEN]` (b) way — a code-level G-DRIFT audit, at zero LP, rather than a control solve.

---

## 2. Deliverable 1 — the rollup, committed

`results/scn-campaign-policy-2026-09-06/_rollup/` (new; created by this lane):

| file | what it is |
|---|---|
| `campaign_emissions_by_iso.csv` | one row per (case, iso, year): CO2 level, the two side lines, `cache_key` |
| `campaign_emissions_system.csv` | one row per (case, year): the **six-ISO modeled system** sum, with `isos` / `isos_missing` |
| `campaign_delta_table.csv` | per-ISO and system deltas vs `REF`, each row carrying `delta_isos` / `delta_n_isos` / `delta_coverage` |
| `campaign_report.md` | the tool's own markdown: coverage, levels, final-year deltas, the three side-line disclosures |
| `PROVENANCE.md` | **written by this lane** — how the root was assembled, which `REF`, why the side lines are blank, what the total is not |

Produced by `scripts/collate_scenario_campaign.py`, **unmodified**, `--reference-case REF`. Because
the tool takes one `--root` and the campaign's summaries live in two committed roots, it was pointed
at a **read-only union of copies** assembled in the session scratchpad (79 summaries; the two NYISO
duplicates dropped). **No committed bundle was moved, renamed or deleted.** Full recipe and the
reproduce command: `_rollup/PROVENANCE.md` §1.

**PJM's FINDING §0.1 correction is upheld and this lane can confirm it from the artifact:**
`collate_scenario_campaign.py` was **never** blind to PJM's legs. It reads
`<root>/<iso>/<case>/full_horizon_summary.json` off disk, and PJM's eleven summaries have always
been committed. The three-refresh gap was **registry-side only**.

**Cross-check that the rollup is right:** its ERCOT 2030 deltas reproduce
`ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md` §0 to four decimals independently —
CARB-HI −10.7360, CARB-LO −10.6016, CES-P10 −10.0300, VOL-HI +0.0000, ALL-CLEAN +4.2334 Mt.

---

## 3. The RPS-ACP entry threshold — and the correction to the desk's framing

### 3.1 What the desk carried, and what the code says

> **Retired framing (do not repeat):** "the entry screen folds
> `attr = max(EAC, rps_credit_for_zone, clean_credit)` with **no fuel gate** on the RPS leg."

**Measured against the code by this lane** (`src/market_sim/model/capacity_evolution/new_entry.py`):

```
:121   _RENEWABLE_NEW_FUELS: frozenset[str] = frozenset({"wind", "solar"})

:1190  rps_for_tech = (
:1191      rps_credit_for_zone(rps_shadow_price, _candidate_zone_idx(tech, …))
:1196      if tech in _RENEWABLE_NEW_FUELS
:1197      else 0.0
:1474  )   # and identically at the second fold, :1474-1483
```

The RPS leg **is** fuel-gated to wind and solar, at both folds. So:

| candidate technology | RPS leg | legacy EAC | attribute seen at a campaign premium `P` |
|---|---|---|---|
| **wind / solar** | the ISO's `rps_dual` (= its ACP, in every year of every leg) | $0.00 | `max(P, ACP, clean) = ACP` for every `P ≤ ACP` → **REF's; masked** |
| **nuclear, CCS, hydrogen, every other eligible tech** | **0.0** | **$0.00** | `max(P, 0, clean) = P` → **fully visible from $10 up** |

### 3.2 Why this makes the null sharper, not weaker

The campaign's five-ISO null on VRE entry was never evidence that "the CES row is not wired". It is
a **threshold in the ACP** for VRE, and **no mask at all** for everything else. The corollary the
bracket then proved: the technology that eventually moves is the one that **was never masked**
(§4). `STATE_RPS_ACP` (`config/capacity_market.py:5132-5138`, verified):

| ISO | `STATE_RPS_ACP` | measured `rps_dual`, all legs, all years |
|---|---|---|
| MISO | **30.0** | 30.0 |
| NYISO | **40.0** | 40.0 |
| PJM | **45.0** | 45.0 |
| CAISO | **50.0** | 50.0 |
| NEISO | **50.0** | 50.0 |
| ERCOT | **absent** | **0.0** |

The dual sits **at** the ACP in every year of every leg in all five masked ISOs — the escape regime,
never interior. So the mask is not merely present, it is at its ceiling for the whole horizon.

### 3.3 ERCOT is the unmasked control, and it is the only ISO where the ladder buys VRE

`builds_renew_mw`, ERCOT, against REF:

| case | 2026 | 2027 | 2028 | **2029** | 2030 |
|---|---|---|---|---|---|
| `REF` | 0.0 | 653.1 | 0.0 | **7,846.9** | 6,654.6 |
| `CES-P10` | 0.0 | 653.1 | 0.0 | **8,346.9** (+500) | 6,654.6 |
| `CES-P20` | 0.0 | 653.1 | 0.0 | **8,346.9** (+500) | 6,654.6 |
| `CES-P30` | 0.0 | 653.1 | 0.0 | **9,346.9** (+1,500) | 6,654.6 |
| `CES-T80` | 0.0 | 653.1 | 0.0 | **11,346.9** (+3,500) | 6,654.6 |

**Monotone in the attribute price, in the one ISO where nothing masks it.** That is the positive
control the five nulls needed, and it is why ERCOT matters to this campaign despite everything in
§10.1. Its cost is stated where it belongs: `CES-T80` buys those 3,500 MW of solar by **displacing
3,000 MW of gas-CC** and shedding **+16.8 TWh** more in 2029 (reserve margin −0.2252 vs REF's
−0.2060). On an energy-only ISO already in shortage, a standard that prices only attributes buys
clean energy and adequacy loss in the same screen.

---

## 4. The threshold, bracketed on both sides — one table, ordered by ACP

**Read the table as two questions, because the mask answers only the first.**

| ISO | ACP | VRE entry Δ vs REF at $10 / $20 / $30 | **VRE at the bracket** | **nuclear Δ vs REF** | that ISO's nuclear queue cap |
|---|---|---|---|---|---|
| **MISO** | **30** | +0.0 / +0.0 / +0.0 | `P60` **+0.0 MW** | `T80` **+1,000.0** (2030) · `P60` **+1,000.0** | 1.0 GW/yr — **at cap** |
| **NYISO** | **40** | +0.0 / +0.0 / +0.0 | `T80` **+156.6** · `P60` **+156.6** (2030) | `P60` **+500.0** (156.6 in 2029, 343.4 in 2030) · `T80` +0.0 | 0.5 GW/yr — **under cap** |
| **PJM** | **45** | +0.0 / +0.0 / +0.0 | `P60` **+0.0 MW** | `T80` **+1,000.0** (2030) · `P60` **+1,000.0** | 1.0 GW/yr — **at cap** |
| **CAISO** | **50** | +0.0 / +0.0 / +0.0 | `P60` **+0.0 MW** | `P60` **+1,000.0** (2029 **and** 2030) · `T80` +0.0 | 1.0 GW/yr — **at cap** |
| **NEISO** | **50** | +0.0 / +0.0 / +0.0 | `P60` **+0.0 MW** | `P60` **+500.0** (2029 and 2030) · `T80` +0.0 | 0.5 GW/yr — **at cap** |
| **ERCOT** | **none** | **+500 / +500 / +1,500** (2029) | *(not owed — no mask)* | +0.0 at every level | 2.0 GW/yr |

`builds_renew_mw` and `capacity_by_fuel_mw["nuclear"]`, read from each leg's committed
`full_horizon_summary.json`. Queue caps: `constants.QUEUE_CAP_PER_TECH_GW`.

### 4.1 Does the ordering by ACP hold? **No — and that is the result.**

If the ACP were the binding constraint on VRE entry, the four ISOs whose ACP the $60 bracket clears
would all build something. **Four of five build exactly nothing.** The ACP predicts the VRE step in
**one** ISO of five (NYISO, step inside (40, 50]), and that step is **156.6 MW** — 0.6 % of NYISO's
2030 capacity. Everywhere else, lifting the mask by 20–100 % changes VRE entry by **+0.0 MW to the
decimal**. The correct statement is: **the mask is real, it is measured, and outside NYISO it is not
what stops renewables from entering.** What stops them is the candidate's own delivered economics —
which is MISO §7.1's sharpest sentence and now holds footprint-wide.

### 4.2 What the nuclear column does and does not identify

Four of five responses land **exactly on that ISO's annual queue cap**. A response pinned to its cap
measures the **sign** of the entry decision and the **cap**, and cannot measure the elasticity: any
attribute price above the threshold buys the same MW. NYISO is the one unpinned reading
(+156.6 MW in 2029, +343.4 in 2030, summing to 500.0 against a 0.5 GW/yr cap in *each* year).

**The nuclear threshold, read only where the arm's attribute price is actually known:**

| ISO | is `T80`'s dual $50 in the deciding year? | nuclear threshold |
|---|---|---|
| MISO | **yes**, `[−0.0, −0.0, 50.0]` all five years (committed `duals.json`) | **(30, 50]** |
| PJM | **not measurable** — no PJM leg committed a duals artifact | ≤ 50 *(the arm builds; the price is inferred, not read)* |
| NYISO | **no** — the row binds interior in 2029/2030 (credited = target·D to 5×10⁻⁵ TWh); value unrecoverable | **(50, 60]** on the premium ladder alone |
| CAISO | **no** — `[50.0, 50.0, 50.0, 50.0, **6.9465**]` (committed `duals.json`) | **(50, 60]** on the premium ladder alone |
| NEISO | **no** — `50.0000` exactly 2026–28, **`−0.0`** in 2029 (REF's own credited share already clears the target), **strictly interior `4.2912`** in 2030 | **(50, 60]** on the premium ladder alone |

**A `CES-T80` arm is a "$50 data point" only where its row escapes.** Where the row goes interior,
the entry screen sees the interior dual — single digits, not $50 — so that arm cannot bracket
anything, and reading it as a $50 rung would be wrong. This is a second reason a target case and a
premium case are not one instrument at two levels (§5).

---

## 5. The CES premium's real channel is the CCS retrofit — and the CES *target row* cannot reach it

**State this at the top of any table that ranks `CES-T80` beside `CES-P*`, not in a footnote.**

`gas_cc_ccs` capacity, **Δ vs REF at 2030, MW**:

| ISO | `CES-P10` ($10) | `CES-P20` | `CES-P30` | `CES-P60` | **`CES-T80` ($50 ACP)** |
|---|---|---|---|---|---|
| MISO | **+8,378.4** | +8,378.5 | +8,376.3 | +8,378.7 | **+0.0** |
| PJM | **+6,732.5** | +6,745.7 | +6,748.9 | +6,748.0 | **+0.0** |
| NYISO | +779.6 | +1,475.8 | +1,506.8 | +1,634.4 | **+0.0** |
| NEISO | +1,220.1 | +1,301.8 | +1,304.0 | +1,307.0 | **+0.0** |
| CAISO | +97.8 | +106.8 | +109.9 | +111.3 | **+0.0** |
| ERCOT | +3,205.7 | +3,190.8 | +3,219.6 | *(not owed)* | +185.1 |

**Five of six ISOs: a $50 target ACP buys exactly zero retrofit where a $10 premium buys thousands
of megawatts.** NYISO's lane found the seam and named it:

> `ccs.py:475-476` prices the retrofit's attribute uplift with
> `effective_eac_price_for_unit = max(legacy eac_price_*, premium × credit)` and **never reads
> `clean_attribute_price_by_fuel`** — the field where a target-row dual lives, and which both
> `new_entry.py` and `retirements.py` **do** read.

NYISO is the cleanest single demonstration: **`CES-T80`'s $50 ACP buys 0.0 MW of retrofit while
`CES-P20`'s $20 premium buys 1,475.8 MW at 2030.** This memo's contribution is that the same zero
appears in **four more ISOs**, on independently configured legs, which removes the possibility that
it is a NYISO artifact.

**Consequences for how the campaign may be read.**

1. **A target row and a premium are not the same instrument at two levels.** They reach different
   seams: a premium enters `apply_eac_to_mc` → dispatch marginal cost **and** the retrofit screen;
   a target row's dual enters **entry and retirement only**. Ranking them on one axis under-states
   the target row by the whole retrofit channel.
2. **They are additive and separable, and MISO measured it.** `CES-P60 − CES-P30 = −3.9996 Mt`
   against `CES-T80 = −4.0250 Mt` at 2030 — the nuclear channel recovered to 0.6 % from two arms
   sharing no configuration. A model in which one instrument proxied the other would not do this.
3. **The federal target's real-world analogue is a tradeable credit that a CCS retrofit would
   earn.** This model's target row cannot pay it. That is a **defect in reach, not a level**, ruled
   **D-15 / S19** and routed to the capx director as a named lane. **This lane reports it and does
   not fix it** (`src/` is outside its regions).

**The dispositive timing evidence, from the rollup.** `ccs_retrofit_available_year = 2028`. The
six-ISO CES-premium delta is:

| year | 2026 | 2027 | **2028** | 2029 | 2030 |
|---|---|---|---|---|---|
| `CES-P20` Δ vs REF (Mt) | +0.014 | −0.009 | **−19.532** | −35.550 | **−52.451** |

**Exactly zero, to 0.01 Mt, in both years before the retrofit gate opens, and −19.5 Mt in the year
it does.** No other channel in the model has that footprint.

---

## 6. Saturation and the binding retrofit cap — a shared constraint on the whole CES axis

`ccs_retrofit_max_gw_per_year = 3.0` per ISO ⇒ a **cumulative** 3,000 / 6,000 / 9,000 MW at
2028 / 2029 / 2030.

| ISO | REF `gas_cc_ccs` 2030 | **% of the cumulative cap, in REF** | headroom | what the premium ladder can identify |
|---|---|---|---|---|
| **CAISO** | 8,885.7 | **98.7 %** | 114.3 MW | **nothing** — REF is already at the cap |
| **NEISO** | 7,691.3 | 85.5 % | 1,308.7 MW | little — every rung is at cap by 2030 |
| **NYISO** | 6,255.9 | **69.5 %** | 2,744.1 MW | **a real ladder** — see below |
| **ERCOT** | 5,763.8 | 64.0 % | 3,236.2 MW | cap-bound at $10 from 2028 |
| **PJM** | 2,248.7 | 25.0 % | 6,751.3 MW | cap-bound at $10 |
| **MISO** | 618.1 | 6.9 % | 8,381.9 MW | cap-bound at $10 |

- **CAISO saturates between $10 and $30 because its REF is already at the cap.** The P20 → P30
  step is **−0.0165 Mt = 0.086 %** against a pre-registered ">1 %" band, and the retrofit fleet sits
  at 2,996.6–2,999.9 / 5,979.1–5,998.4 / 8,885.7–8,997.0 MW in **every arm, REF included**. CAISO's
  measured saturation is a **cap artifact**, not a demand-curve property.
- **PJM is cap-bound at $10 already and still cuts 2030 CO2 by −14.34 / −14.07 / −13.99 Mt (−3.1 %).**
  The +16.4 MW separation from $10 to $30 measures a **binding constraint, not an elasticity**.
  A large abatement number and an unidentified elasticity are compatible, and here they coexist.
- **MISO: +2,663 / +2,714 / +3,000.0 MW per year against REF's 334.5 / 283.7 / 0, flat in the
  premium** — $10 and $60 within **0.3 MW** of each other, the 2030 increment the cap to the tenth
  of a MW. That is the whole of MISO's −20.4 Mt.
- **NYISO is the campaign's only identified CES-premium retrofit elasticity**: +779.6 → +1,475.8 →
  +1,506.8 → +1,634.4 MW at $10 → $20 → $30 → $60, monotone, and not at cap until 2029.

**Reading for the owner:** the campaign's CES-premium CO2 numbers are a measure of **how much CCS
retrofit each ISO's fleet can physically absorb under a 3 GW/yr cap**, not of how much a $10 vs a
$30 credit would buy. If the elasticity is the question, the cap is the parameter to vary — and
that is a Stage-B design question, not a re-level of §3.5.

---

## 7. The voluntary axis — inert everywhere, for two different reasons

Six-ISO 2030 CO2, `VOL-HI` vs `REF` on the common set: **−0.0838 Mt on 1,203.12 Mt (−0.007 %).**
`VOL-MID` is **−0.0836 Mt**. Per-ISO Δ at 2030: ERCOT +0.0000 · MISO −0.0023 · PJM +0.0014 ·
NYISO +0.0012 · NEISO −0.0841 Mt. CAISO's `VOL-HI` was killed at phase 0.

**The distinction the campaign can now make, and must:**

| ISO | voluntary row's regime | measured dual | which finding this is |
|---|---|---|---|
| **ERCOT** | **escapes at its ceiling** from 2028 | `[−0.0, −0.0, 7.0, 7.0, 7.0]` (committed `duals.json`) | **the level is the reason** — escape 24.5 / 59.0 / 100.8 TWh; a higher WTP ceiling is a live question |
| **MISO** | **escapes at its ceiling** from 2028 | `[…, 7.0]` from 2028 (committed `duals.json`) | **the level is the reason** |
| **NEISO** | **binds** 2026–28 at the arm's own ceiling, slack 2029–30 | $4.50 / $7.00 exactly when binding, −0.0 when slack | **the level is the reason** — and NEISO is the pure ladder: `E_DC = 0`, so `VOL-MID` and `VOL-HI` carry the **identical volume to the MWh** |
| **CAISO** | **slack, escape 0** | **−0.0** in all five years | **the level is NOT the reason** — the row never binds, so the ceiling is untested |
| **NYISO** | escapes | not recoverable (§10.5) | **the strongest null**: volumes differ by **1.82 → 6.39 TWh** (`E_DC` 3.64 → 12.78 TWh) and the two arms are **byte-identical** in the headline, by-fuel and curtailment frames; the only difference anywhere is by-zone CO2 attribution, max \|Δ\| **2.9×10⁻⁵ Mt** |
| **PJM** | not recoverable (no duals artifact) | — | `VOL-MID` ≡ `VOL-HI` bit-for-bit in every trajectory field except `co2_mt` at 2029 (2×10⁻⁴ Mt) and 2030 (1×10⁻⁴); doubling volume 216.1 → 360.6 TWh buys nothing, both ceilings 6–10× under the $45 the eligible fleet already earns |

**Why "inert because the level is low" and "inert because the row escapes" are different findings.**
An **escaping** row is one whose buyers have already paid the ceiling and gone home: raising the
ceiling is a live lever and the campaign has simply not tested a high enough one. A **slack** row
(CAISO) has demand below the eligible fleet's output — the ceiling is irrelevant at any level, and
raising it would change nothing. Only the first is about the levels. **D-2(b)'s ceiling evidence can
therefore be carried by NEISO and ERCOT, and not by CAISO.**

### 7.1 Ruling S11 — both nettings, reported, neither asserted

S11 settles D-6 as *"a voluntary MWh counts toward the federal standard; report both."* NYISO's
`ALL-CLEAN` produces the campaign's largest spread, because it is the one arm where a CES **target
row** and the voluntary row are both live:

| yr | credited TWh | V TWh | target·D TWh | **counts-toward escape** | **additional escape** |
|---|---|---|---|---|---|
| 2026 | 60.486 | 17.677 | 87.103 | **26.618** | 44.295 |
| 2027 | 60.486 | 21.148 | 93.859 | **33.373** | 54.521 |
| 2028 | 82.267 | 24.627 | 100.905 | **18.638** | 43.265 |
| 2029 | 108.251 | 28.114 | 108.251 | **0.000** | 28.114 |
| 2030 | 115.909 | 31.611 | 115.909 | **0.000** | 31.611 |

The two readings differ by exactly `V` — **17.68 → 31.61 TWh, more than the entire eligible fleet's
annual output** — and in 2029–2030 they are the difference between a **met** standard and a
**28.1 / 31.6 TWh shortfall**. `CES-P20+VOL-HI` carries the same arithmetic without a target row
(counts-toward escape 24.27 / 29.60 / 13.16 / 0 / 0 TWh). **Neither reading is asserted here.** The
size of the open modelling choice is the deliverable.

---

## 8. `CES-T80` and the one year the federal target is met

CAISO is the first and only ISO in the campaign to go **strictly interior**, measured from its
committed `duals.json`:

| year | CAISO `clean_region_duals` | regime |
|---|---|---|
| 2026 | **50.0000** | escape at the ACP |
| 2027 | **50.0000** | escape |
| 2028 | **50.0000** | escape |
| 2029 | **50.0000** | escape |
| **2030** | **6.9465** | **BINDING — credited 178.915 TWh vs an obligation of 178.912 TWh** |

Both limbs of the G4 dual identity are therefore exercised on one ISO in one arm. NYISO exercises
both too — escape in 2026–2028 (shortfall 24.27 / 29.60 / 13.26 TWh), binding **exactly** in 2029
and 2030 (credited share 0.6333333332 vs a target of 0.6333330000, i.e. the LP drives credited to
`target·D` within **5.3×10⁻⁵ TWh**) — but its dual **value** is not recoverable (§10.5). NEISO
exercises both as well — `CES-T80`'s row reads **50.0000** in 2026–2028, **−0.0** in 2029 where REF's
own credited share already clears the target, and **strictly interior 4.2912** in 2030; its
`ALL-CLEAN` arm, which carries the CES and voluntary rows together, reads `[50.0, 7.0]` → `[−0.0,
−0.0]` → `[4.2051, −0.0]`.

**Everywhere else the target row escapes at $50 for the whole horizon**: ERCOT `[50.0]×5` and MISO
`[−0.0, −0.0, 50.0]×5`, both from committed duals; PJM's regime is supported by the volumes (unmet
by 208.967 → 564.746 TWh) but its dual is not carried.

---

## 9. The six-ISO CO2 rollup, with the three side lines beside it

**The total is the `six-ISO modeled system` — ERCOT + CAISO + MISO + PJM + NYISO + NEISO, roughly
two thirds of US load. It is never a national figure.**

### 9.1 Levels and deltas, full-coverage cases only

Six-ISO CO2, Mt:

| case | 2026 | 2027 | 2028 | 2029 | **2030** | **Δ2030 vs REF** |
|---|---|---|---|---|---|---|
| `REF` | 1,026.95 | 1,097.02 | 1,141.53 | 1,155.57 | **1,223.07** | — |
| `CES-P10` | 1,026.97 | 1,097.02 | 1,122.07 | 1,121.18 | **1,172.18** | **−50.90** (−4.16 %) |
| `CES-P20` | 1,026.97 | 1,097.02 | 1,122.00 | 1,120.02 | **1,170.62** | **−52.45** (−4.29 %) |
| `CES-P20+VOL-HI` | 1,026.98 | 1,097.01 | 1,121.98 | 1,119.97 | **1,170.63** | **−52.44** |
| `CES-P30` | 1,026.94 | 1,097.01 | 1,122.08 | 1,117.60 | **1,166.74** | **−56.33** (−4.61 %) |
| `CES-T80` | 1,026.98 | 1,097.02 | 1,140.72 | 1,141.19 | **1,198.46** | **−24.62** (−2.01 %) |
| `LOAD-HI` | 1,129.57 | 1,250.40 | 1,314.48 | 1,373.01 | **1,466.14** | **+243.06** (+19.9 %) |
| `ALL-CLEAN` | 1,129.59 | 1,241.29 | 1,279.74 | 1,324.98 | **1,407.60** | **+184.52** |

**`ALL-CLEAN` must be read against `LOAD-HI`, not `REF`** — it is CARB-MID + CES-T80 + VOL-HI + **LOAD-HI**,
so it carries the high-load demand by construction (its ERCOT and PJM 2030 levels are identical to
`CARB-MID+LOAD-HI`'s, 317.099 and 589.969 Mt). Against `LOAD-HI`:

| year | 2026 | 2027 | 2028 | 2029 | **2030** |
|---|---|---|---|---|---|
| `ALL-CLEAN` − `LOAD-HI` (Mt) | +0.014 | −9.109 | −34.741 | −48.026 | **−58.541** |

**The coherent policy corner claws back 24.1 % of the load-driven CO2 increase and leaves
+184.5 Mt above REF.** That is the campaign's single most quotable climate result, and it is a
result about the *size of the load shock*, not about weak policy.

### 9.2 Partial-coverage cases — read `delta_coverage` before quoting

Five of the seventeen cases do not span all six ISOs, and `campaign_delta_table.csv` differences
them on the **intersection** with `REF` (the SCN-FIX1 repair; without it a partial arm silently
differences against a wider reference and understates by the missing ISOs' whole levels — measured
at 71 % on the load campaign). The `CES-P60` row is the one that matters here:

| scope | `CES-P30` 2030 | `CES-P60` 2030 | **P60 − P30** |
|---|---|---|---|
| CAISO+MISO+PJM+NYISO+NEISO (5 ISOs, `REF` = 910.21 Mt) | 867.16 | **856.02** | **−11.13 Mt** |

Per-ISO: CAISO −2.518 · MISO −4.000 · PJM −4.098 · NYISO −0.644 · NEISO +0.127 Mt. NEISO's
**positive** in-ISO sign at $60 is not an error — see §9.3.

### 9.3 Side line (i) — import-attributed CO2, reported beside the total, never inside it

**The tool's own side-line columns are blank in these files, and that is correct behaviour, not a
gap in the campaign.** `import_co2_mt_reported` and `unserved_mwh` are not in the
`full_horizon_summary.json` schema; the tool reconstructs them from each run's cached
`year_*.parquet`, and **no scenario cache is on disk** (gitignored, fresh container). The tool
reports a blank, which it documents as "never a zero". The lane-measured values exist and are
carried here with citations:

| ISO | `import_co2_mt_reported`, REF 2026 → 2030 | as % of in-ISO at 2030 | source |
|---|---|---|---|
| **NYISO** | **10.4548 → 11.0746 Mt** | **101.6 %** | NYISO FINDING §2.0 |
| **NEISO** | 4.7657 Mt at 2030 (REF) | 78 % | NEISO FINDING §2.2 |
| **CAISO** | **0.0000 in every Stage-A leg-year except one** — `CES-P60` books 0.020423 Mt at 2030 | ~0 % | CAISO FINDING §0.6 |
| **MISO** | **0.0000 Mt in every leg-year** — no import node in the committed topology | 0 % | MISO FINDING §0.10 |
| **ERCOT** | 0.0 by construction | 0 % | ERCOT FINDING §2 |
| **PJM** | not carried (no committed side-line artifact) | — | — |

**Two consequences that are results, not caveats.**

- **NYISO's campaign CO2 deltas measure roughly half the emissions NYISO's consumption causes.**
  By 2030 its imported CO2 **exceeds its own** (11.07 vs 10.90 Mt), because D77 + D65-B cut the
  in-ISO denominator 23.69 → 10.90 Mt while the import line stayed flat at 9.8–11.1 Mt. On
  `CES-P60` at 2030 the import cut (−4.598 Mt) is **88 % as large as the in-ISO cut** (−5.244 Mt).
- **NEISO's CES ladder reverses sign across the leakage line, twice.** In-ISO `emissions_mt` goes
  2.8713 → 2.9392 → 3.0664 Mt at $20 → $30 → $60 (**rising with the premium**) while the
  leakage-inclusive total goes 6.1017 → 5.2251 → **4.3002 Mt** (falling), as imports collapse
  29.14 → 10.22 → **1.11 TWh**. **A reader given `emissions_mt` alone would conclude that a higher
  CES premium raises NEISO's emissions.** This is the campaign's strongest case for the WS-0
  disclosure duty and the reason no CO2 number in this memo is quoted without its import line.

### 9.4 Side line (ii) — unserved energy

`unserved_mwh` is **0.0 in every Stage-A leg-year on NYISO** (`ALL-CLEAN` included) and zero or
immaterial on CAISO, MISO, NEISO and PJM. **ERCOT is the exception and it is severe**: its REF
sheds **0.38 → 127.2 TWh** across 2026–2030, and `CES-T80` adds **+16.8 / +16.4 TWh** on top in
2029/2030. A case whose CO2 falls while unserved energy rises has not decarbonised — on ERCOT,
read the two together, always.

### 9.5 Side line (iii) — what is outside the number

SPP, the Southeast (Southern / TVA / Duke and the rest of SERC), and the non-ISO West (the WECC
balancing areas outside CAISO). The remaining third of US load is **not modeled and not estimated**.
SPP specifically: §10.4.

---

## 10. The campaign's honest-unfit list, at full magnitude

### 10.1 ERCOT's REF is adequacy-collapsed, and every ERCOT price delta is disclosure-only

Measured by this lane from ERCOT's committed `REF` summary:

| year | `lw_price` $/MWh | hours ≥ $2,000 | hours ≥ $500 | reserve margin |
|---|---|---|---|---|
| 2026 | 91.04 | 74 | 74 | **+3.31 %** |
| 2027 | **982.31** | 1,552 | 1,653 | **−6.48 %** |
| 2028 | **3,215.99** | 5,439 | 5,439 | **−15.74 %** |
| 2029 | **3,846.00** | 6,633 | 6,634 | **−20.60 %** |
| 2030 | **4,437.53** | 7,950 | 7,962 | **−25.25 %** |

The load-weighted price is at **89 % of the $5,000 cap** by 2030 and **91 % of all hours** clear
above $2,000. This is the known G-S4 defect, declared under G2 **before any solve**, and the WS-1b 2027
pair reported it as 641 scarcity hours / −6.5 % reserve margin / **4.6 TWh unserved in both arms**.

- **NOT campaign-grade:** every ERCOT **price** level and captured price, in every year, in every arm.
- **Robust to it:** ERCOT's **CO2** and **merit-order** results, and every leg-vs-leg comparison.
- **And ERCOT still matters more than any other ISO to §3–§4**, because it is the campaign's only
  **unmasked control on entry**. The one ISO where the ladder demonstrably buys VRE is the one whose
  price you cannot quote. That is an uncomfortable pairing and it is stated, not managed.
- **The 2028–2030 contamination caveat is RETIRED**, not carried: ADDENDUM B re-solved ERCOT's three
  reference legs at the pin, the committed r2 `REF` converts 0 / 2,763.8 / 5,763.8 MW of CCS on its
  own, and this memo's deltas reproduce ADDENDUM B's re-difference exactly (§2).

### 10.2 The T1-F FC-1 live fail sets, per ISO

Read from the committed **bare** `ff-verdicts.json` keys (`<iso>-t1f`), not from a `-pre-*` or
`-ff2d` snapshot:

| ISO | FC-1 | live failing invariants |
|---|---|---|
| **NEISO** | **PASS** | — |
| **NYISO** | **PASS** | — |
| **CAISO** | FAIL | **I12, I7** (accredited firm 46,105 < requirement 57,306 MW at 2026; reserve margin 10.4 % vs a [15 %, 30 %] band) |
| **MISO** | FAIL | **I12, I7** |
| **PJM** | FAIL | **I12, I7** |
| **ERCOT** | FAIL | **I12, I3** (reserve margin 8.9 % → −2.5 %; slack in 2027–2030) |
| SPP | — | `spp-t1h` **SKIPPED**; there is no `spp-t1f` key |

**A scenario's *deployment* delta on a FAIL ISO is a delta between two runs that share the defect** —
directionally informative, never a forecast of GW. Four of the six ISOs are on that footing, and
they include every ISO in the §4 nuclear column except NYISO and NEISO.

### 10.3 MISO is the one ISO outside the §2.1b `complete` block

`frontend/data/backcast/calibration-complete.json` `complete` = **{CAISO, ERCOT, NEISO, NYISO, PJM}**;
`final` = **{}** (no ISO has ever spent a locked-test year). MISO is absent. **It changes nothing
this campaign did** — every leg is `mode="forecast"` over 2026–2030, inside the T1-F window, needing
no grant and claiming none. It does mean **MISO's Stage-B path is closed on leg (a) as well as leg
(b)**. Disclosed, not argued.

### 10.4 SPP — outside the total, and the reason has changed

**Correction to the record.** The desk's r#19 note ("SPP is a seventh ISO but has no scenario base
YAML") was true when written and is **stale at HEAD**: `configs/scenarios/spp_scenario_base_2026_2030.yaml`
and `..._2026_2050.yaml` both exist, landed 2026-09-07 by SPP-38 (`a31c9ef0`). SPP is nevertheless
outside this campaign and outside the `six-ISO modeled system` sum for three current reasons: it is
**not in `configs/scenario_campaign_matrix.yaml`**, it has **no registered forecast run** (only a
`spp-2021-2025-realized-t1h-spp60` hindcast sidecar), and its **FC-1 is SKIPPED**. The `isos_missing`
column of `campaign_emissions_system.csv` names it in every row. One line, as owed — but the correct
line.

### 10.5 Duals are not recoverable from the committed artifacts of half the footprint

`clean_region_duals` and the RPS/clean row duals are written **only** to the gitignored cached year
bundle and the solver log. Under ruling **S16**'s shard split each shard's `results/<ISO>/<key>/`
lived in its own container, so those containers took the duals with them.

| ISO | committed `duals.json` | consequence |
|---|---|---|
| **ERCOT · CAISO · MISO** | **yes, one per case (11 / 8 / 13)** | every dual-limbed gate scored **on the dual** |
| **NEISO** | no file, but per-year duals recorded in the FINDING's own tables | scored on the recorded values |
| **NYISO** | **none** | **G7's dual half scored on the escape IDENTITY** (`escape = V − eligible`, reproduced to the printed digit in every voluntary leg-year) — the regime is proven, the dual scalar is not read |
| **PJM** | **none** | **G4, G7, G10's dual half and G12's read-out half are UNSCORABLE** — 4 of 13 gates. G4's regime is supported by the volumes (target unmet by 208.967 → 564.746 TWh); the $50 value is inferred |

**This is sound, and it is not what the gates say.** A gate written as "the dual equals the ACP
exactly" and scored as "the escape volume equals the deficit exactly" is testing the **regime**, not
the **price**. The two coincide whenever the row escapes, which is why the substitution is defensible
here — and they do **not** coincide when the row binds interior, which is exactly the case (§4.2)
where NYISO's and PJM's unread duals would have mattered most. **Routed** (§12 item 3).

### 10.6 Coverage gaps carried, not absorbed

- **PJM has no Stage-A carbon reading.** `CARB-LO` / `CARB-MID` / `CARB-HI` were never solved
  (15 solve-years); `CARB-MID+LOAD-HI` carries the load axis by construction and cannot separate
  them. Predictions P-1…P-8 are UNSCORABLE on PJM.
- **The carbon axis is measured on two ISOs.** Only ERCOT and MISO carry the full `CARB-*` ladder;
  CAISO / NYISO / NEISO killed theirs at phase 0 on a **proven LP-input identity** (their RGGI
  trajectory dominates every RFF path in every year — NYISO's is 23.64 → 30.98 $/t against
  `CARB-HI`'s $30.00 at 2030, so Δ = **exactly 0.000000 $/t**). That is a *correct* kill, not a gap,
  and it says nothing about whether carbon pricing works in those ISOs — they are **already** carbon
  priced at 2.1–6.7× the `mid` path.
- **ERCOT's clean rows credit dumped energy.** ~4.9 TWh/yr of curtailed wind and solar is dispatched
  into the Dump column at ε cost and credited by the CES and voluntary rows. Every credited/escape
  **volume** on ERCOT is overstated by that amount; no CO2 level moves. Routed by the ERCOT lane.

---

## 11. Cost — the D-5 input from the policy half

| ISO | legs | solve-years | LP | source |
|---|---|---|---|---|
| MISO | 13 | 65 | **8.498 h** (7.844 min/solve-year) | MISO §6 |
| PJM | **11** | 55 | **≈8.19 h** for the first ten; the `CES-P60` leg was the closing session's only solve | PJM §0.1, §0.3 |
| CAISO | 8 | 40 | **4.21 h** (4.12 min/solve-year, Stage-A legs) | CAISO §0.1, §6 |
| NYISO | 10 | 50 | **183.7 min** case LP **+ 64.3 min** on the one Stage-B leg | NYISO header |
| NEISO | 10 | 50 | **147.4 min** (2.95 avg, 3.69 max min/solve-year) | NEISO §6 |
| ERCOT | 11 | 55 | **86.6 min** across four containers, peak RSS 4.20 GB | ERCOT §6 |
| **total** | **63 solved** | **315** | **≈28.9 h** (the PJM `CES-P60` leg is not separately timed) | |

**The one cost signal worth carrying into Stage B: a binding mass-cap row costs 14.6 min/solve-year
against 1.05–3.09 for every other arm** — 49 % of NEISO's entire lane LP on one of ten legs. Budget
`CAP-STATE-TIGHT` at ~5× a normal leg.

---

## Appendix A — `CAP-STATE-TIGHT`, carried as **STAGE-B SEED** evidence only (ruling S17)

**Out of Stage A.** Under owner ruling **S17** (2026-09-07, desk card D-13) the case leaves the
§3.5 Stage-A set. Its already-registered legs (NEISO, NYISO, CAISO) **stay registered** and PJM's
solved leg stays on disk; none is un-registered. It is **excluded from every headline, delta table
and plan §5.1 row above**, and appears only here. **Ruling S12's 80 % budget slope is NOT withdrawn**
— only the stage moved.

**Why the owner moved it, in one line:** NEISO refused a charter-ordered kill and was right. The case
the charter said would be byte-identical to REF **binds in all five years and is a policy LOOSENING**,
because on a program ISO the mass-cap row **replaces** a live RGGI price adder rather than stacking
on it, and the cap's own dual is *below* the adder it displaced.

| ISO | measured content | reading |
|---|---|---|
| **CAISO** | permits **+6.27 / +12.86 / +16.51 Mt** more leakage-inclusive CO2 than REF in 2028–2030; builds **zero** CCS where REF builds 8.9 GW; prices at **$4,975/t**; sheds **12.2 TWh** | confirms NEISO's basis and exceeds it |
| **NEISO** | binds all five years; **+2.9 to +13.9 Mt** looser; dual 12.23 → 8.26 $/t against the 26.05 → 34.15 $/t RGGI adder it replaces | the finding that produced S17 |
| **NYISO** | +9.297 Mt at 2030 vs REF | same mechanism |
| **PJM** | **measurably INERT** — max \|ΔCO2\| over 2027–2030 is **0.0070 Mt (0.002 %)**; 2026 byte-identical to REF in every trajectory field | the loosening mechanism **cannot** operate on PJM: its RGGI `price_adder` resolves to **0.0** in every REF year, so the row can only tighten or do nothing |
| **MISO · ERCOT** | never in scope | `CAP_AND_TRADE_PROGRAMS.get("MISO")` is `None`; ERCOT resolves to no program |

**The Stage-B question this seeds:** a price-vs-quantity comparison at **full horizon**, where the
declining budget has room to bite, and with the RGGI-replacement semantics made explicit before the
solve rather than discovered in it. Cost: ~5× a normal leg (§11).

---

## 12. Routed to SCN-DESK — this lane owns none of these files

This lane does not edit `docs/handoffs/scenario-desk-ledger-2026-09.md`, any other lane's FINDING,
`src/`, `scripts/`, `configs/`, `tests/`, `frontend/`, or any mechanism-matrix shard (the six policy
lanes stamped their own cells; nothing is re-stamped here).

1. **D-15 / S19 — the CCS retrofit seam is now a six-ISO measurement, not a NYISO one.**
   `ccs.py:475-476` never reads `clean_attribute_price_by_fuel`, so a CES **target** row cannot
   reach the retrofit screen. Measured `+0.0 MW` on **five** ISOs (§5). Already routed to the capx
   director; this memo raises its evidential weight and asks that the fix's A/B name the five-ISO
   zero as its pre-registered target.
2. **The 3 GW/yr retrofit cap is the binding constraint on the whole CES premium axis** and the
   campaign identifies **no elasticity** outside NYISO (§6). If the CES demand curve is a Stage-B
   question, the **cap** is the parameter to vary. Not a re-level of §3.5.
3. **Duals must be committed beside every scenario leg.** MISO / CAISO / ERCOT committed a
   `duals.json`; NEISO / NYISO / PJM did not, and four PJM gates are permanently UNSCORABLE as a
   result (§10.5). One line in the registration path would close it for every future campaign — and
   it matters precisely where a row binds interior, which §4.2 shows is where the reading is hardest.
4. **PJM's carbon axis is unmeasured** — three legs, 15 solve-years, never solved (§10.6).
5. **`CES-P60` is a five-ISO leg by design.** The record should say so; "registered on all six ISOs"
   is not accurate and ERCOT was never owed one (§1.3).
6. **The SPP line in the desk record is stale** — the base YAMLs exist at HEAD (§10.4).
7. **The `ces-p60` NYISO sidecar's `meta.set_overrides` reads `null`** where it should record
   `federal_ces_premium_usd_per_mwh=60.0`; the run is still self-describing through `meta.case`, its
   own key and both `full_horizon_summary.json` and `run_config.json`. Reported by NYISO against
   interest; carried here so it is not lost.
8. **ERCOT's dump-crediting defect** overstates every credited/escape **volume** on ERCOT by
   ~4.9 TWh/yr (§10.6). Routed by the ERCOT lane; unresolved.

---

## 13. Files this lane wrote

| file | status |
|---|---|
| `docs/handoffs/FINDING-scenario-campaign-2026-09-07.md` | this memo — the plan §3 WS-5 Stage C deliverable |
| `results/scn-campaign-policy-2026-09-06/_rollup/{campaign_emissions_by_iso,campaign_emissions_system,campaign_delta_table}.csv` | generated by `collate_scenario_campaign.py`, unmodified |
| `results/scn-campaign-policy-2026-09-06/_rollup/campaign_report.md` | generated by the same tool |
| `results/scn-campaign-policy-2026-09-06/_rollup/PROVENANCE.md` | written by this lane |
| `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §5.1 (four policy columns) + §9 ledger line | edited by this lane, last commit |

**Zero LP. Zero solves. Zero registrations. Zero defaults. Zero markers. No `src/`, `scripts/`,
`configs/`, `tests/`, `frontend/` or mechanism-matrix file touched.**
