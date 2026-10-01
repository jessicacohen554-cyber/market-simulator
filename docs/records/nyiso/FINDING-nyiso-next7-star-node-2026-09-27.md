# FINDING — NYISO-NEXT-7: the external star node (ZERO LP, ZERO SHARDS)

- **Question.** Does NYISO's single `NYISO_external` node let import move between neighbours in a way
  the real seams cannot, and is a per-neighbour routing lever admissible with zero free parameters?
- **Verdict.** The node is fully fungible (87–100 % of the NEXT-6 Long Island cut re-routed). But the
  keeper's standing error is the **opposite** of the NEXT-6 hypothesis: Zone A is **under**-supplied
  and import is **over**-delivered **east** of Central-East. **No per-neighbour lever is identifiable
  at zero DOF from data in the repo.** Refused on identification (rules 20/21). No solve, no keeper
  change.
- **Probe.** `scripts/probes/nyisonext7_star_node_phase0.py` → `results/calibration/_nyisonext7_phase0.json`.
  Control = the NEXT-3 keeper hourlies read from git (`8227c1f3^`).

## 0. G-DRIFT (keeper `git_sha` 671fa815 → HEAD 571147d0)

8 files move on the backcast path. **All INERT for NYISO:**

| hunk | why inert |
|---|---|
| `zone_assignment.py` DAM-membership admission | gated `iso == "ERCOT"` |
| `data/raw/reference/*` (3 CSVs) | ERCOT crosswalk / bin rows |
| `scenarios.py`, `outages.py`, `fleet/arrays.py`, `resolved_inputs.py` | `unit_outage_full_rederive`, default off, absent from the keeper recipe |

No solve was run, so form 4 was never needed.

## 1. The committed sidecars cannot answer the question directly

- The hourly sidecars have zone prices and the aggregate `import` class only. **There are no per-link
  flows** (those are in gitignored `dispatch/` / network files).
- **The per-tranche per-link question is ill-posed anyway.** The ladder is a Q-Q derivation on
  **total** net import (`derive_nyiso_import_tranches.py`). The rung names are depth markers, not
  neighbours. No rung has a neighbour identity to route.
- **Bounded analytically instead, with no shard.** A border link is at its import cap when its zone
  price is above `NYISO_external`'s, and at its export cap when it is below. Links are lossless:
  Upstate_West is interior in 98 % of 2021 hours. Caps are the keeper's own: the PAR-attributed p90
  envelope, with LI clipped at its posted limit. That rebuilds every at-bound flow exactly.

## 2. Phase-0 numbers

**Re-route of the NEXT-6 Long Island cut** (arm vs NEXT-3 control, aggregate import class):

| year | LI cut TWh | Δ total import TWh | re-routed | Upstate_West Δ$ (lw) |
|---|---|---|---|---|
| 2021 | 0.160 | 0.000 | 100 % | −0.24 |
| 2022 | 0.343 | 0.000 | 100 % | −2.02 |
| 2023 | 0.268 | −0.001 | 100 % | −0.09 |
| 2024 | 0.269 | 0.000 | 100 % | −0.03 |
| 2025 | 0.308 | −0.039 | 87 % | −0.07 |

**Share of hours each border link is at a bound** (keeper): Capital_Hudson 1.00 / 1.00 / 0.80 /
0.65 / 0.63, NYC 0.93–1.00, LI 0.96–1.00, Upstate_West 0.02 / 0.14 / 0.45 / 0.52 / 0.62. Upstate_West
is the node's only interior link, so it takes any MW the others release.

**Rebuilt link flow vs NYISO's own attributed P-32 schedule** (mean MW over at-bound hours;
excess TWh/yr):

| year | Capital_Hudson model / meas (TWh) | NYC model / meas (TWh) | LI model / meas (TWh) | Upstate_West ≤ model UB / meas (TWh) |
|---|---|---|---|---|
| 2021 | +236 / −295 (+4.65) | 840 / 621 (+1.92) | 734 / 617 (+1.03) | ≤1,321 / 2,165 (≤ −7.40) |
| 2022 | +280 / −177 (+4.00) | 886 / 684 (+1.77) | 867 / 748 (+1.04) | ≤1,146 / 1,825 (≤ −5.95) |
| 2023 | +362 / −182 (+3.80) | 979 / 726 (+2.19) | 957 / 844 (+0.99) | ≤527 / 1,247 (≤ −4.97) |
| 2024 | +277 / −216 (+2.79) | 907 / 739 (+1.44) | 941 / 802 (+1.21) | ≤587 / 1,268 (≤ −3.74) |
| 2025 | +259 / −164 (+2.33) | 990 / 803 (+1.53) | 888 / 770 (+0.99) | ≤521 / 1,050 (≤ −2.59) |

The Upstate_West column is an upper bound: node supply minus the three at-bound links, over the hours
all three are at a bound (8,760 / 8,760 / 6,907 / 5,502 / 4,893). Export sinks (≤ 600 MW) would only
lower it.

- **Model total import ≈ measured net import** (3,130 / 3,179 / 2,662 / 2,347 / 2,204 MW vs 3,108 /
  3,080 / 2,546 / 2,360 / 2,197). The level is right. The **location** is wrong.
