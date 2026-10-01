# FINDING — SCN-WS5A-POLICY-NYISO: the CES premium is entry-masked at every committed rung and reaches NYISO only through the CCS retrofit, the voluntary row is inert with a 6.4 TWh volume delta, and the S15 bracket buys new nuclear

**Lane** SCN-WS5A-POLICY-NYISO (coordinator) · **Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) ·
**Date** 2026-09-07 · **Branch** `claude/scn-ws5a-policy-nyiso-close-u22igx` · **Data profile** `nyiso` ·
**Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, unmoved · **Charter** SCN-DESK ledger §5
policy charter **v6** (r#17) as amended by **v7 / ruling S16** (r#18 am.1) ·
**Predecessors** `PRECOMMIT-scn-ws5a-policy-nyiso-2026-09-06.md` + **ADDENDUM** + **ADDENDUM 2**,
all three pushed before the legs they predict.

**10 legs solved across 5 owner-authorised shards, 50 solve-years, 183.7 min of case LP + 64.3 min
on the one Stage-B leg. 4 of 13 chartered cases killed at phase 0 on a proven LP identity; 1 leg
added under ruling S15. Nine Stage-A legs, all 14/14 invariants PASS. `CAP-STATE-TIGHT` is
reported in §8 only, per ruling S17.**

**ZERO LP WAS SPENT IN THIS SESSION.** All ten registered legs were verified present on `main`
before anything else (§10); nothing surviving phase 0 is missing, so the one solve the closing
prompt permitted was not needed and was not taken. This document is scoring and records.

---

## 0. Bottom line

1. **THE CES PREMIUM LADDER PRODUCES *EXACTLY ZERO* INCREMENTAL ENTRY AT EVERY COMMITTED RUNG,
   AND NYISO REPRODUCES NEISO'S NULL TO THE MEGAWATT.** `wind_mw` / `solar_mw` / `builds_renew_mw`
   are **identical to REF in `CES-P10`, `CES-P20` and `CES-P30`, in all five years** (2400/1500 →
   3400/3343.4 MW; builds 0.0 / 0.0 / 0.0 / 2843.4 / 0.0). NYISO's state RPS row escapes at its
   **$40/MWh ACP in 5 of 5 years of every arm**, and the entry fold
   `attr = max(effective_eac_price_for_tech, rps_credit_for_zone, clean_credit)`
   (`new_entry.py:1132-1143`) applies that leg with **no fuel gate**, so `max(10|20|30, 40, 0)`
   = 40 = REF's. Pre-registered in **ADDENDUM 2 §3 before the deciding legs ran** (§7).
2. **THE S15 BRACKET BREAKS THE NULL, AND THE THRESHOLD SITS BETWEEN $40 AND $50 — MEASURED, NOT
   INFERRED.** `CES-P60` ($60) and `CES-T80` ($50 ACP) both build **+156.6 MW of solar in 2030**;
   `CES-P60` additionally builds **+500.4 MW of NEW NUCLEAR** (+156.0 MW in 2029, +344.4 in 2030,
   3.326 → 3.826 GW). The masked rungs build **nothing**. So the entry response is a **step
   function of the attribute price with its step inside (40, 50]**, and a second step for nuclear
   inside (50, 60] — a measured threshold ladder where the campaign previously had a null (§7).
3. **THE CES PREMIUM REACHES NYISO ALMOST ENTIRELY THROUGH THE CCS RETROFIT SCREEN, AND THE CES
   *TARGET ROW* CANNOT REACH THAT SCREEN AT ALL.** `gas_cc_ccs` capacity at 2030 goes REF 6,255.9
   → 7,035.5 / 7,731.7 / 7,762.7 / 7,890.3 MW at $10/$20/$30/$60, while `CES-T80`'s $50 ACP leaves
   it at **6,255.9 MW — REF's, to the 0.1 MW, in every year**. The cause is a code seam, not a
   level: `ccs.py:475-476` prices the retrofit's attribute uplift with
   `effective_eac_price_for_unit`, i.e. `max(legacy eac_price_*, federal CES PREMIUM × credit)`,
   and **never reads `clean_attribute_price_by_fuel`** — so a $50 row dual is invisible where a
   $20 premium is not. This is why prediction **P-9 missed badly** (§5) and it is routed (§9).
4. **THE VOLUNTARY ROW IS INERT ON NYISO — AND THIS IS A FAR STRONGER NULL THAN NEISO'S, BECAUSE
   NYISO HAS THE VOLUME CONFOUND NEISO LACKS.** `VOL-MID` and `VOL-HI` carry volumes differing by
   **1.82 → 6.39 TWh** (V = 13.86 → 18.29 vs 15.68 → 24.68 TWh, driven by a real
   `E_DC` of 3.64 → 12.78 TWh) and come back **byte-identical in the headline frame, the by-fuel
   frame and the curtailment frame in all five years**; the only difference anywhere is the
   by-zone CO2 attribution, max |Δ| **2.9e-5 Mt**. Both arms are within **0.0031 Mt** of REF.
   NEISO's identical result had `E_DC` exactly zero and so could not distinguish "the ceiling does
   nothing" from "the volume never moved"; **NYISO moves the volume by 35 % and still gets
   nothing** (§7.3).
5. **NYISO'S CES LADDER IS MONOTONE ON *BOTH* SIDES OF THE LEAKAGE LINE WHERE NEISO'S REVERSED —
   but it reverses somewhere else, at 2028, and in-ISO CO2 there RISES with the premium.**
   2030 leakage-inclusive total: REF 21.978 → 18.796 / 16.358 / 14.874 / **12.136** Mt at
   $10/$20/$30/$60, strictly monotone, with `import_co2_mt_reported` falling 11.075 → 6.477 Mt at
   $60. At **2028** in-ISO CO2 goes 17.1630 (REF) → 17.1597 / **17.1948 / 17.2098 / 17.2478**, i.e.
   three of four rungs are *worse* than REF and the ladder is non-monotone. Small (≤ 0.085 Mt on
   17 Mt) and reported at full magnitude (§2.2).
6. **THE LEAKAGE LINE IS THE CAMPAIGN'S LARGEST AND IT IS NOT A CAVEAT, IT IS THE RESULT.**
   REF's `import_co2_mt_reported` runs **10.45 → 11.07 Mt against an in-ISO 23.69 → 10.90 Mt** —
   **44 % of the in-ISO level at 2026 rising to 102 % at 2030**. Every CO2 number in §2 carries
   its import line beside it. On `CES-P60` at 2030 the import cut (−4.598 Mt) is **88 % as large
   as the in-ISO cut** (−5.244 Mt): a reader given `emissions_mt` alone sees under half the answer.
7. **`CES-T80` EXERCISES BOTH LIMBS OF THE G4 DUAL IDENTITY, AND THE ONE I FLAGGED AS UNCERTAIN IS
   THE ONE THAT LANDED.** The row escapes in 2026–2028 (shortfall 24.27 / 29.60 / 13.26 TWh) and
   **binds exactly in 2029 and 2030** — credited share 0.6333333332 vs target 0.6333330000 and
   0.6611111117 vs 0.6611110000, i.e. the LP drives credited to `target·D` to **5.3e-5 and 1.8e-5
   TWh**. PRECOMMIT §6.4 named 2029/2030 as "the one year I flag as genuinely uncertain" and
   pre-registered that outcome as **G4 passing on its other leg**, which is what it is (§3).
8. **Five of my own pre-registered predictions MISSED and are reported at full magnitude** —
   **P-3, P-7, P-9, P-18** and **P-22** — plus **P-8** as a pre-registered SPLIT. P-15, the one
   the PRECOMMIT itself called "the most reasoned and most likely to miss prediction in the lane",
   **hit to 0.01 Mt in all five years** (§5).
9. **One artifact defect found in my own registration path:** the `ces-p60` sidecar's
   `meta.set_overrides` reads **`null`**, against ADDENDUM 2 §6.3's statement that it would record
   `federal_ces_premium_usd_per_mwh=60.0`. The run is still self-describing (`meta.case: CES-P60`,
   a distinct key `c3013cc6087bd2aa`, and both `full_horizon_summary.json` and `run_config.json`
   carry the override and the resolved 60.0). Reported against interest and routed (§9 item 5).

---

## 1. Phase 0 as committed — NOT re-derived

Everything in this section is quoted from `PRECOMMIT-scn-ws5a-policy-nyiso-2026-09-06.md` and its
two ADDENDUMs, which were pushed before any LP. Nothing here was recomputed for this document, and
nothing here is revised by a result.

### 1.1 Four cases killed on a proven LP-input identity — 20 solve-years never spent

| case | key at THE PIN | the only resolved field that differs | killed against |
|---|---|---|---|
| `CARB-LO` | `68294f45fda64aed` | `carbon_price_path: zero → low` | REF |
| `CARB-MID` | `91d435c848c57fb6` | `carbon_price_path: zero → mid` | REF |
| `CARB-HI` | `3608ca88c0a19d4e` | `carbon_price_path: zero → high` | REF |
| `CARB-MID+LOAD-HI` | `80b8a2ec7406f75d` | `carbon_price_path: zero → mid` | the committed `LOAD-HI` leg |

Under owner ruling **S2**'s floor, `resolved = max(RFF path(y), program trajectory(y))`. NYISO's
RGGI trajectory is **23.6363 / 25.2908 / 27.0612 / 28.9555 / 30.9824 $/tCO2** across 2026–2030 and
dominates every registered path in every year — the closest approach is `CARB-HI` at 2030, $30.00
against $30.98. `carbon_price_path`'s only LP-affecting consumer at the pin is
`policy/carbon.py::resolved_base_trajectory_price`'s `max` (`:187`); everything else is a
docstring, a cache-key registration, or the `carbon_path_below_program_warning` tripwire, which
only warns. **Δ = exactly 0.000000 $/t in every carbon arm in every year** (PRECOMMIT §4.1) — gate
**G1** on the carbon axis, passed before any LP. This is `FINDING-scn-ws1b-2026-09-06.md`'s
"EXACTLY INERT on CAISO/NYISO/NEISO" extended from a single 2027 probe to the whole T1-F window,
and it is why the lane's `CARB-*` legs were killed rather than solved.

**What the kills are NOT evidence of** (PRECOMMIT §4.2, restated because it now governs four of my
thirteen cases): they say a *federal RFF* price of $8–30/t is a no-op where RGGI already charges
$23.64–30.98/t. They say **nothing** about whether carbon pricing works in New York — NYISO is
already carbon-priced at **6.7× (2027) falling to 2.1× (2030)** the `mid` path's own level in the
years that path is non-zero.

### 1.2 The voluntary row survives phase 0 in every arm, and NYISO is ERCOT's structural inverse

V(ISO, y) computed by calling `policy.voluntary_demand.resolve_voluntary_volume` on the demand the
LP is handed (PRECOMMIT §3.1). Eligible generation `G` = wind + solar as dispatched in the paired
committed baseline; NYISO has no offshore-wind or geothermal row in any leg.

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| `E_DC` (DC mid) TWh | 3.641 | 5.925 | 8.209 | 10.493 | 12.777 |
| **V (mid)** TWh | 13.857 | 14.962 | 16.068 | 17.177 | 18.287 |
| **V (high)** TWh | 15.677 | 17.924 | 20.173 | 22.423 | 24.676 |
| **V (high, DC-high — `ALL-CLEAN`)** TWh | 17.677 | 21.148 | 24.627 | 28.114 | 31.611 |
| eligible `G` TWh | 7.314 | 7.314 | 7.314 | 11.892 | 11.892 |

The row **binds in every year of every voluntary arm**, V/G running **1.4× to 3.4×**. The cause is
ruling **S10**: NYISO's clean fleet is hydro (26.2 TWh) and nuclear (27.0 TWh) and the
renewable-only eligible set credits **neither** — so the same convention that makes the row inert
on a wind-and-solar ISO (ERCOT, 197–235 TWh of eligible fleet) makes it bind hard on a
hydro-and-nuclear one, at a *higher* clean share (0.39 vs ERCOT's 0.35).

### 1.3 The WTP ceilings, both committed cells live

`voluntary_wtp_ceiling_usd_per_mwh` resolves `None` on every case, so the resolver takes
`VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`: **$4.50/MWh** on `VOL-MID` (ruling S9's cell) and
**$7.00/MWh** on `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN`. Gate **G7** is bounded per arm at that
arm's own ceiling (the charter v6 correction).

### 1.4 G8's object does not exist on NYISO

REF curtails **exactly 0.0 MWh** of wind and solar in every year (PRECOMMIT §3.4, re-confirmed on
the re-solved REF in ADDENDUM 2 §5). G8 is therefore recorded **N/A with its reason** and replaced
by its degenerate form: **a non-zero Δcurtailment is a finding against the row**.

### 1.5 G-DRIFT (rule 29(b)) — form 4 valid, no control solve earned

RESOLVE's 34-commit classification (`1cc45bb2..bdfb3095`) plus this lane's own
`bdfb3095..origin/main` audit of 18 files / 8 non-merge commits found **no LIVE hunk for a NYISO
forecast leg** (PRECOMMIT §5). D77 and D65-B are LIVE ISO-wide but are *the object of the re-solve,
not a confound*, which is why this lane differences against the `-r2` REF (`f10cc93084b4c0db`) and
never the pre-fix bundle. The four PJM-only mechanisms measured `None`/`False` on the resolved
NYISO config. **The committed re-solved REF and LOAD-HI ARE the control; no control solve was
spent, in this lane or in any shard.**

### 1.6 The S15 mask, measured pre-solve (ADDENDUM 2 §3)

REF's `rps_dual` = **40.0000 in all five years**; `STATE_RPS_ACP["NYISO"]` = 40.0. The resolved
entry fold, identical in all five zones and all five years: REF 40.00, `CES-P10` 40.00, `CES-P20`
40.00, `CES-P30` 40.00, **`CES-P60` 60.00** — **15/15 ladder leg-years masked, 150/150
tech-zone-years identical to REF**, and **+20.00 $/MWh on 50 of 50** eligible tech-zone-years at
$60. **Gate G-B1 cleared pre-solve.** `CES-P60` is the committed `--set` channel
(`--case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0`), key `c3013cc6087bd2aa`, verified by
a full `dataclasses.fields` diff; **$60 is one common level for every ISO**, above the footprint's
highest published ACP ($50), declared ex ante and never swept. **DOF ledger: zero free parameters.**

### 1.7 Gate G13 — PASSED before any case leg

`REF` at `f10cc93084b4c0db` and `LOAD-HI` at `c2ceaefa4afafcda` reproduced their committed
`full_horizon_summary.json` trajectories **exactly** (ADDENDUM 2 §1). Both are controls; neither is
registered by this lane.

### 1.8 Provenance re-verified at close, not assumed

Every one of the twelve committed bundles records `git.dirty: false`, 5/5 solved years and
`error: null`, and **every key matches the pre-declared key in ADDENDUM 2 §2**. Ten record
`basis_sha` = THE PIN exactly. Two do not — `CES-P30` at `37ef8158ba9a` and `LOAD-HI` at
`7411679a6f10` — and both were checked rather than waved through: each is a **descendant of the
pin whose entire diff against it is 7–9 files, all of them documentation or this lane's own
artifacts, with a zero solve-path diff**
(`git diff --name-only bdfb3095 <sha>` lists only `docs/handoffs/PRECOMMIT-…`,
`docs/handoffs/scn-ws5a-policy-nyiso/*` and this campaign's own `REF`/`LOAD-HI` slim files).
That is exactly the ADDENDUM 1 §3.1 convention — "the pin itself or a doc-only descendant with a
zero solve-path diff, and every leg's HEAD guard is the diff itself" — and the key equality is the
independent second proof.

---

## 2. Per-case deltas vs the committed post-D77 REF

**REF is never re-solved.** Its trajectory is the `-r2` bundle at key `f10cc93084b4c0db`; its
headline scalars — including the import line, clean share, curtailment and unserved that the slim
summary does not carry — are the committed
`results/scn-campaign-load-2026-09-06/NYISO/report/nyiso_headline_deltas.csv`, built against
`bundle/meta.json`'s `REF: f10cc93084b4c0db` (ADDENDUM 2 §5).

### 2.0 The reference, with its leakage line

| year | `emissions_mt` | **`import_co2_mt_reported`** | import / in-ISO | leakage-incl. total | `clean_share` | `avg_price` | `curtailment_twh` | `neg_price_hours` | `unserved_mwh` |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 23.6923 | **10.4548** | **44.1 %** | 34.1471 | 0.3924 | 49.24 | 0.0 | 0 | 0.0 |
| 2027 | 24.5911 | **10.1556** | **41.3 %** | 34.7467 | 0.3879 | 48.28 | 0.0 | 0 | 0.0 |
| 2028 | 17.1630 | **10.5393** | **61.4 %** | 27.7023 | 0.5205 | 50.02 | 0.0 | 0 | 0.0 |
| 2029 | 13.7082 | **9.8112** | **71.6 %** | 23.5194 | 0.5863 | 48.19 | 0.0 | 0 | 0.0 |
| 2030 | 10.9030 | **11.0746** | **101.6 %** | 21.9776 | 0.6227 | 53.78 | 0.0 | 0 | 0.0 |

**By 2030 NYISO's imported CO2 exceeds its own.** The ratio climbs because D77 + D65-B cut the
in-ISO denominator (23.69 → 10.90 Mt) while the import line stays flat at 9.8–11.1 Mt. No CO2
delta below is quoted without its import line beside it.

### 2.1 Every Stage-A leg, absolute and vs REF

`ΔTOTAL` is the leakage-inclusive delta (`Δemissions + Δimport`). Curtailment is **0.0000 TWh** and
`negative_price_hours` **0** in every leg and every year; `unserved_mwh` is **0.0** in every
Stage-A leg-year, `ALL-CLEAN` included; `backstop_built_mw` is **0** everywhere.

| case | yr | CO2 Mt | ΔCO2 | import CO2 Mt | Δimport | TOTAL Mt | ΔTOTAL | clean | Δclean | avg $ | Δavg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CES-P10 | 2026 | 23.6924 | +0.0001 | 10.4548 | −0.0000 | 34.1472 | +0.0001 | 0.3924 | +0.0000 | 49.24 | +0.00 |
| CES-P10 | 2027 | 24.5903 | −0.0008 | 10.1556 | +0.0000 | 34.7459 | −0.0008 | 0.3879 | +0.0000 | 48.27 | −0.01 |
| CES-P10 | 2028 | 17.1597 | −0.0033 | 10.5333 | −0.0060 | 27.6930 | −0.0093 | 0.5220 | +0.0015 | 50.01 | −0.01 |
| CES-P10 | 2029 | 10.7287 | **−2.9795** | 9.3778 | −0.4334 | 20.1065 | **−3.4129** | 0.6439 | +0.0576 | 45.35 | −2.84 |
| CES-P10 | 2030 | 8.6383 | **−2.2647** | 10.1574 | −0.9172 | 18.7957 | **−3.1819** | 0.6741 | +0.0514 | 50.19 | −3.59 |
| CES-P20 | 2026 | 23.6924 | +0.0001 | 10.4548 | −0.0000 | 34.1472 | +0.0001 | 0.3924 | +0.0000 | 49.24 | +0.00 |
| CES-P20 | 2027 | 24.5919 | +0.0008 | 10.1536 | −0.0020 | 34.7455 | −0.0012 | 0.3879 | +0.0000 | 48.27 | −0.01 |
| CES-P20 | 2028 | 17.1948 | **+0.0318** | 10.5389 | −0.0004 | 27.7337 | **+0.0314** | 0.5221 | +0.0016 | 49.97 | −0.05 |
| CES-P20 | 2029 | 9.1990 | **−4.5092** | 9.0313 | −0.7799 | 18.2303 | **−5.2891** | 0.6768 | +0.0905 | 44.00 | −4.19 |
| CES-P20 | 2030 | 6.8086 | **−4.0944** | 9.5492 | −1.5254 | 16.3578 | **−5.6198** | 0.7140 | +0.0913 | 46.79 | −6.99 |
| CES-P30 | 2026 | 23.6920 | −0.0003 | 10.4548 | −0.0000 | 34.1468 | −0.0003 | 0.3924 | +0.0000 | 49.23 | −0.01 |
| CES-P30 | 2027 | 24.5906 | −0.0005 | 10.1536 | −0.0020 | 34.7442 | −0.0025 | 0.3879 | +0.0000 | 48.27 | −0.01 |
| CES-P30 | 2028 | 17.2098 | **+0.0468** | 10.5121 | −0.0272 | 27.7219 | **+0.0196** | 0.5221 | +0.0016 | 49.90 | −0.12 |
| CES-P30 | 2029 | 8.9580 | **−4.7502** | 9.0051 | −0.8061 | 17.9631 | **−5.5563** | 0.6815 | +0.0952 | 43.48 | −4.71 |
| CES-P30 | 2030 | 6.3030 | **−4.6000** | 8.5706 | −2.5040 | 14.8736 | **−7.1040** | 0.7401 | +0.1174 | 44.21 | −9.57 |
| **CES-P60** | 2026 | 23.6904 | −0.0019 | 10.4548 | −0.0000 | 34.1452 | −0.0019 | 0.3924 | +0.0000 | 49.23 | −0.01 |
| **CES-P60** | 2027 | 24.5871 | −0.0040 | 10.1556 | +0.0000 | 34.7427 | −0.0040 | 0.3879 | +0.0000 | 48.26 | −0.02 |
| **CES-P60** | 2028 | 17.2478 | **+0.0848** | 10.4988 | −0.0405 | 27.7466 | **+0.0443** | 0.5221 | +0.0016 | 49.70 | −0.32 |
| **CES-P60** | 2029 | 8.6092 | **−5.0990** | 8.8559 | −0.9553 | 17.4651 | **−6.0543** | 0.6896 | +0.1033 | 43.29 | −4.90 |
| **CES-P60** | 2030 | **5.6588** | **−5.2442** | **6.4769** | **−4.5977** | **12.1357** | **−9.8419** | 0.7853 | +0.1626 | 38.97 | −14.81 |
| CES-T80 | 2026 | 23.6954 | +0.0031 | 10.4506 | −0.0042 | 34.1460 | −0.0011 | 0.3924 | +0.0000 | 49.24 | +0.00 |
| CES-T80 | 2027 | 24.5913 | +0.0002 | 10.1536 | −0.0020 | 34.7449 | −0.0018 | 0.3879 | +0.0000 | 48.27 | −0.01 |
| CES-T80 | 2028 | 17.1344 | −0.0286 | 10.5199 | −0.0194 | 27.6543 | −0.0480 | 0.5214 | +0.0009 | 50.01 | −0.01 |
| CES-T80 | 2029 | 11.3295 | **−2.3787** | 9.4760 | −0.3352 | 20.8055 | **−2.7139** | 0.6331 | +0.0468 | 46.09 | −2.10 |
| CES-T80 | 2030 | 9.2987 | **−1.6043** | 10.3119 | −0.7627 | 19.6106 | **−2.3670** | 0.6609 | +0.0382 | 51.24 | −2.54 |
| VOL-MID | 2026 | 23.6954 | +0.0031 | 10.4506 | −0.0042 | 34.1460 | −0.0011 | 0.3924 | +0.0000 | 49.24 | +0.00 |
| VOL-MID | 2027 | 24.5913 | +0.0002 | 10.1536 | −0.0020 | 34.7449 | −0.0018 | 0.3879 | +0.0000 | 48.27 | −0.01 |
| VOL-MID | 2028 | 17.1630 | +0.0000 | 10.5393 | −0.0000 | 27.7023 | −0.0000 | 0.5205 | +0.0000 | 50.02 | +0.00 |
| VOL-MID | 2029 | 13.7079 | −0.0003 | 9.8112 | −0.0000 | 23.5191 | −0.0003 | 0.5863 | +0.0000 | 48.21 | +0.02 |
| VOL-MID | 2030 | 10.9042 | +0.0012 | 11.0760 | +0.0014 | 21.9802 | +0.0026 | 0.6227 | +0.0000 | 53.78 | +0.00 |
| VOL-HI | 2026 | 23.6954 | +0.0031 | 10.4506 | −0.0042 | 34.1460 | −0.0011 | 0.3924 | +0.0000 | 49.24 | +0.00 |
| VOL-HI | 2027 | 24.5913 | +0.0002 | 10.1536 | −0.0020 | 34.7449 | −0.0018 | 0.3879 | +0.0000 | 48.27 | −0.01 |
| VOL-HI | 2028 | 17.1630 | +0.0000 | 10.5393 | −0.0000 | 27.7023 | −0.0000 | 0.5205 | +0.0000 | 50.02 | +0.00 |
| VOL-HI | 2029 | 13.7079 | −0.0003 | 9.8112 | −0.0000 | 23.5191 | −0.0003 | 0.5863 | +0.0000 | 48.21 | +0.02 |
| VOL-HI | 2030 | 10.9042 | +0.0012 | 11.0760 | +0.0014 | 21.9802 | +0.0026 | 0.6227 | +0.0000 | 53.78 | +0.00 |
| CES-P20+VOL-HI | 2026 | 23.6915 | −0.0008 | 10.4548 | −0.0000 | 34.1463 | −0.0008 | 0.3924 | +0.0000 | 49.24 | +0.00 |
| CES-P20+VOL-HI | 2027 | 24.5932 | +0.0021 | 10.1536 | −0.0020 | 34.7468 | +0.0001 | 0.3879 | +0.0000 | 48.26 | −0.02 |
| CES-P20+VOL-HI | 2028 | 17.1948 | +0.0318 | 10.5389 | −0.0004 | 27.7337 | +0.0314 | 0.5221 | +0.0016 | 49.97 | −0.05 |
| CES-P20+VOL-HI | 2029 | 9.1979 | **−4.5103** | 9.0358 | −0.7754 | 18.2337 | **−5.2857** | 0.6767 | +0.0904 | 44.00 | −4.19 |
| CES-P20+VOL-HI | 2030 | 6.8098 | **−4.0932** | 9.5478 | −1.5268 | 16.3576 | **−5.6200** | 0.7140 | +0.0913 | 46.79 | −6.99 |
| ALL-CLEAN | 2026 | 25.3850 | +1.6927 | 10.5784 | +0.1236 | 35.9634 | +1.8163 | 0.3819 | −0.0105 | 50.49 | +1.25 |
| ALL-CLEAN | 2027 | 27.0665 | +2.4754 | 10.5003 | +0.3447 | 37.5668 | +2.8201 | 0.3723 | −0.0156 | 50.37 | +2.09 |
| ALL-CLEAN | 2028 | 20.2591 | +3.0961 | 11.2239 | +0.6846 | 31.4830 | +3.7807 | 0.4936 | −0.0269 | 52.04 | +2.02 |
| ALL-CLEAN | 2029 | 12.9452 | −0.7630 | 9.9336 | +0.1224 | 22.8788 | −0.6406 | 0.6331 | +0.0468 | 47.43 | −0.76 |
| ALL-CLEAN | 2030 | 11.2883 | +0.3853 | 10.7901 | −0.2845 | 22.0784 | +0.1008 | 0.6608 | +0.0381 | 52.84 | −0.94 |

**`ALL-CLEAN` must be netted against `LOAD-HI`, not REF** — it carries growth-high + DC-high by
construction, so its REF-relative column above is mostly the load half. Against the committed
`LOAD-HI` leg (`c2ceaefa4afafcda`), which is its correct baseline:

| yr | ΔCO2 vs LOAD-HI | Δimport | ΔTOTAL | Δclean | Δavg $ |
|---|---|---|---|---|---|
| 2026 | +0.0012 | +0.0000 | +0.0012 | +0.0000 | +0.00 |
| 2027 | +0.0012 | +0.0000 | +0.0012 | +0.0000 | +0.00 |
| 2028 | −0.0123 | −0.0141 | −0.0264 | +0.0004 | +0.00 |
| 2029 | **−3.0409** | −0.4520 | **−3.4929** | +0.0549 | −3.12 |
| 2030 | **−2.7317** | −0.8176 | **−3.5493** | +0.0530 | −4.18 |

### 2.2 The 2028 reversal, stated rather than smoothed

At 2028 the in-ISO CO2 **rises** with the CES premium in three of four rungs
(+0.0318 / +0.0468 / +0.0848 at $20/$30/$60) and the leakage-inclusive total rises in all three
too. The mechanism is visible in the by-fuel frame: the premium pulls a little more `gas_cc_ccs`
capacity in (2,984.4 → 2,998.1 → 2,999.7 → 2,999.9 → 2,999.5 MW at REF/$10/$20/$30/$60 — the
**3 GW/yr/ISO retrofit cap** to within 0.5 MW) and displaces a little more *import* than *in-ISO
gas*, so the scored in-ISO number worsens while total gas burn barely moves. The magnitude is
≤ 0.085 Mt on a 17.16 Mt level (≤ 0.5 %), it is the only year in which the ladder is non-monotone
in either direction, and it is **not** the NEISO reversal (which was a leakage-line sign flip at
2030 of 0.88 Mt). It is reported because prediction **P-3** claimed monotonicity in *every* year.

### 2.3 Both nettings, ruling S11 — `CES-P20+VOL-HI` and `ALL-CLEAN`

**Counts-toward is the headline (as built and as ruled); additional is reported beside it.**
`CT esc` = `max(0, target·D − federal_credited)`; `ADD esc` = `max(0, target·D + V −
federal_credited)`; `VOL esc` = `max(0, V − eligible)`. `D` is the run's own demand.

**`CES-P20+VOL-HI`** — carries a CES *premium* (a screen price, no row), so its only row is the
voluntary one and the CES columns below are the arithmetic of the netting question, not a dual:

| yr | D TWh | credited TWh | V TWh | target | target·D | **CT esc TWh** | ADD esc TWh | **VOL esc TWh** | eligible TWh |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 154.094 | 60.486 | 15.677 | 0.5500 | 84.752 | **24.266** | 39.944 | **8.363** | 7.314 |
| 2027 | 155.915 | 60.486 | 17.924 | 0.5778 | 90.084 | **29.599** | 47.523 | **10.610** | 7.314 |
| 2028 | 157.757 | 82.373 | 20.173 | 0.6056 | 95.531 | **13.158** | 33.331 | **12.859** | 7.314 |
| 2029 | 159.621 | 108.058 | 22.423 | 0.6333 | 101.093 | **0.000** | 15.459 | **10.531** | 11.892 |
| 2030 | 161.507 | 115.345 | 24.676 | 0.6611 | 106.774 | **0.000** | 16.105 | **12.783** | 11.892 |

**`ALL-CLEAN`** — the one arm where a CES *target row* and the voluntary row are both live, so
D-6 has real content here:

| yr | D TWh | credited TWh | V TWh | target | target·D | **CT esc TWh** | ADD esc TWh | **VOL esc TWh** | eligible TWh |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 158.369 | 60.486 | 17.677 | 0.5500 | 87.103 | **26.618** | 44.295 | **10.363** | 7.314 |
| 2027 | 162.448 | 60.486 | 21.148 | 0.5778 | 93.859 | **33.373** | 54.521 | **13.833** | 7.314 |
| 2028 | 166.632 | 82.267 | 24.627 | 0.6056 | 100.905 | **18.638** | 43.265 | **17.312** | 7.314 |
| 2029 | 170.923 | 108.251 | 28.114 | 0.6333 | 108.251 | **0.000** | 28.114 | **16.222** | 11.892 |
| 2030 | 175.325 | 115.909 | 31.611 | 0.6611 | 115.909 | **0.000** | 31.611 | **19.522** | 12.089 |

**The two readings differ by exactly `V` in every year — 17.677 → 31.611 TWh, more than the entire
eligible fleet's annual output.** That is the largest D-6 spread the campaign has produced, and in
2029–2030 it is the difference between a *met* standard (counts-toward: escape 0) and a **28.1 /
31.6 TWh shortfall** (additional). Neither reading is asserted as the answer; **D-6 is settled as
"counts toward; report both" (S11)** and that is what is done, with the additional reading beside
it so the size of the open modelling choice is visible.

---

## 3. Gate verdicts — the nine Stage-A legs

Scored with the committed instrument
`docs/handoffs/scn-ws5a-policy-nyiso/score_gates_2026-09-06.py`, whose JSON output is committed
beside it. `CAP-STATE-TIGHT` is **excluded from Stage-A gate scoring per ruling S17** and is scored
separately in §8.

| gate | verdict | evidence |
|---|---|---|
| **G1** resolved-input premise reproduces at THE PIN | **PASS** (pre-solve) | Carbon Δ = 0.000000 in five years × four arms; V from the runner's own demand chain; budgets from `scheduled_power_sector_budget`. §1.1–1.2. |
| **G2** REF-side precondition | **PASS** | REF 14/14 invariants, `unserved_mwh` 0.0, `hours_ge_500` 0, `backstop_built_mw` 0.0, reserve margin +0.185 → +0.201, all five years. **Every price, captured price and deployment level in this document is campaign-grade**; the one standing level caveat is the leakage line (44 → 102 %), disclosed beside every CO2 number and never used to discount one. |
| **G3** footprint confinement | **PASS** | CES-premium arms move eligible-class rows (wind/solar/nuclear/`gas_cc_ccs`), the thermal and import rows they displace, and the retrofit + entry ledgers — nothing else. `builds_storage_mw` is **0.0** in every leg-year; `retire_mw` is REF's **27.8 MW in 2027 and 0.0 elsewhere in every leg**; hydro is 26.2129 TWh and biomass/oil move only through dispatch. `CES-P60`'s new nuclear is **inside** the declared footprint — nuclear is a `federal_ces_eligible_fuels` member credited 1.0 — and is called out in §4 rather than treated as a leak. Voluntary arms move eligible-class rows, thermal rows and the escape column only. |
| **G4** `CES-T80` dual identity | **PASS, on BOTH legs** | Escape in 2026–2028: shortfall 24.266 / 29.599 / 13.264 TWh, target unmet. **Binding in 2029 and 2030**: credited share 0.6333333332 vs target 0.6333330000 and 0.6611111117 vs 0.6611110000 — the LP drives credited to `target·D` to **5.3e-5 / 1.8e-5 TWh**, which is the interior-dual limb the PRECOMMIT pre-registered as "G4 passing on its other leg". Same identity on `ALL-CLEAN` (5.7e-5 / 2.0e-5). The dual's *numeric value* is not re-readable from committed artifacts (see the note below). |
| **G5** no non-target load-bearing invariant flips PASS → FAIL | **PASS** | **14/14 PASS on all nine Stage-A legs, 126 invariant records, zero FAIL and zero WARN.** No line owed in `invariant-failures.json` for any Stage-A leg. |
| **G6** no unserved energy where REF has none | **PASS** | `unserved_mwh` = **0.0** in all 45 Stage-A leg-years, `ALL-CLEAN` included — and G6 binds only weakly there by construction, so this is a stronger pass than the gate required. |
| **G7** voluntary dual bounded, per arm | **PASS on the observable half; dual value UNVERIFIED, with its reason** | The escape identity holds exactly: `escape = V − eligible` reproduces to the printed digit in every voluntary leg-year (VOL-MID 6.542 / 7.647 / 8.754 / 5.284 / 6.395; VOL-HI and CES-P20+VOL-HI 8.363 / 10.610 / 12.859 / 10.531 / 12.783; ALL-CLEAN 10.363 / 13.833 / 17.312 / 16.222 / 19.522 TWh), and every arm is in escape in every year as phase 0 predicted. **The dual scalar itself cannot be re-read**: `clean_region_duals` is written only to the cached year bundle and the solver log, and under ruling S16 each shard's `results/NYISO/<key>/` lived in its own container. Recorded as an artifact gap, not claimed as measured (§9 item 4). |
| **G8** curtailment before thermal | **PASS in its degenerate form** | `curtailment_twh` = **0.0000 in every Stage-A leg-year** and in REF, so Δcurtailment = 0.0 exactly and the finding-against-the-row that a non-zero value would have been does not arise. G8's ordering claim has no object on NYISO and is recorded **N/A with its reason**, exactly as declared pre-solve. |
| **G9** both nettings on the combined legs | **PASS** | §2.3, counts-toward as headline, additional beside it. |
| **G13** rematerialization identity | **PASS** | ADDENDUM 2 §1; §1.7 above. |
| **G-B1** at $60, `attr` strictly exceeds REF's | **PASS (pre-solve), CONFIRMED post-solve** | +20.00 $/MWh on 50/50 eligible tech-zone-years, computed before the leg ran; the post-solve entry response (§4) is the confirmation the arithmetic predicted. |
| **G-B2** bracket footprint + `rps_dual` unmoved | **PASS** | `CES-P60`'s `rps_dual` = **40.0000 in all five years**, identical to REF's — the premium outbids the RPS row *inside* the fold and never reaches the row itself, which is the STOP this gate was written to catch. Footprint as G3. |
| **G-B3** bracket monotonicity, as a direction | **PASS, no reversal** | `builds_renew_mw` at $60 ≥ $30's in every year (2030: 156.6 vs 0.0; equal elsewhere). \|ΔCO2\| at $60 ≥ at $30 in all five years (0.0019/0.0040/0.0848/5.0990/5.2442 vs 0.0003/0.0005/0.0468/4.7502/4.6000). Δclean_share at $60 ≥ at $30 in all five (equal in 2026–2028, +0.1033 vs +0.0952 and +0.1626 vs +0.1174 in 2029–2030). **The degenerate-leg clause did not need to fire**: the bracket is not a null. |

**No gate killed an arm, and no gate promoted one.** No gate read a target residual.

---

## 4. The deployment response vs REF

This is the section the S15 ruling exists for. Capacity in MW, from each leg's own committed
`capacity_by_fuel_mw` and `builds_*` rows.

### 4.1 Renewable entry — the null and where it breaks

| case | attribute price into the entry fold | 2026 | 2027 | 2028 | 2029 | 2030 | `builds_renew_mw` 2030 |
|---|---|---|---|---|---|---|---|
| REF | 40.00 (RPS) | 2400 / 1500 | 2400 / 1500 | 2400 / 1500 | 3400 / 3343.4 | 3400 / **3343.4** | **0.0** |
| CES-P10 | 40.00 (masked) | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3343.4** | **0.0** |
| CES-P20 | 40.00 (masked) | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3343.4** | **0.0** |
| CES-P30 | 40.00 (masked) | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3343.4** | **0.0** |
| CES-T80 | 50.00 (ACP, escape) | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3500.0** | **+156.6** |
| ALL-CLEAN | 50.00 (ACP, escape) | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3500.0** | **+156.6** |
| **CES-P60** | **60.00** | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3500.0** | **+156.6** |
| VOL-MID / VOL-HI / CES-P20+VOL-HI | 40.00 (masked) | ≡ REF | ≡ REF | ≡ REF | ≡ REF | 3400 / **3343.4** | **0.0** |

(wind MW / solar MW. "≡ REF" is byte equality on both columns.)

**Three readings, and the third is the one that matters.** (a) The three committed premium rungs
add **exactly zero** MW — NYISO reproduces NEISO's null. (b) The null breaks the moment the
attribute price clears the $40 RPS escape, at $50, not only at $60 — so the threshold is inside
**(40, 50]**, and the bracket did not have to reach $60 to find it. (c) **The response is a single
156.6 MW block, identical at $50 and at $60**: clearing the mask by $10 and clearing it by $20 buy
the *same* solar. The entry fold is behaving as a step, not as an elasticity, over this range.

### 4.2 The CCS retrofit ledger — the premium's real channel, and the target row's absence from it

`gas_cc_ccs` capacity MW (the retrofit ledger; nothing else builds this fuel):

| case | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| REF | 0 | 0 | 2984.4 | 5255.9 | 6255.9 |
| CES-P10 | 0 | 0 | 2998.1 | 5994.5 | 7035.5 |
| CES-P20 | 0 | 0 | 2999.7 | 5999.7 | 7731.7 |
| CES-P30 | 0 | 0 | 2999.9 | 5999.3 | 7762.7 |
| **CES-P60** | 0 | 0 | 2999.5 | 5999.3 | **7890.3** |
| **CES-T80** | 0 | 0 | **2984.4** | **5255.9** | **6255.9** |
| **ALL-CLEAN** (vs LOAD-HI 2984.4 / 5979.0 / 6979.0) | 0 | 0 | 2984.4 | 5979.0 | 6979.0 |
| VOL-MID / VOL-HI | 0 | 0 | 2984.4 | 5255.9 | 6255.9 |
| CES-P20+VOL-HI | 0 | 0 | 2999.7 | 5999.7 | 7731.7 |

**Two facts, both structural.** (i) The **premium** saturates on the 3 GW/yr/ISO retrofit cap in
2028 and 2029 (2,999.5–2,999.9 MW of a 3,000 MW cap) and separates only in 2030, when the
retrofit-eligible unabated `gas_cc` fleet has fallen to 4.3–5.9 GW; that is the mechanism
PRECOMMIT P-4/P-6 named, confirmed. (ii) **`CES-T80`'s $50 ACP moves the ledger by 0.0 MW in every
year** — and `ALL-CLEAN`, which also carries the target row, matches its own `LOAD-HI` baseline
exactly. The cause is a code seam read at the pin: `model/capacity_evolution/ccs.py:475-476` prices
the retrofit's attribute uplift with
`effective_eac_price_for_unit(config, "gas_cc"|"gas_cc_ccs", …)` — documented at `:223-225` as
`max(legacy eac_price_*, federal CES premium × the state's credit fraction)` — and **never reads
`clean_attribute_price_by_fuel`**, which is where a target-row dual lives. The retirement screen
(`retirements.py:3529-3532`) and the entry screen (`new_entry.py:1132-1143`) both *do* read it.
**So the CES target row and the CES premium reach different capacity screens**, and a $50 row dual
buys less retrofit than a $20 premium. Routed §9 item 1.

### 4.3 The one thing only the bracket found: new nuclear

`CES-P60` is the **only** leg in the campaign's NYISO set that moves nuclear capacity:

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| nuclear MW, every other leg incl. REF | 3326 | 3326 | 3326 | 3326 | 3326 |
| **nuclear MW, `CES-P60`** | 3326 | 3326 | 3326 | **3482** | **3826** |
| `builds_thermal_mw`, `CES-P60` (REF 0 / 0 / 0 / 1000.0 / 0) | 0 | 0 | 0 | **1156.6** | **343.4** |
| nuclear generation TWh (others 26.958) | 26.958 | 26.958 | 26.958 | **28.227** | **31.011** |

The `builds_thermal_mw` deltas (+156.6 in 2029, +343.4 in 2030) account for the nuclear additions
exactly — nuclear is carried in the thermal-build column. Nuclear is CES-eligible at credit 1.0 and
is **not** in `_RPS_ELIGIBLE_FUELS = {wind, solar}`, so it earns 0 from the RPS row in the
retirement screen and the CES premium is its sole attribute price there; at $60 it clears an entry
screen that $50 does not. Reserve margin rises with it (0.208 → 0.213 in 2029, 0.201 → 0.218 in
2030), and NYISO's imports fall 33.76 → 22.95 TWh at 2030. **This is the single largest structural
response in the lane**, it exists only above the mask, and no committed campaign level would have
found it.

### 4.4 The voluntary arms

`builds_renew_mw`, `builds_thermal_mw`, `builds_storage_mw`, `retire_mw`, `wind_mw`, `solar_mw`,
`gas_cc_ccs_mw` and `reserve_margin` are **identical to REF's in all five years of `VOL-MID` and
`VOL-HI`**. `CES-P20+VOL-HI` is identical to `CES-P20`'s. The voluntary row has **no deployment
content on NYISO at either committed ceiling**.

---

## 5. Predictions, scored as written — including every miss, at full magnitude

Twenty-two predictions were pre-registered (P-1 … P-19 in the PRECOMMIT, P-20 … P-22 in
ADDENDUM 2). **Fourteen HIT, five MISSED, two are pre-registered SPLITs, one is unscorable.**

| # | claim (abbreviated) | verdict | measurement |
|---|---|---|---|
| **P-1** | rematerialized REF / LOAD-HI reproduce the committed trajectories exactly (G13) | **HIT** | Exact on `co2_mt` and `lw_price`, both legs, five years (ADDENDUM 2 §1). |
| **P-2** | no solved arm's 2026 is byte-identical to REF's | **HIT on the letter, with the magnitude stated against it** | Every 2026 ΔCO2 is non-zero, but the largest is **+0.0031 Mt (1.3e-4 relative)** and the whole 2026–2027 block moves ≤ 0.004 Mt in every arm. Below 2028 there is no CCS to credit and the entry fold is masked, so nothing but a dispatch tie-reshuffle is available; the prediction is technically right and its substance ("every mechanism is live from 2026") is **wrong**. |
| **P-3** | CO2 falls and clean share rises monotonically REF → P10 → P20 → P30 **in every year** | **MISS** | Clean share is monotone non-decreasing in all five years. **CO2 is not**: 2028 goes 17.1630 → 17.1597 → **17.1948 → 17.2098**, i.e. up at $20 and $30; 2026 and 2027 are non-monotone at the 1e-3 Mt level. Monotone as claimed only in 2029 and 2030. §2.2. |
| **P-4** | the dominant channel is the CCS retrofit screen; retrofit capacity above REF's in 2028–2030 in all three arms, monotone in premium | **HIT, with one hairline exception recorded** | Above REF in all nine leg-years; monotone in 2028 and 2030. **2029 is non-monotone by 0.4 MW** (P20 5999.7 > P30 5999.3) — both at the 3,000 MW cap, so the ordering there is a cap artifact, not a ladder. §4.2. |
| **P-5** | \|ΔCO2\| < 1.0 Mt in 2026–2027 in all three arms, and > 1.0 Mt in ≥1 of 2028–2030 in P20 and P30 — "the sharpest falsifiable split in the CES block" | **HIT, cleanly** | 2026–2027 max \|Δ\| **0.0008 Mt**; P20 2029 **−4.5092**, P30 2029 **−4.7502**. |
| **P-6** | P20 and P30 within 15 % on ΔCO2 while P10 → P20 moves more | **HIT** | 2030: \|ΔP30−ΔP20\|/\|ΔP20\| = **12.3 %** vs P10→P20 **80.8 %**. 2029: **5.3 %** vs **51.3 %**. Saturating from above, on the cap P-4 named. |
| **P-7** | `avg_price` falls in all three arms **and** `negative_price_hours` > 0 in CES-P30 | **SPLIT — first limb HIT, second limb MISS** | Price falls in every arm and year (2030: 53.78 → 50.19 / 46.79 / 44.21; −14.81 at $60). **`negative_price_hours` = 0 in every case and every year**, including $60. The premium never reaches a price-setting VRE hour because NYISO's VRE never becomes marginal — renewable builds are REF's at all three rungs (§4.1). The prediction assumed a channel this ISO does not have. |
| **P-8** | `CES-T80` in escape in **every** year, dual = $50 exactly; 2029/2030 flagged as genuinely uncertain, an interior dual there pre-registered as G4's other leg | **SPLIT, resolving to the flagged alternative** | Escape 2026–2028; **binding, target met exactly, in 2029 AND 2030**. The main clause misses for two of five years; the alternative I wrote into the same paragraph is what happened, and G4 passes on it. |
| **P-9** | `CES-T80` produces the **largest deployment response of any leg**; builds at their annual caps from 2027, exceeding CES-P30's | **MISS, badly** | `CES-T80`'s retrofit ledger is **REF's, to 0.1 MW, in every year** — smaller than *every* premium rung. Its only response is the +156.6 MW solar block, which `CES-P60` also builds while additionally adding 500.4 MW of nuclear and 1,634.4 MW of retrofit. The largest response in the lane is `CES-P60`'s, and the second largest is `CES-P30`'s. The root cause is §4.2's seam, which I did not know when I wrote P-9. |
| **P-10** | voluntary duals at their ceilings; escape ≈ 6.5/7.6/8.8/5.3/6.4 (mid) and 8.4/10.6/12.9/10.5/12.8 (high) TWh | **HIT on the escape volumes; the dual is UNVERIFIABLE** | Measured 6.542/7.647/8.754/5.284/6.395 and 8.363/10.610/12.859/10.531/12.783 — the predicted values to the printed digit. The dual scalar is not re-readable from committed artifacts (G7 note, §9 item 4). |
| **P-11** | \|ΔCO2\| < 1.5 Mt in every year of VOL-MID and VOL-HI | **HIT, by three orders of magnitude** | Max \|Δ\| **0.0031 Mt**. |
| **P-12** | VOL-HI's escape exceeds VOL-MID's in every year; its ΔCO2 at least as negative | **HIT, degenerately** | Escape strictly larger in all five years (+1.821 → +6.388 TWh). ΔCO2 **equal**, which satisfies "at least as" — and the equality is the finding, not the prediction. |
| **P-13** | Δcurtailment = exactly 0.0 in every voluntary leg-year | **HIT** | 0.0000 TWh everywhere. |
| **P-14** | cap identity: emissions = budget, dual > 0, in every binding year | **HIT** | §8. |
| **P-15** | ΔCO2 = −0.53 / −2.17 / +4.5 / +7.2 / +9.3 Mt — "the most reasoned and most likely to miss prediction in the lane" | **HIT, to 0.01 Mt in all five years** | −0.5323 / −2.1711 / +4.5170 / +7.2318 / +9.2970. §8. |
| **P-16** | the endogenous cap dual exceeds the RGGI adder it replaced in every binding year | **HIT, 5/5** | §8. |
| **P-17** | the case's reading is "a quantity instrument under-delivers against a price instrument once an abatement technology arrives" | **CONFIRMED** | `gas_cc_ccs` is **0.0 MW and 0.0 TWh in every year** of the cap case. §8. |
| **P-18** | `CES-P20+VOL-HI`'s eligible generation exceeds `CES-P20`'s, so its voluntary escape is **smaller** than `VOL-HI`'s | **MISS, on both limbs** | Eligible generation is **identical** to `CES-P20`'s and to `VOL-HI`'s (7.314 ×3, 11.892 ×2 TWh), so the escape is `VOL-HI`'s **exactly** (8.363 / 10.610 / 12.859 / 10.531 / 12.783 TWh). The premium builds no VRE at all (the S15 mask), so there is no eligible-fleet growth for the voluntary row to see. The "one place the two axes interact measurably" turns out to be a place they do not interact at all. |
| **P-19** | `ALL-CLEAN`: both rows in escape at their ceilings; the two nettings differ by V | **SPLIT** | The spread **is** V in every year, to the digit (§2.3) — HIT. But the CES row is **not** in escape in 2029–2030 under counts-toward (target met exactly), so the "both rows in escape at their ceilings" clause misses for two of five years, the same way P-8 did. |
| **P-20** | `CES-P60`'s `builds_renew_mw` exceeds REF's in ≥1 year of 2027–2030 and exceeds `CES-P30`'s in ≥1 year | **HIT** | 2030: **156.6 vs 0.0 and 0.0**. |
| **P-21** | P10/P20/P30's Δ`builds_renew` arrives through the energy-price term alone, so it is small and **non-monotone**; P60's is monotone-positive through the attribute term. A *monotone* renewable-build ladder across P10→P20→P30 would falsify ADDENDUM 2 §3.2's masking arithmetic | **HIT on the substance; the non-monotonicity limb is VACUOUS** | Δ`builds_renew` is **exactly 0.0** at all three masked rungs in all five years — stronger than "small and non-monotone", and it is the outcome the masking arithmetic requires. The falsification test did not fire: §3.2 stands. |
| **P-22** | `CES-P60`'s ΔCO2 is more negative than `CES-P30`'s **in every year** | **MISS in 2028; HIT in the other four** | 2026 −0.0019 vs −0.0003 ✓; 2027 −0.0040 vs −0.0005 ✓; **2028 +0.0848 vs +0.0468 ✗** (P60 is 0.038 Mt *worse*); 2029 −5.0990 vs −4.7502 ✓; 2030 −5.2442 vs −4.6000 ✓. The 2028 miss is the §2.2 reversal reaching the top rung. |

**Not scorable, and named as such:** the *numeric* dual limbs of G4, G7 and P-10 — the escape and
binding **identities** are all confirmed from committed artifacts, but the dual scalars themselves
were only ever written to the shard containers' cached bundles and logs. Nothing in this document
quotes a dual value that was not measured pre-solve or is not in a committed file.

---

## 6. Cost — wall and RSS per solve-year

Every leg: 5 solve-years, sequential within the invocation (rule 12's within-invocation half,
honoured in every shard), one LP at a time. Shards were separate containers under ruling S16.

| leg | shard | wall s | **min/solve-year** | peak RSS MB | per-year wall s (2026…2030) |
|---|---|---|---|---|---|
| `REF` (control, unregistered) | coordinator | 1461.9 | 4.87 | 3501.3 | 219.0 · 268.3 · 312.9 · 330.5 · 331.1 |
| `LOAD-HI` (control, unregistered) | coordinator | 1544.0 | 5.15 | 3868.9 | 219.7 · 260.6 · 321.9 · 338.6 · 403.1 |
| `CES-P10` | A | 1072.0 | 3.57 | 4057.2 | 184.3 · 195.2 · 221.4 · 236.2 · 234.7 |
| `CES-P20` | A | 1059.4 | 3.53 | 3619.5 | 160.8 · 192.0 · 237.1 · 238.0 · 231.3 |
| `CES-P30` | B | 1328.2 | 4.43 | 3527.4 | 214.4 · 236.8 · 296.8 · 283.5 · 296.5 |
| `CES-P60` | B | 1392.0 | 4.64 | 3506.2 | 229.6 · 237.5 · 278.7 · 315.9 · 330.2 |
| `CES-T80` | C | 1818.9 | 6.06 | 3556.2 | 219.3 · 213.9 · 271.0 · **668.4** · 446.1 |
| `ALL-CLEAN` | C | 1851.6 | 6.17 | 3808.0 | 173.4 · 230.2 · 309.0 · **675.2** · 463.6 |
| `VOL-MID` | D | 813.8 | 2.71 | 3674.4 | 165.4 · 157.2 · 161.6 · 160.4 · 169.0 |
| `VOL-HI` | D | 863.7 | 2.88 | 3587.8 | 145.0 · 147.5 · 192.9 · 175.8 · 202.5 |
| `CES-P20+VOL-HI` | E | 825.2 | 2.75 | 3662.8 | 165.6 · 142.3 · 171.4 · 156.8 · 189.0 |
| **`CAP-STATE-TIGHT`** (§8) | E | **3860.6** | **12.87** | 3636.9 | **1367.3** · 488.2 · 805.2 · 596.1 · 603.8 |

**Nine Stage-A legs: 11,024.8 s = 183.7 min.** Twelve legs incl. the two controls and the cap:
17,891.3 s = **4.97 h**. Peak RSS **3.51–4.06 GB**, well inside a 15 GB container.

**Three cost readings worth carrying.** (a) **A binding mass-cap row costs 12.87 min/solve-year
against 2.71–6.17 for every other arm** — 64.3 min on one of ten legs, **35 % of the lane's total
LP** — which independently reproduces NEISO's finding 4 (14.57 min/solve-year, 57 % of its total).
A campaign running `CAP-STATE-TIGHT` on all three program ISOs must budget it separately.
(b) **A binding CES *target row* costs about double a slack one in the year it binds**: `CES-T80`
and `ALL-CLEAN` both spike to 668–675 s at **2029**, the first year the row is interior (§3, G4),
against 271–309 s at 2028 when it escapes. Escape is cheap because it is a bound; binding is a
constraint the simplex has to satisfy. (c) The S16 shard sizing was right: NYISO's measured
2.71–6.17 min/solve-year against the §5.5 table's 4.06 puts a 2-leg shard at 27–62 min of LP,
inside the <1 h target in every case.

---

## 7. Ruling S15 — the threshold beside the masked ladder, and the NYISO ↔ NEISO voluntary inverse

### 7.1 The mask, per year, as S15 asks it

| | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| **REF `rps_dual` ($/MWh)** | **40.0000** | **40.0000** | **40.0000** | **40.0000** | **40.0000** |
| `STATE_RPS_ACP["NYISO"]` | 40.0 | 40.0 | 40.0 | 40.0 | 40.0 |
| row state | escape (at ACP) | escape | escape | escape | escape |
| `rps_dual` in **every** solved arm (all ten legs) | 40.0000 | 40.0000 | 40.0000 | 40.0000 | 40.0000 |

**No arm moves the RPS row's dual** — not the $60 premium, not the $50 ACP, not the cap. That is
G-B2's own STOP condition never firing, and it is the direct evidence that the premium outbids the
row *inside* `max()` rather than reaching the row.

### 7.2 The CES dual each arm carries, the fold it produces, and the incremental entry it buys

| leg | CES signal into the fold | fold `attr` = max(CES, 40, ·) | vs REF | Δ `builds_renew_mw` (5 yr) | Δ nuclear MW | Δ `gas_cc_ccs` MW 2030 |
|---|---|---|---|---|---|---|
| REF | — | **40.00** | — | — | — | — |
| `CES-P10` | premium **$10** | **40.00** | **0.00 — MASKED** | **0.0 in all five years** | 0 | +779.6 |
| `CES-P20` | premium **$20** | **40.00** | **0.00 — MASKED** | **0.0 in all five years** | 0 | +1475.8 |
| `CES-P30` | premium **$30** | **40.00** | **0.00 — MASKED** | **0.0 in all five years** | 0 | +1506.8 |
| `CES-T80` | **row dual $50** (ACP, escape 2026–28; interior 2029–30) | **50.00** | **+10.00 — LIVE** | **+156.6 (2030)** | 0 | **0.0** |
| `ALL-CLEAN` | **row dual $50** (same identity) | **50.00** | **+10.00 — LIVE** | **+156.6 (2030)** | 0 | 0.0 vs LOAD-HI |
| **`CES-P60`** | premium **$60** | **60.00** | **+20.00 — LIVE** | **+156.6 (2030)** | **+156.0 (2029), +344.4 (2030)** | **+1634.4** |

**Does NYISO reproduce NEISO's exact-zero null? YES for the committed ladder, and NO above it — and
the premium at which it breaks is between $40 and $50, not at $60.** NEISO measured `vre_mw`
identical in REF and all eight non-cap arms because every level it carried ({10,20,30}, the $50
ACP, and both voluntary ceilings) sat **at or under** its own $50 RPS escape — including the ACP,
which *ties* rather than clears. NYISO's ACP is $40, so `CES-T80`'s $50 row **clears by $10** and
`CES-P60`'s $60 premium clears by $20, and both produce entry NEISO's arms structurally could not.
**That is the bracketing evidence S15 was created to obtain**: the campaign now has one ISO where
every level is masked (NEISO, tie at the top), one where the top two clear (NYISO), and the
measured response either side of the line.

**Two further readings, both reportable findings rather than gate outcomes.**

1. **Clearing the mask by $10 and by $20 buys the same renewables.** `CES-T80` and `CES-P60` both
   build **+156.6 MW of solar in 2030 and nothing else renewable**, despite a 20 % difference in
   attribute price. Over this range the fold is a step, and the campaign should not read
   "unmasked ⇒ elastic".
2. **The masked rungs are not inert, and reading the entry null as "the CES row is not wired" would
   be wrong** — which is exactly the alternative reading S15 says the bracket exists to falsify.
   `CES-P30` still cuts 2030 CO2 by **4.60 Mt in-ISO and 7.10 Mt leakage-inclusive**, entirely
   through the CCS retrofit screen, whose RPS leg **is** fuel-gated to `{wind, solar}` so a
   `gas_cc_ccs` unit's attribute price is the premium alone with nothing to mask it. The mask is
   specific to the *entry* fold.

**And the asymmetry cuts the other way too, which is the §4.2 result:** the CES **target row's**
dual reaches the entry fold and the retirement screen but **not** the CCS retrofit screen, so
`CES-T80`'s $50 buys **0.0 MW** of retrofit where `CES-P20`'s $20 buys 1,475.8 MW. On NYISO the two
CES instruments are not stronger and weaker versions of each other — they act on different screens.

### 7.3 The voluntary axis: NEISO and NYISO bracket the volume regime, and both return the same null

My own phase 0 called NYISO "the voluntary row's structural inverse" of the ERCOT reading
(eligibility). Against **NEISO** the inverse is on the **volume** limb, and it is the sharper
comparison, because the two ISOs sit on opposite ends of the one parameter that separates `mid`
from `high`.

| | **NEISO** | **NYISO** |
|---|---|---|
| `DATACENTER_ADDITIONS_MW[ISO]` | `{}` — **`E_DC` is exactly 0** | a real, growing DC layer: **`E_DC` = 3.641 → 12.777 TWh** (DC-mid) |
| what separates `VOL-MID` from `VOL-HI` | only `f_commit` (0.5 → 1.0), which multiplies zero — `s_base` = 0.08 on both paths | `f_commit` on a large `E_DC`: **V = 13.86 → 18.29 vs 15.68 → 24.68 TWh** |
| the *volume* delta between the two arms | **0.000 TWh in every year** (V = 8.4289 … 8.6828 TWh in both) | **+1.820 / +2.962 / +4.105 / +5.246 / +6.389 TWh** (up to **+35 %**) |
| row regime | binds 2026–2028, **slack 2029–2030** | **binds in all five years of both arms** (V/G = 1.4 – 3.4×) |
| what the pair measures | a **pure $4.50-vs-$7.00 WTP-ceiling ladder with no volume confound** | the **same ceiling ladder carried on a 35 % volume step** |
| measured difference between the arms | byte-identical in every reported scalar, fuel and capacity column, all five years; only the dual differs | **byte-identical in the headline, by-fuel and curtailment frames, all five years**; the only difference anywhere is by-zone CO2 attribution, max \|Δ\| **2.9e-5 Mt**, per-year Σ\|Δ\| ≤ 5.8e-5 Mt |
| effect on emissions / deployment | none | none — max \|ΔCO2\| vs REF **0.0031 Mt**; deployment identical to REF |

**Same instrument, opposite volume regime, same answer.** NEISO's null was strong but ambiguous: with
V identical in both arms the pair could not distinguish *"the WTP ceiling does nothing"* from
*"the volume never moved"*. **NYISO removes that ambiguity.** Here the volume moves by up to 6.39
TWh — more than half the entire eligible fleet's annual output — and both the ceiling **and** the
volume produce a difference of 2.9e-5 Mt of zone-attributed CO2 and nothing else. So the campaign's
combined reading is stronger than either ISO's:

> On a program ISO whose voluntary row is in **escape**, neither the WTP ceiling (S9's `mid` vs
> `high` cell) nor the committed volume (S9's `f_commit` cell) has any LP consequence. The escape
> is a bound; once the row is on it, the row's parameters price a certificate and change no
> dispatch, no build and no emission. The instrument's whole NYISO content is the **dual, the
> escape volume, and the crediting convention** — never an emissions response.

The mechanism composes with §7.1: even if the row *were* to reach a screen, its ceilings ($4.50 /
$7.00) sit far under NYISO's $40 RPS escape, so the entry fold could not see them either. Routed to
open card **D-3c** beside the eligibility tail (§9 item 2).

---

## 8. STAGE-B SEED — `CAP-STATE-TIGHT` on NYISO, beside NEISO's

**Ruling S17 (2026-09-07, desk card D-13) drops this case from Stage A and routes it to Stage B.**
The leg was solved and registered before the ruling reached this lane. Per S17 it **stays
registered** (un-registering strands a bundle and reddens the parity gate), it is **excluded from
§3's Stage-A gate scoring, from §0's headline and from the plan §5.1 rows**, and it is reported
here as Stage-B seed evidence. **Ruling S12's level is not withdrawn — only the stage moves.**
Nothing was re-solved and nothing was deleted. Run id
`nyiso-2026-2030-scn-campaign-policy-2026-09-06-cap-state-tight`, key `76c60ac152400146`.

### 8.1 The measurement

| year | budget Mt (S12) | `emissions_mt` | rel. gap | `co2_cap_price` $/t | REF RGGI adder $/t | ΔCO2 vs REF | import CO2 Mt | Δimport | ΔTOTAL | `avg_price` $ | `peak_price` $ | `unserved_mwh` | `n_co2_caps_binding` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 23.16 | **23.1600** | 0.0e+00 | **26.9792** | 23.6363 | **−0.5323** | 10.8260 | +0.3712 | −0.1611 | 50.50 | 71.00 | 0.0 | 1 |
| 2027 | 22.42 | **22.4200** | 0.0e+00 | **47.1569** | 25.2908 | **−2.1711** | 11.7265 | +1.5709 | −0.6002 | 56.64 | 80.24 | 0.0 | 1 |
| 2028 | 21.68 | **21.6800** | 0.0e+00 | **186.3067** | 27.0612 | **+4.5170** | 12.9350 | +2.3957 | +6.9127 | 114.14 | 167.37 | 0.0 | 1 |
| 2029 | 20.94 | **20.9400** | 0.0e+00 | **70.4527** | 28.9555 | **+7.2318** | 12.5814 | +2.7702 | +10.0020 | 64.71 | 96.29 | 0.0 | 1 |
| 2030 | 20.20 | **20.2000** | 0.0e+00 | **4130.3483** | 30.9824 | **+9.2970** | 12.9350 | +1.8604 | +11.1574 | **1412.71** | **2000.00** | **1,566,947.7** | 1 |

**G10 PASS** — emissions equal the budget **exactly** (0.0 relative, to the printed digits) in all
five years, with `n_co2_caps_binding` = 1 and a strictly positive dual throughout; there is no slack
year to test the dual-is-zero limb against. **G11 PASS, pre-solve** — the resolution carries a
`cap_spec` with `price_adder is None` and `resolve_carbon_price` = 0.0000 in all five years, so the
row **replaces** the RGGI adder and never composes with it. **G12** reports the price-vs-quantity
comparison as the case exists to produce it, and **the NYISO dual is ABOVE the adder it replaced in
every year** (1.14× → 133×).

**I3 (unserved/dump) FAILs on 2030** — slack 0.97 % of load, 1,089 h, 1,566.9 GWh, peak 5,505 MW —
and is declared in `frontend/data/hindcast/invariant-failures.json` in the registration commit per
the Y-24 ratchet. **I14 reads WARN, not FAIL** (2028 LW $117.2 and 2030 LW $1,687.5 outside
[0.5×, 3.0×] CC MC $31.0) and is therefore not declared. The other 12 invariants PASS.

**The mechanism, which P-15 and P-17 pre-registered and which the by-fuel frame confirms:**
`gas_cc_ccs` is **0.0 MW and 0.0 TWh in every year** of this case, against REF's
2,984 / 5,256 / 6,256 MW and 22.8 / 30.0 / 37.4 TWh. The cap sets the carbon price to zero, the CCS
retrofit screen closes completely (capx D50's asymmetry, measured here from the opposite side), and
the ISO meets the budget by burning unabated gas up to the cap and then — in 2030 — by **shedding
load**, because a mass cap has no safety valve.

### 8.2 NYISO beside NEISO — the two ISOs that have actually solved it

| | **NEISO** | **NYISO** |
|---|---|---|
| binds | all five years | all five years |
| emissions = budget | to 3.2e-13 relative | to 0.0 relative |
| ΔCO2 vs REF | **+2.91 to +13.91 Mt** (loosening in **all five** years) | **−0.53 / −2.17** then **+4.52 / +7.23 / +9.30 Mt** (tightening 2026–27, loosening 2028–30) |
| cap dual vs the RGGI adder it replaces | **12.23 → 8.26 vs 26.05 → 34.15 $/t — BELOW, in every year** | **26.98 → 4130.35 vs 23.64 → 30.98 $/t — ABOVE, in every year** |
| `gas_cc_ccs` under the cap | 0.0 in 2026–28, **2.78 / 0.93 TWh survives** in 2029–30 | **0.0 in all five years** — the screen closes completely |
| clean capacity vs REF | **less** (2030 `builds_renew` 287.4 vs 1198.0 MW) | **equal** (builds and `vre_mw` identical to REF in every year) |
| import line | **falls** −0.53 to −0.94 Mt (unpriced domestic gas undercuts imports) | **rises** +0.37 to +2.77 Mt (the cap pushes generation across the seam) |
| reliability | `unserved_mwh` 0.0 in all five years | **1,566.9 GWh unserved in 2030**, LW $1,687.5, avg $1,412.71, peak at the $2,000 cap |
| headline reading | *a quantity instrument named TIGHT that is a policy **loosening*** | *a quantity instrument that is **simultaneously a loosening on emissions and a reliability event**, because it removes the abatement driver and then has no safety valve* |

**The two ISOs disagree on the dual's sign relative to the price it replaces, and they do so for a
reason worth a Stage-B card.** NEISO's budget (18.0 – 20.67 Mt) sits far above its REF trajectory
(4.76 – 17.10 Mt), so the row is cheap to satisfy and its dual is small. NYISO's budget
(20.20 – 23.16 Mt) sits *below* its carbon-zero counterfactual in every year, and by 2030 the gap
between "what an unabated NYISO fleet emits" and "what the S12 glide allows" is wide enough that
the LP prices the last tonne at **$4,130/t** and sheds 1.57 TWh rather than emit it. **Same
instrument, same glide construction, opposite dual sign and opposite reliability outcome** — which
is the strongest argument the campaign has produced for S17's own reasoning that this instrument
belongs on a horizon long enough for its glide to bite, and is worth less inside a five-year window.

**What this seed does NOT license.** No Stage-A determination, gate or §5.1 row is derived from
this leg. Its 2030 price and unserved numbers are a *result of the case*, not a defect in NYISO's
REF, which carries zero unserved and zero scarcity hours in every year (§3, G2).

---

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

Parent PRECOMMIT §9 items 1–4 and ADDENDUM 2 §8 items 5–7 stand. Added or sharpened:

1. **THE CES TARGET ROW CANNOT REACH THE CCS RETROFIT SCREEN, AND THE CES PREMIUM CAN. This is a
   footprint-wide seam, measured on NYISO.** `ccs.py:475-476` prices the retrofit uplift with
   `effective_eac_price_for_unit` = `max(legacy eac_price_*, premium × credit)`; it never reads
   `clean_attribute_price_by_fuel`, which is where a target-row dual lives and which both
   `new_entry.py` and `retirements.py` do read. Consequence measured here: `CES-T80`'s $50 ACP buys
   **0.0 MW** of retrofit while `CES-P20`'s $20 premium buys **1,475.8 MW** at 2030. On any ISO
   whose CES response runs through CCS, a target-row case and a premium case are **not** comparable
   as "the same instrument at different levels", and a campaign that reads them that way will
   under-state the target row. Not a defect judgement — the max() attribute doctrine is deliberate
   (rule 19 `[R-ONE-MECH]`) — but the *coverage* difference between the two folds is worth an owner
   look beside ADDENDUM 2 §8 item 5's entry/retirement asymmetry. Neither `ccs.py` nor
   `federal_ces.py` is this lane's region and neither was touched.
2. **D-3c now has all three tails, and NYISO supplies the volume one.** ERCOT: the row can never be
   live under all-eligible crediting (eligible fleet ≫ V). NYISO §1.2: an ISO that is 39 % clean has
   the row bind at V/G = 1.4–3.4× because hydro and nuclear carry its clean share and neither is
   eligible. NYISO §7.3: with a 35 % volume step between the two committed paths, **both the volume
   and the ceiling are measurably inert once the row escapes** — which is a statement about the
   *escape*, not about the levels, and it argues that D-3c's crediting leg (new-builds-only vs
   all-eligible) is the only limb of that card that can change any of these answers.
3. **The S15 threshold is now bracketed on two sides and should be stated as a level, not a null.**
   `STATE_RPS_ACP` reads MISO 30, **NYISO 40**, PJM 45, CAISO 50, NEISO 50, ERCOT absent. NYISO
   measures the entry response at 40 (zero), 50 (+156.6 MW) and 60 (+156.6 MW solar **+ 500.4 MW
   nuclear**). The remaining lanes can therefore predict their own null/live split from their ACP
   *before* spending a leg, and the campaign can report a threshold rather than five nulls.
4. **A policy campaign's duals are not recoverable from its committed artifacts, and the S16 shard
   split made that binding.** `clean_region_duals` and the RPS/clean row duals are written only to
   the cached year bundle (`results/<ISO>/<key>/`, gitignored) and the solver log; the slim summary
   carries `rps_dual` alone and the sidecar carries neither. Under S16 each shard's bundles died
   with its container, so **G4's and G7's dual limbs are unscorable at the coordinator by
   construction** — this lane scored their *identities* from credited shares and escape volumes
   instead, which is sound but is not what the gates say. Cheap fix for a successor: have
   `run_ces_leg.py` copy `clean_region_duals` / `co2_cap_price` into `full_horizon_summary.json`'s
   trajectory rows beside the `rps_dual` already there. `scripts/run_ces_leg.py` is not this lane's
   region.
5. **`register_forecast_run.py` drops `set_overrides` into the sidecar as `null`.** ADDENDUM 2 §6.3
   stated the `ces-p60` sidecar would carry `meta.set_overrides:
   {federal_ces_premium_usd_per_mwh: 60.0}`; it reads `null`. The bundle is unaffected
   (`full_horizon_summary.json` and `run_config.json` both carry the override and the resolved
   60.0) and the run is still self-describing through `meta.case: CES-P60` plus its distinct key,
   so nothing is mis-registered — but a `--set`-constructed leg is **not** self-describing from the
   dashboard alone, which is where a reader looks first. Reported against interest.
6. **NYISO's leakage line passes 100 %.** REF's `import_co2_mt_reported` is 101.6 % of its in-ISO
   `emissions_mt` at 2030 (11.075 vs 10.903 Mt) and 44–72 % before that; on `CES-P60` at 2030 the
   import cut is 88 % as large as the in-ISO cut. Beyond the disclosure duty this says NYISO's
   campaign CO2 deltas measure roughly half the emissions the ISO's consumption is responsible for.
   Carries to the leakage card with a hard number.
7. **`CAP-STATE-TIGHT` needs a separate LP budget wherever it is run** — 12.87 min/solve-year here
   and 14.57 on NEISO, against 1.05–6.17 for every other arm in both lanes (§6). A Stage-B charter
   sizing shards from an ISO's Stage-A min/solve-year will under-budget it by 2–12×.

**Nothing outside this lane's declared regions was edited.** No `src/`, no `scripts/`, no
`configs/`, no `.github/`, no other ISO's matrix shard, no `program-status.json`, no
`ff-verdicts.json`, no backcast namespace file.

---

## 10. Files, and what was verified before anything was written

### 10.1 The ten registered legs, verified present on `main` at close

Verified by `git ls-tree -r --name-only origin/main -- frontend/data/hindcast/`, not by claim.
All ten sidecars `nyiso-2026-2030-scn-campaign-policy-2026-09-06-<slug>.json` are on `main`:
`all-clean`, `cap-state-tight`, `ces-p10`, `ces-p20`, `ces-p20-vol-hi`, `ces-p30`, `ces-p60`,
`ces-t80`, `vol-hi`, `vol-mid`. Their bundles are committed under
`results/scn-campaign-policy-2026-09-06/NYISO/<CASE>/` (slim summary + `run_config.json` + the four
absolute report frames), together with the two unregistered controls `REF` and `LOAD-HI`.
**Cross-checked against the PRECOMMIT §2 / ADDENDUM 2 §2 case set: ten surviving cases, ten
registered legs, zero missing.** The single solve this session was permitted to spend on a missing
case was therefore not needed and **no LP was run**.

Every leg's key matches its pre-declared key exactly:
`3c96d694c18e5547` · `9da7c76372c98406` · `89a70dd1140c6731` · `c3013cc6087bd2aa` ·
`eb1b0e1df942db47` · `e13b0d801b1ffce1` · `9528d708b81b5074` · `893acae55a1a898f` ·
`566335c8ca37dc17` · `76c60ac152400146`, plus the controls `f10cc93084b4c0db` and
`c2ceaefa4afafcda`. Provenance re-verified per §1.8.

### 10.2 Written by this session

- `docs/handoffs/FINDING-scn-ws5a-policy-nyiso-2026-09-07.md` (this document)
- `docs/handoffs/scn-ws5a-policy-nyiso/score_gates_2026-09-06.json` (the committed scorer's output)
- `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §5.1 rows 3 and 7, NYISO cells only
- `docs/handoffs/scenario-desk-ledger-2026-09.md` §3, the same two rows (the plan's mirror)
- `docs/codebase-site/data/mechanism-matrix/NYISO.js` — **NYISO's shard only**, four cells:
  `federal_ces`, `federal_ces_target`, `voluntary_clean_demand`, `carbon_price_path`

### 10.3 Duties

- **No default moved, no knob moved, no `ScenarioConfig` field added, no CI workflow created, no
  solve run.** **DOF ledger: ZERO free parameters** — `CES-P60`'s $60 is a scenario axis level
  identified from the published ACP table, declared ex ante in ADDENDUM 2, common to every ISO, and
  never swept against a gate.
- No `authorized_price_tuning` block (a backcast offer-curve channel; untouched).
- **Backcast byte-identity: untouched by construction** — every leg is `mode="forecast"`.
- **Rule 29(c):** this lane produced no screen bundle and no control bundle. `REF` and `LOAD-HI` are
  rematerializations of committed, registered configs, are not registered by this lane, and are not
  screens or controls in rule 29's bundle-retention sense.
- **Rule 27:** no existing source file ≥300 lines was rewritten; every push touching one is verified
  by fetch-back.
- **Rule 15 / forecast plan §7.5:** this lane registers into the forecast namespace only; the whole
  backcast namespace is untouched.
