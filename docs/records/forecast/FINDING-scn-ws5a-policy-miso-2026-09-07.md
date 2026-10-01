# FINDING — SCN-WS5A-POLICY-MISO: the Stage A-POLICY case set, all thirteen legs scored

**Lane** SCN-WS5A-POLICY-MISO (COORDINATOR under ruling **S16**) · **Model** Opus
(`claude-opus-5`, rule 27 `[R-PUSH]`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-miso-close-ro5izu` · **Data profile** `miso` · **Campaign**
`scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` · **THE PIN**
`bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **PRECOMMIT**
`PRECOMMIT-scn-ws5a-policy-miso-2026-09-07.md` (+ ADDENDUM A) · **Predecessors**
`FINDING-scn-ws5a-resolve-miso-2026-09-06.md` (the re-solved REF at THE PIN),
`FINDING-scn-ws5a-load-miso-2026-09-06.md` (the REF's caveats),
`FINDING-scn-ws1b-2026-09-06.md` §4 (the leakage duty).

**ZERO LP IN THIS SESSION.** Every number below is read from a committed artifact — the
thirteen legs' `full_horizon_summary.json` / `duals.json` / `run_config.json`, the six shard
report groups' absolute CSV columns, the committed REF and LOAD-HI legs at THE PIN, and this
lane's own phase-0 JSON. Instrument:
`docs/handoffs/scn-ws5a-policy-miso/score_gates_final_2026-09-07.py` →
`gate-scores-final-2026-09-07.json`. The pre-solve scorer
(`score_gates_2026-09-07.py`, committed before the legs landed) is left untouched so its
pre-solve form stays on the record.

---

## 0. Bottom line

1. **ALL THIRTEEN LEGS LANDED AT THE PIN AND ARE REGISTERED ON `main`.** 13/13 carry
   `git.basis_sha = bdfb3095e9fa…`, `dirty: false`, **0 changed files**, five solve-years
   each, and a `cache_key` **identical to the one this lane pre-registered before any
   solve**. 65 solve-years, 8.50 h of LP, zero re-solves, zero cache hits.
   MISO is the first ISO in the footprint to complete the full set.

2. **GATES: 12 PASS, 1 FAIL, G8 N/A-VACUOUS, G9 REPORTED, G10–G12 N/A.** The single FAIL is
   **G1a on `ALL-CLEAN` alone** (ΔCO2 −0.0008 Mt, Δ`lw_price` −0.001 $/MWh against
   `LOAD-HI` 2026) and it is a **pre-registration defect, not a model defect**: `ALL-CLEAN`
   carries a live federal-CES target row and a present-but-slack voluntary row in 2026, so
   its 2026 LP was never the same LP as `LOAD-HI`'s, and the miss sits **13× below this
   campaign's own measured LP reproducibility floor** (§3.2). No arm was killed by a gate.

3. **THE S15 BRACKET IS CLOSED, AND THE ANSWER IS AN INTERVAL: MISO'S CES ENTRY THRESHOLD IS
   `(30, 50]` $/MWh.** `CES-P10` / `P20` / `P30` produce **exactly zero** incremental entry;
   `CES-T80` (target row, dual = ACP $50.0000) and `CES-P60` (premium $60) each build
   **+1,000.0 MW of nuclear in 2030**, as does `ALL-CLEAN`. G-B1 clears and the leg **moves
   something** — so MISO does *not* reproduce NEISO's "clears the mask and still moves
   nothing" null on entry (§7).

4. **MISO DOES REPRODUCE THE NEISO NULL ON VRE, EXACTLY AND UNIVERSALLY.** `vre_mw` is
   **identical to its own baseline in all thirteen legs and all five years**, and
   `builds_renew_mw` is identical to REF's `0 / 0 / 0 / 5,650.2 / 4,349.8 MW` in every leg —
   including at $60/MWh, and including in the **four of six zones where the measured RPS
   credit is 0.0 and the mask does not exist at all**. A CES premium never builds a MW of
   wind or solar on MISO at any level tested (§4, §7).

5. **THE MASK WAS NEVER THE BINDING CONSTRAINT, AND THAT IS THE LANE'S SHARPEST RESULT.**
   Two measured statements, and the second corrects the premise this lane was issued with
   (§7.1, verified independently against the code): the entry screen's RPS leg **is** fuel-gated
   to `{wind, solar}` (`new_entry.py:1190–1197`, `:1474–1483`), so **nuclear — the only tech
   that ever entered — carries no RPS mask in any zone**, and with MISO's clean-tier duals
   measured 0.0 and its legacy EAC 0.0 its REF attribute is **0.00 everywhere, always**; $10
   beats nothing and it still built nothing until $50. And for wind and solar, ADDENDUM A's
   zonal census is **CONFIRMED** by the measured region duals (MN 0 / MI 30 / WI 0 / IL 0→30 /
   MO 0), so `rps_credit_for_zone` is **structurally 0.0 in MISO-West, MISO-Plains,
   MISO-Indiana and MISO-South** — 60 % of 2030 ISO demand, MISO-South alone 26 % — and not one
   MW of VRE was built there either, at any level up to $60. The threshold is set by the
   **candidate's own delivered economics**, not by `STATE_RPS_ACP["MISO"]`.

6. **THE CES PREMIUM DOES REACH DEPLOYMENT — THROUGH THE CCS RETROFIT SCREEN, AT $10, AND AT
   THE 3 GW/yr CAP.** Every premium arm converts **+2,663 / +2,714 / +3,000.0 MW/yr** of
   gas-CC to `gas_cc_ccs` (2028/29/30), against REF's 334.5 / 283.7 / 0. That is the whole of
   the ladder's **−20.4 Mt** CO2 move at 2030, it is **flat in the premium** ($10 and $60
   within 16 MW of each other), and the 2030 increment is the cap to the tenth of a MW. The
   mechanism is that the premium enters the **dispatch marginal cost**
   (`policy/eac.py::apply_eac_to_mc` → `effective_unit_eac_prices`, `gas_cc_ccs` at the 0.95
   capture fraction), not the attribute `max()` — so it moves the screen's `mc_cost` operand
   directly (§4.3).

7. **THE TWO CES INSTRUMENTS HIT TWO DIFFERENT SEAMS, AND THEY ARE ADDITIVE AND SEPARABLE.**
   A **premium** reaches dispatch + retrofit and nothing else; a **target** row's dual reaches
   entry and nothing else. Measured at 2030: `CES-P60 − CES-P30 = −3.9996 Mt` against
   `CES-T80 = −4.0250 Mt` — the nuclear channel, recovered to 0.6 %, from two arms that share
   no configuration. A model in which one instrument is a proxy for the other would not do
   this.

8. **THE RETIREMENT SCREEN NEVER MOVED. AT ALL.** `retire_mw` is **byte-identical to the
   baseline in 65 of 65 arm-years**. The PRECOMMIT's P-8 named retirement as the CES premium's
   primary channel; that is a **clean MISS** and is scored as one (§5).

9. **CARBON IS LIVE AND RIGHT-SIGNED, AND `CARB-MID+LOAD-HI` MISSED ITS BAND BY 16 Mt IN THE
   HELPFUL DIRECTION.** ΔCO2 at 2030: **−23.22 / −27.24 / −34.29 Mt** at $8 / $15 / $30/t, with
   `lw_price` **+4.77 / +9.14 / +18.85 $/MWh`. The load-paired arm lands at **459.906 Mt**
   against a predicted `[476, 481]` — carbon at $15/t claws back **22.71 Mt of a 72.42 Mt load
   increase (31 %)**, not the predicted 2–7 Mt. **The honest headline survives the miss**: a mid
   carbon price still does **not** hold MISO's CO2 flat under data-centre growth (459.906 vs
   REF's 410.201, still **+49.70 Mt**).

10. **`import_co2_mt_reported` = 0.0000 Mt IN EVERY LEG-YEAR** (G-E3). MISO's committed topology
    carries no import node and no `import` fuel row appears in any of the thirteen legs, so
    every CO2 number in this document is a complete basis and the WS-1b §4 leakage duty is met
    trivially rather than by argument. **This is the one ISO where "in-ISO CO2" and "total CO2"
    cannot diverge**, which is exactly what NEISO's sign reversal makes worth stating.

11. **`CAP_AND_TRADE_PROGRAMS.get("MISO")` is `None`** (`config/capacity_market.py:154` — the
    registry's keys are exactly `{CAISO, NYISO, NEISO, PJM}`), so `resolve_carbon_program`
    early-returns `None` (`policy/cap_and_trade.py:260–262`) in every year for REF and for any
    cap case alike; `CAP-STATE-TIGHT` was never in this lane's chartered set, is out of Stage A
    under ruling **S17** / card D-13, was never solved, and nothing further is owed on it.

12. **MISO is the only ISO outside the §2.1b `complete` marker.** It changes nothing this lane
    did — every leg is `mode="forecast"` over 2026–2030, inside the five-solve-year T1-F window,
    needing no grant and claiming none — but it is stated in §8 so a reader of the synthesis is
    not surprised.

---

## 1. Phase 0 as committed — nothing was killed, and the one crossing is razor-thin

**Reproduced from the PRECOMMIT, not re-derived.** Instruments
`docs/handoffs/scn-ws5a-policy-miso/phase0-miso-2026-09-07.{py,json}` and
`rps-region-census-2026-09-07.{py,json}`, both committed before the first solve.

### 1.1 Cases killed at phase 0: **NONE in the chartered set; ONE out-of-scope case proven inert**

| case | verdict | the identity or regime that decided it |
|---|---|---|
| the twelve chartered cases | **ALL SURVIVE** | MISO kills none. `CARB-*` are LIVE (no state program, so ruling **S2**'s `max(RFF path, program trajectory)` reduces to the path alone); `CES-*` are live on both the premium and target rows; `VOL-*` bind. |
| **`VOL-MID`** | **SURVIVES — the ERCOT kill does NOT generalise** | Slack 2026–28 (+42.58 / +24.70 / **+6.65** TWh), **binds 2029 (−0.70 TWh) and 2030 (−6.07 TWh)**. On ERCOT the same arm was slack by ≥ 36 TWh in all five years and was killed on a proven identity. The 2029 crossing is **0.6 % of `G`** — the thinnest anywhere in the campaign. |
| **`CES-P60`** | **ADDED** (ruling S15) | `--set federal_ces_premium_usd_per_mwh=60.0`, key `e5fb002f78c0c681`. G-B1 computed pre-solve: attr 60.00 (57.00 for `gas_cc_ccs`) against an exact ≤ 30.00 upper bound on REF's attribute. |
| **`CAP-STATE-TIGHT`** | **KILLED — proven LP-identical to REF, and OUT OF SCOPE** | `CAP_AND_TRADE_PROGRAMS.get("MISO")` is `None` → `resolve_carbon_program` early-returns `None` **before** `mass_cap_enabled` is read, for BOTH REF and the cap case, in all five years. The cache key moves (`32584ac5c0133d89`) because the fields are set; **no LP input differs**. Never in this lane's chartered set; out of Stage A under **S17**. Not solved. |

### 1.2 The voluntary regime table, as pre-registered — and 20/20 confirmed by the duals

`V(ISO, y) = s_base·w_ISO·E_nonDC + f_commit·E_DC` on the runner's own demand chain;
`G` = wind + solar as dispatched in the paired committed baseline. Measured `s_base` 0.08,
`w_ISO` 1.0 (MISO's `VOLUNTARY_BASELINE_ISO_WEIGHT` is `None` ⇒ 1.0), `f_commit` 0.5 / 1.0.

| arm | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `VOL-MID` slack `G − V` (TWh) | +42.58 | +24.70 | +6.65 | **−0.70** | **−6.07** |
| `VOL-HI` / `CES-P20+VOL-HI` | +38.28 | +2.86 | **−32.73** | **−57.62** | **−80.53** |
| `ALL-CLEAN` (vs `G_LOAD-HI`) | +35.23 | **−14.14** | **−63.92** | **−103.26** | **−140.91** |

**Every one of these twenty regime calls is confirmed by the measured VOLUNTARY dual** (§3,
G7): the dual is `−0.0` exactly wherever phase 0 said slack and the arm's own WTP ceiling
exactly wherever phase 0 said binding, including at the 0.70 TWh crossing. Phase 0 predicted
the LP's dual regime with no LP.

### 1.3 The RPS-region census (ADDENDUM A), as committed — and confirmed post-solve

MISO's RPS row is **five regions with five different eligible geographies**; MISO-South is in
**no** RPS region's and no clean-tier region's eligible set. Predicted per-zone credit and
measured (from every leg's `duals.json` `rps_region_duals`, region order `[MN, MI, WI, IL, MO]`):

| zone | ADDENDUM A predicted | **measured, all 13 legs** | 2030 demand |
|---|---|---|---|
| MISO-East | 30 | **30.0, all five years** (MI) | 221.54 TWh |
| MISO-Illinois | 30 | **0.0 in 2026, 30.0 in 2027–2030** (IL) | 61.84 TWh |
| MISO-West / MISO-Plains / MISO-Indiana | 0 | **0.0 in every year** | 130.05 / 123.96 / 122.48 TWh |
| **MISO-South** | **0** | **0.0 in every year** | **228.04 TWh** |

Measured region duals, identical in all thirteen legs: **MN 0.0, MI 30.0, WI 0.0, IL 0.0
(2026) → 30.0 (2027–2030), MO 0.0**; the state clean-tier family `[MN, MI]` is **0.0 in every
leg-year**. The one refinement on the addendum: IL is slack in 2026 at REF-level load and binds
from 2027 (it binds already in 2026 under LOAD-HI-level load, visible in `CARB-MID+LOAD-HI` and
`ALL-CLEAN`). So **five of six zones are unmasked in 2026 and four of six from 2027**.

*REF itself carries no `duals.json` (the load campaign's slim set predates this lane's
`extract_duals.py`), so REF's own per-zone vector is inferred, not measured: all thirteen arms —
including `VOL-MID`/`VOL-HI`, whose mechanism cannot touch the RPS row and whose dispatch is
REF's to within the degeneracy floor — report the identical vector. Stated as an inference with
its basis rather than as a measurement.*

---

## 2. Per-case deltas vs the paired committed baseline

Baseline: **REF** (`results/scn-campaign-load-2026-09-06-r2/MISO/REF/`, key
`f1b3caa22b3f14ff`) for eleven arms; **LOAD-HI** (key `9688b06c1b0a5a54`) for
`CARB-MID+LOAD-HI` and `ALL-CLEAN`. Both were re-solved at THE PIN by SCN-WS5A-RESOLVE-MISO,
so rule 29(b) form 4 is valid **by construction** — control and arms share a base commit and
the drift window between them is empty. No control solve was earned or spent.

**Baseline levels.** REF `co2_mt` 368.5353 / 371.1727 / 381.2997 / 387.9419 / 410.2013;
`lw_price` 44.599 / 53.787 / 91.967 / 90.727 / 206.363; `clean_share` 0.2828 / 0.2679 /
0.2563 / 0.2579 / 0.2545; unserved 111.6 / 228.9 / 698.7 / 506.2 / 2,824.2 GWh;
`rps_dual` 30.0 in 5 of 5. LOAD-HI `co2_mt` 387.0428 / 406.8978 / 432.7259 / 455.1277 /
482.6176; `lw_price` 59.632 / 106.334 / 301.077 / 473.619 / 1,073.910; unserved 299.1 /
1,269.7 / 5,668.3 / 12,934.3 / 42,391.1 GWh. **`import_co2_mt_reported` = 0.0000 Mt in both,
every year.**

### 2.1 The carbon axis

| case | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| `CARB-LO` ($0/2/4/6/8/t) | ΔCO2 Mt | **+0.0000** | −3.4888 | −9.9208 | −16.8479 | **−23.2246** |
| | `import_co2` Mt | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | Δ`lw_price` | +0.000 | +1.293 | +2.422 | +3.639 | +4.765 |
| `CARB-MID` ($0/3.75/7.5/11.25/15) | ΔCO2 Mt | **+0.0000** | −6.3569 | −13.2351 | −21.4920 | **−27.2409** |
| | `import_co2` Mt | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | Δ`lw_price` | +0.000 | +2.445 | +4.552 | +6.880 | +9.135 |
| `CARB-HI` ($0/7.5/15/22.5/30) | ΔCO2 Mt | **+0.0000** | −12.1898 | −19.1092 | −28.8706 | **−34.2914** |
| | `import_co2` Mt | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | Δ`lw_price` | +0.000 | +4.979 | +9.416 | +14.329 | +18.845 |
| `CARB-MID+LOAD-HI` (vs LOAD-HI) | ΔCO2 Mt | **+0.0000** | −3.7292 | −11.3928 | −17.8154 | **−22.7118** |
| | `import_co2` Mt | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | Δ`lw_price` | +0.000 | +2.310 | +4.468 | +6.594 | +5.233 |

**2026 is EXACTLY 0.0000 / 0.000 in all four** — the RFF paths' 2026 knot is $0 in `low`,
`mid` and `high` alike, so the LP is literally the same LP and HiGHS reproduces it bit for
bit (G1a). Monotone in the price in every year 2027–2030 on both CO2 and price.
`unserved_mwh` moves 0.0 GWh in every carbon arm-year (G6).

**Price levels carry G2's disclosure**: the 2030 `lw_price` level is DISCLOSURE-ONLY (REF
$206.36 with I14 WARN and 361 shortage hours, scarcity-set) and 2028–2029 levels carry the I14
WARN; the **deltas** above are campaign-grade, and 2026–2027 price deltas are campaign-grade
on the level too.

### 2.2 The CES premium ladder, `CES-T80`, and the S15 bracketing leg

| case | attr $/MWh | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|---|
| `CES-P10` | 10 | ΔCO2 Mt | +0.0112 | +0.0108 | −5.8731 | −12.5714 | **−20.4302** |
| | | `import_co2` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | | Δ`lw_price` | +0.000 | −0.004 | −0.028 | −0.068 | −0.014 |
| `CES-P20` | 20 | ΔCO2 Mt | −0.0086 | +0.0027 | −5.9483 | −12.5958 | **−20.4507** |
| | | `import_co2` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `CES-P30` | 30 | ΔCO2 Mt | −0.0086 | +0.0008 | −5.9411 | −12.6143 | **−20.4656** |
| | | `import_co2` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **`CES-P60`** | **60** | ΔCO2 Mt | −0.0090 | +0.0122 | −5.9713 | −12.6446 | **−24.4652** |
| | | `import_co2` | *n/a†* | *n/a†* | *n/a†* | *n/a†* | *n/a†* |
| `CES-T80` | 50 (ACP dual) | ΔCO2 Mt | +0.0105 | −0.0041 | −0.2132 | −0.2709 | **−4.0250** |
| | | `import_co2` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | | Δ`lw_price` | −0.002 | −0.003 | −0.031 | −0.035 | +0.093 |

† `CES-P60` sits in **no shard report group by design** (PRECOMMIT §2: its `--set` leg's
`members[case]` key would collide with the real `CES-P30`), so it has no
`miso_headline_deltas.csv` row and no `import_co2_mt_reported` column. It is nonetheless
**0.0000 by construction and by census**: MISO's committed topology has no import node, and
the union of `generation_by_fuel_mwh` keys over **all thirteen legs and all 65 leg-years** is
exactly `{biomass, coal, gas_cc, gas_cc_ccs, gas_ct, gas_st, hydro, nuclear, oil, solar,
wind}` — no `import` row exists anywhere. Stated as a construction argument, not as a
measured cell.

**The ladder's CO2 move is flat in the premium and is entirely the CCS retrofit.** At 2030
the spread across $10 → $30 is **0.035 Mt on a −20.4 Mt move** (0.2 %). The $60 rung adds
**−4.0 Mt more**, and that increment is the nuclear entry, not more retrofit (§4.3, §7.3).

### 2.3 The voluntary axis

| case | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| `VOL-MID` | ΔCO2 Mt | +0.0105 | −0.0043 | −0.0156 | −0.0051 | **−0.0022** |
| | `import_co2` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | Δ`lw_price` | −0.002 | −0.003 | −0.003 | +0.001 | −0.002 |
| | VOLUNTARY dual | −0.0 | −0.0 | −0.0 | **4.5000** | **4.5000** |
| `VOL-HI` | ΔCO2 Mt | +0.0105 | −0.0043 | −0.0157 | −0.0051 | **−0.0023** |
| | `import_co2` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | VOLUNTARY dual | −0.0 | −0.0 | **7.0000** | **7.0000** | **7.0000** |

**The voluntary row on MISO is an ESCAPE-ONLY instrument, exactly as pre-registered.** The
largest CO2 move either arm produces in any year is **0.0157 Mt (38 ppm)** and the largest
price move is **0.003 $/MWh** — both inside the campaign's own LP reproducibility floor
(§3.2). `VOL-MID` and `VOL-HI` differ from each other by at most **0.0001 Mt** in any year
despite carrying volumes that differ by up to 74 TWh, because both escape. Every build,
retirement, retrofit and capacity row is identical to REF's in both arms and all five years.

### 2.4 The two combined legs — BOTH nettings, side by side (ruling S11)

Reported per ruling **S11**: **counts-toward is the headline**, additional is beside it,
with the CES dual under each. Card **D-6** is OPEN and neither is asserted as the answer.

#### `CES-P20+VOL-HI` (premium $20 + voluntary `high`)

| netting | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| **counts-toward (HEADLINE, as built)** | ΔCO2 Mt | +0.0105 | −0.0055 | −5.9628 | −12.6270 | **−20.4517** |
| — two independent rows, each satisfied on the same credited MWh (FFR-6B §6.4) | `import_co2` Mt | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | `clean_share` | 0.2828 | 0.2679 | 0.2811 | 0.3064 | 0.3265 |
| | VOLUNTARY dual | −0.0 | −0.0 | 7.0000 | 7.0000 | 7.0000 |
| | FEDERAL_CES dual | *n/a — premium, no target row* | | | | |
| **additional (beside it)** | voluntary volume `V` TWh | 65.28 | 100.71 | 136.30 | 172.07 | 208.04 |
| — the same MWh may not serve both rows; the extra escape is `V` at the ceiling | implied extra escape TWh | 65.28 | 100.71 | 136.30 | 172.07 | 208.04 |
| | priced at | $7.00/MWh (the arm's own WTP ceiling; **no ACP applies — a PREMIUM has no target row**) | | | | |

**On this arm D-6 has no dispatch content, and the reason is measured rather than argued.**
`CES-P20+VOL-HI` is **indistinguishable from `CES-P20`** to within 0.031 Mt in every year, and
from `VOL-HI` by −20.45 Mt at 2030 — i.e. the whole arm is its premium half. Under the
counts-toward netting the voluntary row is satisfied entirely by escape; under the additional
netting it is satisfied entirely by *more* escape. Neither reaches a dispatch or a build
decision, so the two nettings differ in accounting only, by a volume of escape and its price,
and by nothing physical.

#### `ALL-CLEAN` (carbon `mid` + CES target 0.55/0.80/1.00 at ACP $50 + voluntary `high` + growth high + DC high; baseline **LOAD-HI**)

| netting | | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| **counts-toward (HEADLINE, as built)** | ΔCO2 Mt | −0.0008 | −3.7238 | −11.5445 | −18.0354 | **−26.7594** |
| | `co2_mt` absolute | 387.0420 | 403.1740 | 421.1814 | 437.0923 | **455.8582** |
| | `import_co2` Mt | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| | `clean_share` | 0.2686 | 0.2480 | 0.2552 | 0.2717 | 0.2977 |
| | **FEDERAL_CES dual** | **50.0000** | **50.0000** | **50.0000** | **50.0000** | **50.0000** |
| | **VOLUNTARY dual** | **−0.0** | **7.0000** | **7.0000** | **7.0000** | **7.0000** |
| **additional (beside it)** | voluntary volume `V` TWh | 68.34 | 117.71 | 167.49 | 217.71 | 268.42 |
| — `federal_credited − V ≥ target(y)·D`; implied extra escape `max(0, target·D + V − credited)` | implied extra escape TWh (lower bound = `V`) | 68.34 | 117.71 | 167.49 | 217.71 | 268.42 |
| | priced at | **ACP $50.00/MWh** on the federal limb, $7.00/MWh WTP ceiling on the voluntary limb | | | | |

**`ALL-CLEAN` is the one arm where D-6 has real content**, because both a federal CES target
row and a voluntary row credit the same clean MWh, and **both escape in every year the target
is unmet**. Under counts-toward the federal escape is `target(y)·D − credited`; under
additional it grows by the whole of `V` (68.3 → 268.4 TWh), which at the ACP is a payment
difference of **$3.4 bn (2026) to $13.4 bn (2030)** on an identical physical dispatch. **The
two nettings do not differ by one MWh of generation, one MW of capacity, or one gram of CO2 on
MISO** — they differ only in what the compliance bill is. That is the cleanest statement of
D-6's stakes the campaign can make, and it is offered as evidence, not as a recommendation.

---

## 3. Gate verdicts

### 3.1 The table

| gate | verdict | evidence |
|---|---|---|
| **G1** resolved-input premise reproduces at THE PIN | **PASS** | 13/13: `basis_sha = bdfb3095e9fa…`, `dirty: false`, 0 changed files, `solved_years = [2026…2030]`, and `cache_key` **identical to the pre-registered key** in every case (`e5fb002f78c0c681` for the `--set` leg, whose `set_overrides` records `{"federal_ces_premium_usd_per_mwh": 60.0}` — rule 24's registered channel). The resolved carbon table reproduces the YAML's declared ERCOT/PJM/MISO table to the cent. |
| **G1a** 2026 identity to the arm's own load baseline | **FAIL — on `ALL-CLEAN` alone** | `CARB-LO/MID/HI` vs REF and `CARB-MID+LOAD-HI` vs LOAD-HI: **0.0000 Mt / 0.000 $/MWh, exactly**. `ALL-CLEAN` vs LOAD-HI: **−0.0008 Mt / −0.001 $/MWh** against a 5e-4 threshold. See §3.2 — a pre-registration defect, reported at full magnitude, not repaired. |
| **G2** REF-side precondition | **PASS** | REF FAIL set exactly `{I3, I7, I12}`, WARN exactly `{I14}` — as WS-5A measured. Unserved 111.6 → 2,824.2 GWh (0.02 % → 0.32 % of load); `lw_price` $44.60 → $206.36. Consequence as declared: CO2, merit-order and dual results campaign-grade in all five years; **the 2030 price LEVEL is disclosure-only** and 2028–29 levels carry I14. |
| **G3** footprint confinement | **PASS** | *Carbon arms:* every zero-carbon class Δ = **0.000000 TWh** in all four arms and all five years; `emissions_by_fuel["import"]` absent everywhere. *CES/voluntary arms:* wind, solar and hydro Δ = **0.000000 TWh** in every arm-year; the only nuclear energy move anywhere (+7.83024 TWh, 2030) occurs exactly where a **+1,000.0 MW nuclear build** is recorded in the same arm-year. |
| **G4** `CES-T80` dual identity | **PASS** | FEDERAL_CES dual = **50.0000 exactly** in all five years, in **both** `CES-T80` and `ALL-CLEAN`. The target is unmet in every year (REF's credited share 0.2828 → 0.2545, *falling*, against a target rising 0.55 → 0.80), so the escape regime is the whole window and no interior dual appears. |
| **G5** no non-target load-bearing invariant flips PASS → FAIL | **PASS 13/13** | Every arm's FAIL set is exactly `{I3, I7, I12}` = its baseline's; **zero new FAILs anywhere**. I14 WARN carried identically. |
| **G6** unserved must not rise where the mechanism cannot raise demand | **PASS 11/11** | Δunserved ≤ 0 in every year of all eleven REF-based arms (max rise **0.0 GWh**); `CES-P30` / `CES-P60` / `CES-T80` each *fall* 1.1 GWh at 2030. Measured at the **0.1 GWh** resolution of the I3 detail string, which is the committed artifact carrying per-year unserved. Not binding on `CARB-MID+LOAD-HI` / `ALL-CLEAN`, which raise load by construction — reported anyway: `CARB-MID+LOAD-HI` 0.0 in every year; `ALL-CLEAN` **+5.7 GWh at 2029** (0.04 % of LOAD-HI's 12,934.3) and **−11.6 GWh at 2030**. |
| **G7** voluntary dual bounded, per arm | **PASS 20/20 arm-years** | Dual = `−0.0` **exactly** wherever phase 0 said slack and the arm's **own** ceiling **exactly** where it binds: `VOL-MID` $4.5000 in 2029–30 only, `VOL-HI` / `CES-P20+VOL-HI` $7.0000 in 2028–30, `ALL-CLEAN` $7.0000 in 2027–30. Bounded per arm from that arm's own resolved path, never from the charter's single $4.5 literal (ruling **S9**). |
| **G8** curtailment before thermal | **N/A — VACUOUS** | Declared vacuous **before the solve** and confirmed after: `curtailment_twh` = **0.0000 in every leg-year with a report row** (12 legs × 5 years), so there is no curtailed eligible MWh to recover and the antecedent is empty. **Never scored as a PASS.** Its substance is carried by §2.3: no thermal response either. |
| **G9** both nettings on `CES-P20+VOL-HI` and `ALL-CLEAN` | **REPORTED** (ruling S11) | §2.4 — counts-toward as headline, additional beside it, the CES dual under each. |
| **G-B1** the S15 mask is actually cleared | **PASS** | 60.00 (57.00 for `gas_cc_ccs` at the 0.95 capture fraction) strictly exceeds an exact ≤ 30.00 upper bound on REF's attribute in every eligible tech-zone-year. **Strengthened by measurement**: in four of six zones the measured RPS credit is **0.0**, so the margin there is the full **$60.00**, not $30.00. |
| **G-B2** `CES-P60` footprint as a CES case | **PASS** | Eligible-class energy share moves 0.2828 → 0.3394 (2030); `gas_cc_ccs` capacity +2,665.1 / +5,378.7 / +8,378.7 MW; nuclear +7.83024 TWh in the single year carrying a +1,000.0 MW nuclear build; wind, solar and hydro **0.000000 TWh** in every year. |
| **G-B3** `CES-P60` collateral | **PASS** | FAIL set `{I3, I7, I12}` = REF's; zero new FAILs; I14 WARN identical. |
| **G10–G12** `CAP-STATE-TIGHT` | **N/A** | Out of MISO's scope and out of Stage A (**S17**, card D-13); `CAP_AND_TRADE_PROGRAMS.get("MISO")` is `None`; never solved. Nothing owed. |

**Score: 12 PASS · 1 FAIL · 1 N/A-vacuous · 1 REPORTED · 3 N/A. No gate killed an arm.**

### 3.2 The G1a FAIL, at full magnitude, and why it is a pre-registration defect

**What was asserted.** PRECOMMIT §6.2 P-1: *"2026 is bit-identical to REF in all five
carbon-bearing arms … (`CARB-MID+LOAD-HI` and `ALL-CLEAN` are excepted: their load half moves
2026 too, so for them G1a asserts identity to `LOAD-HI`'s 2026 …)"*. The reasoning was that
the 2026 RFF knot is $0 on every path, so the carbon axis cannot move 2026.

**What was measured.** Four of the five arms are identical **to the last digit** — `ΔCO2 =
0.0000000`, `Δlw_price = 0.000`. `ALL-CLEAN` is **−0.0008 Mt** (387.0420 against LOAD-HI's
387.0428) and **−0.001 $/MWh**. Against the pre-registered 5e-4 tolerance, that is a **FAIL**,
and it is recorded as one.

**Why the assertion was wrong.** The carbon reasoning was sound and `ALL-CLEAN` is not
a carbon-only arm: it carries a **federal CES target row that binds at $50.0000 in 2026**
(measured) and a voluntary row that is present-but-slack in 2026. Its 2026 LP therefore has
rows and columns `LOAD-HI`'s does not, and the two are not the same problem. G1a should never
have been asserted for it. The exception clause in the PRECOMMIT corrected the **baseline** for
`ALL-CLEAN` and forgot to correct the **premise**.

**The magnitude, in context — the campaign's own LP reproducibility floor.** `VOL-MID` and
`VOL-HI` are the cleanest available probe: phase 0 proves their voluntary row is **slack** in
2026, so their 2026 LP differs from REF's only by a row and a column carrying a zero dual, and
their optimum must be REF's. Measured: **ΔCO2 = +0.0105 Mt** and **Δ`lw_price` = 0.002**. That
is this campaign's degeneracy floor — where an added-but-inert row shifts HiGHS to a different
vertex among ties. **`ALL-CLEAN`'s −0.0008 Mt is 13× BELOW that floor** (and the whole CES-arm
2026 spread, ±0.011 Mt, sits on it). The four exact zeros are exact precisely because a $0
carbon knot changes **no** row, **no** column and **no** coefficient.

**What is NOT claimed.** The gate is not re-scored, the threshold is not moved, and the FAIL is
not explained away — a 5e-4 threshold set an order of magnitude below the LP's own
reproducibility is a defect in the gate, and the honest statement is that G1a as written cannot
be met by any arm that adds a row, whatever the model does. Routed to SCN-DESK (§8 item 3).

---

## 4. The deployment response vs REF — retirements, entry, retrofits

REF's own deployment (identical in LOAD-HI, to the MW, in every year): builds `planned` 55.1
(2027), `planned` 714.7 + `reserve_backstop` 2,049.4 (2028), `economic` 4,349.8 +
`reserve_backstop` 4,049.4 (2029), `economic` 650.2 + `reserve_backstop` 10,000.0 (2030);
`builds_renew_mw` 0 / 0 / 0 / 5,650.2 / 4,349.8; retirements coal 2,368.0 / 3,210.0 / 1,426.2 /
790.7 MW and nuclear 617.0 MW (2030); retrofit `gas_cc_ccs` 334.46 (2028) + 283.67 (2029) MW.

### 4.1 Retirements — **ZERO response, in 65 of 65 arm-years**

`retire_mw` is **byte-identical to the paired baseline in every arm and every year**, and so is
every per-tech retirement row in the shard evolution tables (coal 2,368.0 / 3,210.0 / 1,426.2 /
790.7; nuclear 617.0; `gas_ct`, `gas_st`, oil, biomass all unchanged). No carbon price up to
$30/t, no CES premium up to $60/MWh, no $50 target-row dual and no voluntary row changed a
single retirement decision on MISO over 2026–2030.

### 4.2 Entry — **ZERO VRE at any level; +1,000.0 MW of nuclear at $50 and above**

| | `vre_mw` Δ | `builds_renew_mw` Δ | `builds_thermal_mw` Δ | nuclear capacity Δ |
|---|---|---|---|---|
| **all 13 legs, 2026–2029** | **0.0** | **0.0** | **0.0** | **0.0** |
| all 13 legs, 2030 | **0.0** | **0.0** | 0.0 except below | 0.0 except below |
| `CES-T80` 2030 | 0.0 | 0.0 | **+1,000.0** | **+1,000.0** |
| `CES-P60` 2030 | 0.0 | 0.0 | **+1,000.0** | **+1,000.0** |
| `ALL-CLEAN` 2030 | 0.0 | 0.0 | **+1,000.0** | **+1,000.0** |

The nuclear unit runs at **7.8302 TWh** (89.4 % CF) and displaces `gas_ct` **1:1** (−7.8149 /
−7.8473 / −7.6131 TWh in the three arms). It appears in `builds_by_source` as `economic`
650.2 → 1,650.2 MW — the economic entry screen, not the reserve backstop, which is pinned at
10,000.0 MW in every leg. **Its zone is not determinable from the committed slim artifacts**
and is not asserted here.

**No carbon arm builds anything new**, at any price up to $30/t: `CARB-LO/MID/HI` and
`CARB-MID+LOAD-HI` have `builds_by_source` identical to their baselines in all five years.

### 4.3 Retrofits — **the CES premium's real channel, and it saturates at the cap**

Incremental `gas_cc_ccs` conversion, MW per year, against the paired baseline:

| arm | 2026 | 2027 | 2028 | 2029 | 2030 | cumulative 2030 |
|---|---|---|---|---|---|---|
| `CARB-LO` | 0 | 0 | +2,629.0 | +2,697.8 | **+3,000.0** | +8,326.8 |
| `CARB-MID` | 0 | 0 | +2,638.3 | +2,686.0 | **+3,000.0** | +8,324.3 |
| `CARB-HI` | 0 | 0 | +2,659.6 | +2,713.6 | **+3,000.0** | +8,373.2 |
| `CES-P10` | 0 | 0 | +2,662.7 | +2,715.7 | **+3,000.0** | +8,378.4 |
| `CES-P20` / `CES-P20+VOL-HI` | 0 | 0 | +2,663.7 | +2,714.8 | **+3,000.0** | +8,378.5 |
| `CES-P30` | 0 | 0 | +2,663.1 | +2,713.2 | **+3,000.0** | +8,376.3 |
| **`CES-P60`** | 0 | 0 | +2,665.1 | +2,713.6 | **+3,000.0** | +8,378.7 |
| `CARB-MID+LOAD-HI` | 0 | 0 | +2,663.9 | +2,612.2 | **+3,000.0** | +8,276.1 |
| `ALL-CLEAN` | 0 | 0 | +2,663.9 | +2,612.2 | **+3,000.0** | +8,276.1 |
| **`CES-T80`** | 0 | 0 | **0.0** | **0.0** | **0.0** | **0.0** |
| **`VOL-MID` / `VOL-HI`** | 0 | 0 | **0.0** | **0.0** | **0.0** | **0.0** |

Four facts, in order of importance:

1. **A $10/MWh CES premium converts as much gas-CC to CCS as a $30/t carbon price** —
   +8,378.4 MW against `CARB-HI`'s +8,373.2 MW by 2030. The channel is saturated at both ends.
2. **The 2030 increment is exactly 3,000.0 MW in every armed arm** — the 3 GW/yr/ISO retrofit
   cap, to the tenth of a MW. 2028–29 are 2,612–2,716 MW, i.e. within 10 % of the cap and
   limited by the eligible cohort (≥15 yr remaining life), not by price.
3. **The response is flat in the price by design of the seam, not by coincidence.** $10 and $60
   differ by **16.0 MW** cumulative at 2030 (0.19 %); `low` and `high` carbon differ by 46.4 MW
   (0.55 %).
4. **`CES-T80` and the voluntary arms produce ZERO retrofit**, despite `CES-T80` carrying a
   **$50.0000** dual — five times the premium that saturates the screen in `CES-P10`.

**The mechanism, traced.** The CES **premium** is subtracted from the **dispatch marginal
cost** of every eligible unit — `policy/eac.py::apply_eac_to_mc` → `federal_ces.
effective_unit_eac_prices`, with `gas_cc_ccs` credited at
`federal_ces_ccs_capture_fraction` = 0.95 under `clean_capture`. The retrofit screen values the
CCS uplift through `mc_cost` from `prior_results`, so a per-MWh credit on retrofit output
raises the uplift directly. A **target** row is a clean-tier constraint whose dual reaches the
capacity screens' attribute fold and **never enters `mc`** — which is exactly why `CES-T80`
moves entry and not the retrofit, and the premium ladder moves the retrofit and not entry.
**The two CES instruments are not substitutes at any level; they act on different seams.**

### 4.4 The two channels are additive and separable — measured

At 2030, `CES-P60 − CES-P30 = −3.9996 Mt` (the difference between a leg that builds the
nuclear unit and one that does not, holding the retrofit fixed at the cap) against `CES-T80 =
−4.0250 Mt` (the nuclear unit alone, with no retrofit at all). **The nuclear channel is
recovered to 0.6 % from two arms that share no configuration field.** The retrofit channel is
likewise recoverable: `CES-P30` −20.4656 Mt is 67.5 TWh of gas-CC → `gas_cc_ccs` at a ~0.315
t/MWh rate difference, ≈ −21.3 Mt, the residual being the small coal and `gas_ct` moves in the
same table. This is a strong internal-consistency result and is offered as such.

---

## 5. The PRECOMMIT's predictions, scored at full magnitude

**Fifteen numbered predictions (P-1 … P-15, with P-4 scored as its two independent limbs)
plus ADDENDUM A's P-7b — seventeen scored rows. Score: 7 CORRECT · 4 PARTIAL · 1 SPLIT ·
4 WRONG · 1 DONE** (P-13 is a reporting duty, not a prediction). Every miss is stated with its
magnitude and its cause; none is repaired, re-scoped or averaged away.

| # | prediction (abridged) | verdict | measured |
|---|---|---|---|
| **P-1** | 2026 bit-identical in all five carbon-bearing arms | **PARTIAL — 4/5** | `CARB-LO/MID/HI` and `CARB-MID+LOAD-HI` **exact to the last digit**; `ALL-CLEAN` −0.0008 Mt / −0.001 $/MWh. G1a FAIL, §3.2. |
| **P-2** | CO2 falls and price rises monotonically REF → LO → MID → HI, 2027–2030; 2026 flat | **CORRECT** | Monotone on both metrics in all four years, all three rungs. 2026 flat exactly. |
| **P-3** | `CARB-MID` 2027 ΔCO2 in **[−8.0, −5.5] Mt**, Δprice in **[+1.8, +3.3]** — *"the prediction most likely to miss"* | **CORRECT, both bands** | **−6.3569 Mt** and **+2.445 $/MWh**, both comfortably interior. The band was set from WS-1b-r2's −6.6414 Mt at a different REF level; the transfer held. |
| **P-4a** | `CARB-LO` 2027 in **[−4.5, −2.5] Mt**; `CARB-HI` 2027 in **[−15, −10] Mt** | **CORRECT, 2/2** | **−3.4888** and **−12.1898 Mt**. |
| **P-4b** | *"more than 2× MID's, not less"* — super-linear, asserted deliberately against ERCOT's opposite curvature | **WRONG** | HI/MID = **1.917×** at 2× the price — **sub-linear**, the same sign as ERCOT's P-5. LO/MID = 0.549× at 0.533×, marginally super-linear at the bottom, so the ladder is mildly **concave** overall. The stated reason (a wide coal band crossing between $3.75 and $7.50) is not what MISO's fleet does. |
| **P-5** | coal→gas-CC substitution at ≈1:1, every zero-carbon class 0.0000, import 0.0000 | **PARTIAL** | The **confinement half is EXACT** in all five years (G3: zero-carbon 0.000000 TWh, no import row exists). The **mechanism half holds only in 2027** (`CARB-MID`: coal −10.022, gas_cc +8.163, `gas_ct` +0.649, `gas_st` +0.512, biomass +0.580 TWh). From 2028 the dominant move is the **CCS retrofit** (gas_cc −60.9 → `gas_cc_ccs` +67.0 TWh at 2030), 6–9× the coal move. P-5 characterised the 2027 mechanism as the whole mechanism. |
| **P-6** | `gas_cc_ccs` grows with the carbon price from 2028; `CARB-HI` 2030 strictly above REF's 4.6908 TWh; a **discontinuous two-plant step** | **PARTIAL** | Sign and strict inequality **CORRECT** (`CARB-HI` 2030 = 72.10 TWh) and monotone in the price on energy (`gas_cc_ccs` Δ at 2030: **+65.1964 / +66.9559 / +67.4064 TWh** for LO / MID / HI). The **two-plant step is WRONG**: MISO converted **8.3 GW**, not a two-unit cohort, and the limiter is the **3 GW/yr cap**, not plant granularity. The two-plant reading was REF's cohort at carbon $0, mistaken for the eligible cohort under a price. |
| **P-7** | `CES-P10/P20/P30` show no new VRE entry; `builds_renew_mw` identical to REF's `0/0/0/5,650.2/4,349.8` | **CORRECT on the outcome — and stronger than claimed; its stated REASON was wrong** | **Exactly identical** in all three arms and all five years, **and in all thirteen legs**, `CES-P60` included. But P-7 argued the arms are masked because "the fold is `max(...)` with **no fuel gate**", and §7.1's correction shows the screening folds **are** gated to `{wind, solar}`. The prediction was right about VRE for a reason that happens to survive (VRE is exactly what the gate admits, and MI/IL do escape at $30) and wrong as a general statement of the fold. |
| **P-7b** (ADDENDUM A) | per-zone RPS credit **30 in MISO-East + MISO-Illinois, 0 in the other four**; *therefore* `CES-P10/P20/P30` **DO** reach entry in four of six zones and *"P-7 as written is then WRONG"* | **SPLIT — census CONFIRMED, inference FALSIFIED** | The census is **right**, to the dual: MN 0 / MI 30 / WI 0 / IL 0→30 / MO 0, so four of six zones carry a **0.0** credit (five in 2026 — the one refinement: IL is slack in 2026 at REF-level load, not binding as predicted). The **inference is wrong**: the CES row *does* reach the entry fold in those zones (attr 0 → 10/20/30) and **still builds nothing**. P-7 stands, and stands for a reason neither P-7 nor P-7b gave — see §7.2. |
| **P-8** | divergence from REF appears **first in `retire_mw`** and in the `gas_cc_ccs` cohort, not in `builds_renew_mw`; the premium reaches a unit's going-forward margin through the retirement screen's fuel-gated RPS leg | **WRONG on its named channel** | `retire_mw` **identical in 65 of 65 arm-years** — the premium never reached the retirement screen at all. The `gas_cc_ccs` half is right and is in fact the **entire** channel (§4.3). The mechanism is not the retirement screen's fuel gate; it is the premium entering **dispatch `mc`** via `apply_eac_to_mc`. |
| **P-9** | `CES-T80` in the escape regime every year, dual = ACP **$50.0000 exactly**; and T80 is **the first CES case that is not entry-masked** | **CORRECT, both halves** | Dual **50.0000 exactly** in 5/5 years, in `CES-T80` and `ALL-CLEAN` alike; `CES-T80` is the **lowest-attribute arm in the campaign that produces entry** (+1,000.0 MW nuclear, 2030). |
| **P-10** (G7) | the exact voluntary dual sequence, per arm, per year — including 0 → $4.5 at the 0.70 TWh crossing | **CORRECT, 20/20 arm-years** | Every dual is `−0.0` or the arm's own ceiling, **exactly** as written, in every year of all four voluntary arms. |
| **P-11** | \|ΔCO2\| < 0.5 Mt and \|Δprice\| < 0.5 in `VOL-MID` / `VOL-HI` / **`CES-P20+VOL-HI`** | **PARTIAL — 2/3, scope error** | `VOL-MID` max 0.0156 Mt, `VOL-HI` 0.0157, prices ≤ 0.003 — **CORRECT**. `CES-P20+VOL-HI` is **−12.63 / −20.45 Mt** at 2029/2030, a **40× breach**. The cause is the arm's **premium** half, not its voluntary row: `CES-P20+VOL-HI` minus `CES-P20` is ≤ **0.031 Mt** in every year, inside the degeneracy floor. P-11's *substance* (the voluntary row moves nothing) holds in all three arms; its *scope* wrongly included a premium-bearing arm. |
| **P-12** (G8) | G8 vacuous — REF curtailment 0.0000 in every year | **CORRECT** | 0.0000 in **every leg-year with a report row**; scored N/A, never a PASS. |
| **P-13** (G9) | both nettings reported side by side; D-6 left OPEN | **DONE** | §2.4. |
| **P-14** | `CARB-MID+LOAD-HI` 2030 in **[476, 481] Mt**; carbon claws back **2–7 Mt** of a 72 Mt load increase; `unserved` not below LOAD-HI's | **WRONG on the band — the campaign's largest miss** | **459.906 Mt**, i.e. **16.1 Mt below the band's floor**; carbon claws back **22.71 Mt (31 %)**, not 2–7 Mt (3–10 %). The band assumed carbon's only channel was the 2027-style merit-order substitution and did not anticipate the retrofit screen converting 8.28 GW. `unserved` **CORRECT** — 0.0 GWh in every year. **The headline the prediction was built to deliver survives the miss and is restated: a mid carbon price does NOT hold MISO's CO2 flat under data-centre growth** — 459.906 Mt is still **+49.70 Mt** over REF. |
| **P-15** | `CES-P20+VOL-HI` **indistinguishable from `VOL-HI`**; the premium's only content on the retirement side | **WRONG** | It is indistinguishable from **`CES-P20`** (≤ 0.031 Mt in every year) and differs from `VOL-HI` by **−20.45 Mt** at 2030. The argument — that a $20 premium and a $7 ceiling both sit under the $30 RPS dual so neither reaches deployment — fails because **the premium does not pass through the attribute `max()` on the dispatch/retrofit path at all**. |

**What the misses have in common, stated once.** P-4b, P-5, P-6, P-8, P-14 and P-15 are six
different consequences of **one** wrong model of the CES premium and the carbon price: that
both act only through the attribute fold and the merit order. Both in fact act on the
**retrofit** screen through dispatch `mc`, a channel this lane's phase 0 did not enumerate.
That single omission is worth more than the six individual corrections, and it is the lane's
principal methodological lesson.

---

## 6. Cost — wall and peak RSS per solve-year (the plan D-5 cost table's input)

**13 legs · 65 solve-years · 30,593.1 s = 8.498 h of LP · mean 7.844 min/solve-year ·
peak RSS 10,009.1 MB on a 15 GB box.** Seven shard containers, one solve at a time inside a
shard, years always sequential (rule 12 `[R-PARALLEL]`).

| leg | wall s | peak RSS MB | 2026 | 2027 | 2028 | 2029 | 2030 (s / MB) |
|---|---|---|---|---|---|---|---|
| `CARB-LO` | 1,461.9 | 9,990.2 | 485 / 9,990 | 161 / 8,380 | 201 / 8,218 | 260 / 9,043 | 354 / 9,367 |
| `CARB-MID` | 1,422.9 | 9,904.4 | 472 / 9,904 | 163 / 8,014 | 216 / 8,171 | 266 / 9,000 | 306 / 9,357 |
| `CARB-HI` | 1,580.8 | 9,937.7 | 547 / 9,938 | 179 / 8,389 | 217 / 8,336 | 288 / 8,942 | 349 / 9,416 |
| `CARB-MID+LOAD-HI` | 1,588.8 | 9,848.1 | 476 / 9,848 | 175 / 8,375 | 228 / 8,218 | 308 / 8,954 | 402 / 9,283 |
| `CES-P10` | 1,906.3 | 9,946.7 | 631 / 9,947 | 200 / 8,405 | 278 / 8,378 | 388 / 9,062 | 409 / 9,405 |
| `CES-P20` | 1,833.6 | 9,895.0 | 588 / 9,895 | 202 / 8,389 | 263 / 8,289 | 361 / 8,930 | 420 / 9,335 |
| `CES-P30` | 1,644.6 | 9,958.4 | 535 / 9,958 | 186 / 8,390 | 228 / 8,396 | 310 / 9,004 | 386 / 9,355 |
| **`CES-P60`** | 2,388.9 | 9,984.3 | 762 / 9,984 | 253 / 8,322 | 380 / 8,433 | 434 / 8,963 | 560 / 9,414 |
| **`CES-T80`** | **4,137.9** | 9,991.9 | 481 / 9,992 | 543 / 8,008 | 978 / 7,970 | **1,368** / 8,821 | 767 / 9,329 |
| `VOL-MID` | 1,853.8 | 9,971.8 | 627 / 9,972 | 199 / 8,461 | 265 / 8,378 | 327 / 9,039 | 436 / 9,454 |
| `VOL-HI` | 1,716.6 | 9,887.7 | 497 / 9,888 | 204 / 8,341 | 262 / 8,342 | 333 / 8,973 | 420 / 9,373 |
| `CES-P20+VOL-HI` | 2,343.3 | **10,009.1** | 787 / 10,009 | 255 / 8,470 | 334 / 8,334 | 446 / 9,075 | 521 / 9,432 |
| **`ALL-CLEAN`** | **6,713.7** | 9,996.0 | 721 / 9,996 | 867 / 8,411 | **1,651** / 8,314 | **2,436** / 8,999 | 1,039 / 9,421 |

**Three cost facts for D-5.** (a) **A binding CES target row is the single most expensive
mechanism in the case set** — `CES-T80` costs **2.83×** the mean leg and `ALL-CLEAN` **4.59×**,
while the premium ladder costs 1.10–1.42× and the carbon ladder 0.94–1.05×. The escape-regime
clean-tier row is what does it; the premium, which is a marginal-cost adder, is nearly free.
(b) **2026 is the most expensive year in 11 of 13 legs** (fixed setup lands in it) and is where
peak RSS occurs in **13 of 13** — memory is set by the first solve, not by the fleet's growth.
(c) **The 10.0 GB peak is 67 % of a 15 GB box**, so the PRECOMMIT's "never two MISO solves in
one container" holds with no margin to spare; a shard width of 2 with sequential solves was
correct and a width of 3 would not have changed it.

---

## 7. S15 — the threshold result, reported BESIDE the masked ladder

### 7.1 The mask, as measured

`STATE_RPS_ACP["MISO"]` = **30.0**, the footprint's lowest (NYISO 40 / PJM 45 / CAISO 50 /
NEISO 50), and the ledger scalar `rps_dual` is **30.0 in 5 of 5 years in REF and in every one
of the thirteen legs** — the escape regime, unmoved by any arm. MISO's legacy EAC is 0.0 for
every tech and the state clean-tier family escapes at the **same** $30
(`policy/clean_tiers.py:139`), so on the ISO-wide scalar the S15 reading is: **P10 and P20 are
strictly dominated, P30 ties exactly, T80's $50 clears by $20, P60's $60 clears by $30.**

**CORRECTION, carried at full magnitude — the S15 premise this lane was issued with, and which
its own PRECOMMIT §7.1/§7.3 repeats, is WRONG ABOUT THE FUEL GATE.** The charter and this
lane's PRECOMMIT both state that the entry fold applies the RPS leg to every tech with **no
fuel gate**, citing `new_entry.py:~1132–1143`. Read at the line level that is not what the code
does, and this session **verified it independently on MISO's own read** after
`FINDING-scn-ws5a-policy-neiso-2026-09-06-ADDENDUM-2.md` (landed on `main` at `563b6b37`,
merged in `#5574`) raised it:

- The two **screening** folds — `capacity_evolution/new_entry.py:1190–1197` and `:1474–1483` —
  both compute `rps_for_tech = rps_credit_for_zone(...) if tech in _RENEWABLE_NEW_FUELS else
  **0.0**`, and `_RENEWABLE_NEW_FUELS` is `frozenset({"wind", "solar"})` (`:121`).
- The cited `~1132–1143` fold is inside `_zone_revenue`, nested in `_choose_vre_zone`
  (`:1107`), whose **only** call site is `:1437`, inside `if tech in _RENEWABLE_NEW_FUELS:`
  (`:1434`). It is a VRE-only siting helper, so the absence of a gate there is **vacuous** — it
  never sees a non-VRE tech to fail to gate.

**What this changes for MISO — and it makes the finding stronger, not weaker.** The mask
covers **wind and solar only**. For nuclear and the seven other CES-eligible techs
`rps_for_tech` is **0.0 in every zone and every year**, and MISO's state clean-tier duals
`[MN, MI]` are **measured 0.0 in every leg-year**, with a 0.0 legacy EAC — so **nuclear's REF
attribute is 0.00 everywhere, always. The mask never touched the tech that actually built.** A
$10 premium already gives nuclear an attribute of 10.00 against nothing, in all six zones, from
2026 — and it built nothing until $50.

**What this does NOT change: any number in this document.** Every measurement, dual, delta and
gate verdict stands exactly as reported. G-B1's pre-solve `≤ 30.00` upper bound on REF's
attribute remains a **valid bound** and the gate still clears — the true margin is simply
larger than the $30 claimed (the full **$60** for nuclear and every non-VRE eligible tech, and
for wind/solar in the four zones where the RPS credit is measured 0.0). The zonal census of
§1.3 is untouched and still governs, but its scope is now exact: **it governs wind and solar**,
which is precisely the tech class that built nothing at any level.

### 7.2 The ladder — and the null it produces

| arm | attribute | clears $30? | Δ`vre_mw` | Δ`builds_renew_mw` | Δnuclear MW | Δretrofit MW (2030 cum.) |
|---|---|---|---|---|---|---|
| `CES-P10` | 10 (premium) | no | **0.0 ×5 yr** | **0.0 ×5 yr** | **0.0** | +8,378.4 |
| `CES-P20` | 20 (premium) | no | **0.0 ×5 yr** | **0.0 ×5 yr** | **0.0** | +8,378.5 |
| `CES-P30` | 30 (premium) | **ties** | **0.0 ×5 yr** | **0.0 ×5 yr** | **0.0** | +8,376.3 |
| **`CES-T80`** | **50 (ACP dual)** | **+$20** | **0.0 ×5 yr** | **0.0 ×5 yr** | **+1,000.0** (2030) | 0.0 |
| **`CES-P60`** | **60 (premium)** | **+$30** | **0.0 ×5 yr** | **0.0 ×5 yr** | **+1,000.0** (2030) | +8,378.7 |

**Does MISO reproduce NEISO's null? Plainly: on VRE, yes and universally. On entry as a whole,
no — MISO breaks it, at $50.**

- **NEISO measured** its own ladder producing exactly zero incremental entry with `vre_mw`
  identical in REF and all eight non-cap arms.
- **MISO reproduces the `vre_mw` half exactly and extends it**: `vre_mw` is identical to the
  baseline in **all thirteen legs and all five years** — the carbon arms, the whole premium
  ladder, both voluntary arms, `CES-T80`, `ALL-CLEAN` and `CES-P60` at $60/MWh. **No CES
  premium, at any level tested up to $60, builds one MW of wind or solar on MISO.**
- **MISO breaks the "exactly zero incremental entry" half**: at an attribute of **$50** the
  entry screen builds **+1,000.0 MW of nuclear** in 2030, in `CES-T80`, `CES-P60` and
  `ALL-CLEAN` alike. **NEISO's null was not a model that cannot respond; it was a model whose
  ladder stopped $20 short.**
- **And MISO breaks the null a second way, at $10, on a channel NEISO's ladder also exercised**:
  every premium arm converts 8.4 GW of gas-CC to CCS (§4.3). NEISO reported the same
  retrofit-driven asymmetry; MISO adds that it is **flat in the premium** and **capped**.

### 7.3 The threshold, and the finding that the mask was never the binding constraint

**The bracket closes as an interval: MISO's CES entry threshold is `(30, 50]` $/MWh.** No
attribute at or below $30 builds anything; $50 and $60 both build the same 1,000 MW; the
campaign has no rung between, and none is added — a level chosen to bisect an interval this
lane measured would be exactly the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids.

**G-B1 clears, and the leg moves something — so this is a threshold result, not the reportable
null the charter anticipated.** But the deeper reading is the one the zonal census makes
possible, and it is the lane's headline:

> **The mask does not reach the tech that built, and it does not reach four of six zones for
> the techs it does cover — and the ladder built nothing in either case.** Two independent
> statements, both measured:
>
> 1. **For nuclear — the only tech that ever entered — there is no mask anywhere.** The
>    screening folds gate the RPS leg to `{wind, solar}` (`new_entry.py:1190–1197`,
>    `:1474–1483`), MISO's clean-tier duals are 0.0 in every leg-year and its legacy EAC is
>    0.0, so nuclear's REF attribute is **0.00 in all six zones and all five years**. A $10
>    premium gives it **10.00 against nothing** — and it built nothing until **$50**.
> 2. **For wind and solar, the mask covers at most two of six zones.**
>    `rps_credit_for_zone` is **structurally 0.0** in MISO-West, MISO-Plains, MISO-Indiana and
>    MISO-South (§1.3) — MN, WI and MO are all slack at a dual of 0, and MISO-South is
>    admitted by no region at all. There REF's attribute is **0.00**, $10 raises it to
>    **10.00** and $60 to **60.00** — the **full $60**, not $30. MISO-South alone is **26 % of
>    2030 ISO demand**. **Not one MW of wind or solar was built in any of them, at any level
>    up to $60.**

So the S15 hypothesis — that the state ACP masks the federal premium at the entry screen — is
**true on the ISO-wide scalar and false as an explanation of MISO's behaviour**. The binding
constraint is the **candidate's own delivered economics**: at $50 the nuclear candidate clears
and wind and solar still do not, in a zone where they face no attribute competition
whatsoever. **MISO is the thinnest mask in the footprint, it is thin enough to disappear
entirely in 60 % of the ISO's demand, and the ladder is still masked-looking below $50 for a
reason that has nothing to do with the mask.** Any campaign-level statement of the form "the
CES premium is masked by the state ACP" must be scoped to the ISO-wide scalar and cannot be
carried to MISO's zonal reality.

---

## 8. Routed to SCN-DESK — not executed, outside this lane's regions

1. **THE CES PREMIUM AND THE CES TARGET ACT ON DIFFERENT SEAMS, AND NO CAMPAIGN DOC SAYS SO.**
   A **premium** enters dispatch `mc` (`policy/eac.py::apply_eac_to_mc` →
   `federal_ces.effective_unit_eac_prices`, `gas_cc_ccs` at the 0.95 capture fraction) and so
   reaches dispatch and the **retrofit** screen, and never the entry attribute fold in a way
   that builds. A **target** row's dual reaches the entry fold and **never** `mc`, so it moves
   entry and produces **zero** retrofit even at $50 — five times the premium that saturates the
   screen. Measured, additive and separable to 0.6 % (§4.4). Plan §2.2 and the §5.1 CES columns
   read as though the two are one instrument at different levels. **This is the single most
   consequential thing this lane found** and it changes how every ISO's CES rows should be
   read.

2. **THE S15 CHARTER'S FUEL-GATE PREMISE IS WRONG, CONFIRMED ON A SECOND ISO.** The charter,
   this lane's issuing prompt and its PRECOMMIT all cite `new_entry.py:~1132–1143` for the claim
   that the entry fold applies the RPS leg with **no fuel gate**. The screening folds
   (`:1190–1197`, `:1474–1483`) gate it on `_RENEWABLE_NEW_FUELS = {wind, solar}` (`:121`); the
   cited lines are inside a VRE-only siting helper whose sole call site is itself VRE-gated
   (`:1434`, `:1437`), so their missing gate is vacuous. NEISO raised this in
   `FINDING-scn-ws5a-policy-neiso-2026-09-06-ADDENDUM-2.md` (`563b6b37`, `#5574`) and **MISO
   verified it independently** (§7.1). It changes no number in any lane, and it makes the
   measured nulls **stronger**: on MISO the tech that actually built carries no mask at all.
   Desk card **D-12** and the ledger §0 r#18 text both rest on the ungated reading and should be
   re-scoped; any ISO whose §5.1 CES-premium cell cites `1132-1143` needs the same correction.

3. **THE S15 MASK QUESTION ALSO NEEDS A ZONAL FORM, NOT AN ISO-WIDE ONE.** MISO's ledger `rps_dual`
   is a **MAX over five regions** (`runner.py:4919`), and the measured per-region duals show
   **three of five regions slack at 0** and one binding only from 2027. Four of six zones —
   60 % of 2030 demand — therefore carry a **zero** attribute alternative and are **not masked
   at any premium**. An ISO whose RPS row is region-partitioned cannot have its mask read off
   the ledger scalar. NYISO (LCR/TSL regions) and PJM are the two most likely to share the
   shape; NEISO's ISO-wide $50 is the case where the scalar *is* the answer.

4. **G1a's THRESHOLD IS BELOW THE CAMPAIGN'S OWN LP REPRODUCIBILITY FLOOR.** The gate asserts a
   5e-4 Mt identity; the measured floor — from arms whose added row is **provably inert** — is
   **1.05e-2 Mt** on CO2 and 2e-3 on price, i.e. **21×** the threshold. Any arm that adds a row
   or a column fails G1a whatever the model does, while an arm that changes only a coefficient
   value to zero passes **exactly**. The gate is well-posed only for the second class. A desk
   restatement should either scope G1a to coefficient-only identities or set its tolerance from
   the measured floor; this lane changed neither and reported the FAIL as written (§3.2).

5. **`VOL-MID` IS NOT THE INERT ARM.** ERCOT killed it as slack in all five years; **MISO's
   binds in 2029–30**, and the 2029 crossing is **0.70 TWh — 0.6 % of `G`**, the thinnest
   crossing in the campaign. Any desk or plan text reading "VOL-MID is the inert arm" must be
   scoped to ERCOT. (Restated from PRECOMMIT §11 item 1; the solve confirmed it — the dual is
   $4.5000 exactly in both years.)

6. **THE VOLUNTARY ROW'S DEPLOYMENT HALF CANNOT BE EXERCISED IN ANY RPS ISO AT THE COMMITTED
   LEVELS.** Its ceiling ($4.5 / $7.0) is below **every** `STATE_RPS_ACP` in the footprint, so
   plan §5.1 criterion 2's *"dual → the existing `max()` screen seam"* is structurally
   unreachable. On MISO it is worse than unreachable: the row escapes in every binding year and
   moves **0.0157 Mt** at most. Belongs beside card **D-3c**. (Restated from PRECOMMIT §11
   item 3, now with MISO's measurement behind it.)

7. **THE S15 MASK HAS A SECOND CEILING.** MISO's *clean-tier* family escapes at
   `STATE_RPS_ACP["MISO"]` too (`policy/clean_tiers.py:139`), so the mask is $30 on **both**
   attribute rows. Measured: the state clean-tier duals `[MN, MI]` are **0.0 in every
   leg-year**, so on MISO the second ceiling is never reached — but a lane reasoning only about
   the RPS row would understate the mask on any ISO with a live clean tier. (PRECOMMIT §11
   item 2.)

8. **`miso-2026-2030-d60-arm` remains stale as a description of HEAD** (+14.7 % energy; I3
   fails in REF where the board key has it passing) — for the capx director.
   (`FINDING-scn-ws5a-resolve-miso-2026-09-06.md` §7 item 3, restated so it is not lost.)

9. **MISO IS THE ONLY ISO OUTSIDE THE §2.1b `complete` MARKER** (the other five hold it).
   **It changed nothing this lane did.** Every leg is `mode="forecast"` over **2026–2030**,
   inside the forecast plan §2.1b five-solve-year T1-F window; **no grant is needed and none
   is claimed**; no backcast year was touched and no marker was read or written (rule 22
   `[R-HOLDOUT]` / R-AZ). Stated here so a reader of the six-ISO synthesis, seeing MISO absent
   from the marker board, does not infer a gap in this lane's authorisation.

10. **A RENDERING REPAIR I MADE IN ANOTHER LANE'S CELLS, DISCLOSED RATHER THAN ROUTED.**
    §5.1 row 3 carried **eight unescaped `|`** inside the CES-premium and Voluntary cells —
    `|ΔP30−ΔP20|/|ΔP20|`, `max(10|20|30, 40, 0)` and `max |Δ|` — which split the row into
    **16 columns instead of 7**, so the whole scorecard table rendered as garbage in both
    the plan and the ledger mirror, and no column-indexed edit could address the row at all.
    I escaped them as `\|` in the same commit: **a rendering repair that changes not one
    character of meaning** (`\|` renders as `|`), with the affected cells' wording, numbers
    and claims untouched. It is disclosed here rather than routed because leaving it would
    have blocked this lane's own duty; the authoring lanes should know their cells were
    reformatted, and a desk convention that literal pipes inside a table cell must be
    escaped would stop the next one.

11. **A LANE'S PHASE 0 SHOULD ENUMERATE `mc`-PATH CONSUMERS, NOT ONLY ATTRIBUTE-FOLD
   CONSUMERS.** Six of this lane's eight non-clean prediction rows (P-4b, P-5, P-6, P-8, P-14, P-15) are
   consequences of one omission: phase 0 traced the CES premium and the carbon price through
   the attribute `max()` and the merit order, and not through `apply_eac_to_mc` into the
   retrofit screen's `mc_cost` operand. A one-line addition to the phase-0 protocol would have
   caught all six before any LP ran, at zero cost.

---

## 9. Files

**Written by this session** (all inside this lane's own regions):

| file | note |
|---|---|
| `docs/handoffs/FINDING-scn-ws5a-policy-miso-2026-09-07.md` | this document |
| `docs/handoffs/scn-ws5a-policy-miso/score_gates_final_2026-09-07.py` | the final gate scorer, zero-LP, committed-artifacts-only |
| `docs/handoffs/scn-ws5a-policy-miso/gate-scores-final-2026-09-07.json` | its output — every gate, every case, every year |
| `docs/handoffs/scn-ws5a-policy-miso/gate-scores-2026-09-07.json` | the output of the **pre-solve scorer run unchanged against the landed legs** — its `.py` was written and committed before any leg existed and is not edited here, so this file is that pre-registered form's verdict on the real numbers, committed as a cross-check on the final scorer |
| `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` | §5.1 rows 3 and 7, MISO cells only, in the Carbon / CES premium / CES target / Voluntary columns — **plus the eight-pipe rendering repair of §8 item 10**, which is not MISO's cell but without which the row does not render |
| `docs/handoffs/scenario-desk-ledger-2026-09.md` | §3 mirror of the same, MISO rows only, with the same rendering repair |
| `docs/codebase-site/data/mechanism-matrix/MISO.js` | four cells appended: `federal_ces_target`, the CES premium row, `carbon_price_path`, `voluntary_clean_demand` (rule 28 `[R-MECH-MATRIX]` duty b) |

**Read, never edited:** every committed leg and bundle, `configs/scenario_campaign_matrix.yaml`,
the MISO base YAML, everything under `src/` and `scripts/`, every other ISO's files and matrix
shard, `score_gates_2026-09-07.py` (left in its pre-solve form), the readiness plan and desk
ledger outside this lane's own rows, `calibration-complete.json`, `program-status.json`,
`ff-verdicts.json` and the entire backcast registry.

**Not done, deliberately:** no solve, no re-solve, no registration change, no default moved, no
`ScenarioConfig` field added, no CI workflow, no year past 2030, no marker read or written, no
backcast artifact touched. **DOF ledger: zero free parameters.** No `authorized_price_tuning`
block — rule 1's carve-out is a backcast offer-curve channel and this is a forecast campaign.