- **Capital_Hudson imports at its cap where NYISO's own schedule is a net export.** The measured NE
  AC tie exports 400–668 MW/yr on average. A pooled node priced below the eastern zones can only
  import. It cannot hold the NE export and the HQ/IESO import at once.
- **Net effect:** 4.8–7.6 TWh/yr (7.60 / 6.81 / 6.98 / 5.44 / 4.85) of import lands east of Central-East that NYISO actually received
  in Zone A, or exported to NE. That is the nyiso-125 defect, and PAR attribution only partly closed
  it.
- **Reframes NEXT-6 G-4.** The 0.343 TWh the LI clip freed in 2022 moved Upstate_West **toward** its
  measured volume. The Zone A price drop is real, but it is not import Zone A "cannot physically
  receive". The standing object is the eastern over-delivery.

## 3. Identification (rules 13/14/20/21)

**(a) Tie tranches to the links their ties land on — REFUSED.** No tranche has a neighbour identity
(§1). Any tranche-to-link assignment is a free choice.

**(b) Per-neighbour node split under the frozen Q-Q formula — REFUSED (misaligned, rule 14).** The
formula pairs flow and NY DA price monotonically. That holds only where a neighbour's flow co-moves
with the NY price. Spearman ρ, hourly net import vs NY DA zonal-mean LBMP:

| year | HQ | IESO | PJM AC | PJM DC | NE AC | NE DC | aggregate |
|---|---|---|---|---|---|---|---|
| 2021 | +0.18 | +0.09 | +0.49 | +0.48 | **−0.25** | −0.05 | +0.37 |
| 2022 | +0.42 | +0.30 | +0.29 | +0.26 | **−0.31** | −0.10 | +0.38 |
| 2023 | +0.23 | +0.08 | +0.33 | +0.33 | **−0.34** | +0.02 | +0.30 |
| 2024 | +0.33 | +0.18 | +0.20 | −0.03 | **−0.23** | −0.11 | +0.25 |
| 2025 | +0.23 | +0.17 | +0.35 | +0.13 | **−0.32** | −0.33 | +0.28 |

- NE AC is anti-monotone in all 5 years.
- IESO and PJM DC are near zero in several years.
- These flows are set by the **spread** to each neighbour's own price, not by the NY price. The
  aggregate Q-Q coupling was admissible only because the model has one node (rule 14).
- The per-neighbour grid (firm base, rung count, depth) also has no measured per-neighbour analogue.
  The 4,350 MW SIL is simultaneous.

**(c) Per-neighbour spread ladder (`seam_neighbour_hourly_ladder` class) — NOT identifiable today.**
It needs measured data the repo does not hold:

1. **IESO:** Ontario hourly price (HOEP / OZP), 2021–2025.
2. **PJM:** PJM DA/RT LMP at the NYIS interface pricing node, plus the Neptune/HTP/VFT source pnodes.
   The `pjm-zonal-lmp` payload is gitignored and carries no interface pnodes.
3. **ISO-NE:** DA/RT LMP at the NY external nodes (Roseton AC, Shoreham CSC, Northport 1385). SMD
   carries only zones and the hub.
4. **HQ:** no market. The only measured object is the NYISO_HQ proxy (NY-side), which is not a
   neighbour price.
5. **Export side:** each neighbour node also needs an export sink derived the same way.

With (1)–(3) in hand, the MISO/PJM spread construction transfers in kind only (rule 25). Its offsets
must be re-derived from NYISO's own flows. HQ would stay a firm/proxy block.

## 4. Side defect found (not this lane's lever)

**`SCH - HQ_IMPORT_EXPORT` is double-counted in the aggregate ladder derivation.**
`derive_nyiso_import_tranches.EXTERNAL_SEAMS["HQ"]` lists it next to `SCH - HQ - NY`. It is an
accounting duplicate: corr 0.977–0.993 in all 5 years, and `nyiso_par_attribution.ACCOUNTING_DUPLICATE`
already treats it as one.

- **Net import the committed rungs were derived on:** 3,979 / 3,786 / 2,694 / 2,146 / 1,671 MW.
  The true figure is 3,108 / 3,080 / 2,546 / 2,360 / 2,197 MW (2021–2025).
- **The committed formula reproduces the committed rungs exactly.** Re-derived without the duplicate
  (offline, zero LP), 2022 goes $25.16 / 34.27 / 41.12 / 46.94 / 53.35 / 62.59 / 126.79 →
  $23.63 / 36.06 / 44.20 / 52.54 / 64.64 / 86.91 / 174.89.
- **2025** goes $31.32 / 44.09 / 59.82 / 79.19 / 102.99 / 128.54 / 208.77 →
  $20.40 / 30.75 / 43.15 / 65.77 / 105.83 / 153.51 / 242.96.
- **This is a derivation error**, a rule-14 correction whose cause is independent of any residual
  (rule 23 cites the defect, not a price miss). It re-keys every NYISO year, so it needs its own
  PRECOMMIT and A/B. It is routed to the next lane.

## 5. Record

- Matrix shard `NYISO.js`:
  - `seam_neighbour_anchored_ladder` U → **G** (identification; reopens only on intake of §3(c) data).
  - `seam_neighbour_hourly_ladder` stays **U**; precondition not met, evidence appended.
  - `import_hub_pricing` stays **K**; the §4 defect is appended.
- Retrievability: nothing was solved, so there is nothing to promote. The probe and its JSON are on
  `main` with this PR.
