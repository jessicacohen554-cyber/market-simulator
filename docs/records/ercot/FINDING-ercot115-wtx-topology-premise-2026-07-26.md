# FINDING — ERCOT-115 Task B: the West/Panhandle "topology split" is already built, and the corridor interfaces are already at their measured limits

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 · **No LP** ·
**Probe** `scripts/probes/ercot115_wtx_topology_gtc.py` ·
**Source** `data/raw/iso-specific-transmission/SCEDBTCNP686_SCEDBTCNP686_{2023,2024,2025}.parquet`
(ERCOT NP6-86 SCED Shadow Prices and Binding Transmission Constraints; 308,300 SCED intervals)

## Summary

The ERCOT-115 charter promoted the West/Panhandle topology split to head of the wind lane and
specified it as: *"split West/Panhandle into separate model zones with their own link + TTC so the
corridor limit is represented, rather than collapsed into one wide West→North pipe that almost
never binds."* **Three of that sentence's four premises are false on the committed data**, and the
fourth — that the corridor limit governs — is true but already implemented. Reported before doing
the work, per the standing instruction to state a real problem with the task and then deliver.

| charter premise | status |
|---|---|
| West and Panhandle are collapsed into one zone | **FALSE** — separate `Zone`s since the 7-zone topology (`iso_configs.py:186–187`) |
| The corridor has no link + TTC | **FALSE** — `West→North` 7,300 · `West→South_Central` 2,700 · `Panhandle→North` 2,680 MW (`iso_configs.py:224–226`) |
| The West→North pipe "almost never binds" | **FALSE** — WESTEX binds 7.1–10.7 % and PNHNDL 8.2–12.1 % of SCED intervals |
| The corridor limit is the binding defect | **TRUE, and already represented** at its measured limit-at-bind |

**This was already adjudicated in-repo.** `docs/handoffs/ercot-vre-curtailment-topology-scope-2026-07.md`
(2026-07-07) scoped exactly this work as **WP-A**, measured its expected yield as **~zero**, and
recommended **defer**. This session re-tested that conclusion on all three years (the doc's evidence
was 2024 only) and it holds — see §3, which also finds new Far West GTCs the doc could not have seen.

## 1. The corridor interfaces are already at their measured limits

Median **limit-at-bind** (the limit in the intervals where the constraint actually constrained):

| GTC | 2023 | 2024 | 2025 | model | verdict |
|---|---|---|---|---|---|
| **WESTEX** | 10,038 MW (7.8 %) | 10,275 MW (10.7 %) | 10,109 MW (7.1 %) | **10,000** (7,300 + 2,700) | matched |
| **PNHNDL** | 2,524 MW (8.2 %) | 2,670 MW (12.1 %) | 2,397 MW (9.9 %) | **2,680** | matched (model ~6 % generous vs the 3-yr pooled 2,530) |
| **NE_LOB** | 1,245 MW (24.1 %) | 1,245 MW (11.0 %) | 1,566 MW (11.4 %) | **1,300** export | matched |
| **N_TO_H** | 5,024 MW (0.3 %) | 4,834 MW (0.1 %) | 4,635 MW (0.3 %) | **8,000** | deliberate carve-out (one of several parallel 345 kV paths; rule 14 misalignment clause) |

There is no measured corridor limit for this topology to adopt that it does not already carry.

## 2. The PNHNDL "17 % under-representation" is a basis artifact, not a model error

The scope doc's table quotes PNHNDL median limit **3,239 MW** for 2024 against the model's 2,680 —
which reads as the model under-representing the corridor by 17 %. It is not:

| basis | PNHNDL 2024 |
|---|---|
| median `Limit` over **all** rows | **3,239.3 MW** ← the doc's figure |
| median `Limit` over **binding** rows | **2,670.0 MW** ← the model's basis |

The all-rows median includes the ~78 % of PNHNDL rows that are monitored-but-not-binding, which
carry the constraint's *unconstrained* rating. The transfer limit a zonal link should represent is
the limit at bind. On that basis the model's 2,680 is right to within 0.4 % for 2024. The doc's
binding-*frequency* column (12.1 %) reproduces exactly, so only the limit column is off-basis.

The gap is PNHNDL-specific — WESTEX, NE_LOB and N_TO_H differ by 0–164 MW between the two bases —
which is why the discrepancy looked like a real signal in a table mixing them.

## 3. No additional interface-scale GTC sits behind the corridor (now on 3 years, not 1)

The scope doc's "no additional interface-scale GTC" claim rested on 2024 alone. 2025 introduces
four West-Texas-geography GTCs it could not have seen — and they do not overturn it:

| GTC | geography | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| MCCAMY | McCamey (Permian) | 0.7 % | 0.0 % | **2.1 %** |
| CULBSN | Culberson Cty (Far West) | — | 0.3 % | 1.0 % |
| **I_FW_N** | **Far West North** | — | — | **2.8 %** (1,087 MW) |
| I_FW_S | Far West South | — | — | 0.1 % (2,774 MW) |

The most any of them binds, in any year, is **2.8 %** — against WESTEX's 7.1–10.7 % and PNHNDL's
8.2–12.1 %, and against the nodal tail in §4. A `Far_West` split would relocate generation behind an
interface that binds 2.8 % of intervals in one year of three. That is the copper-plate no-op that
reverted the original Far_West zone, now measured on three years instead of asserted.

**Worth flagging forward, not acting on now:** `I_FW_N`/`I_FW_S`/`CULBSN` are *new* — absent in
2023–24, present in 2025. If their binding frequency keeps climbing, the WP-A recipe (already
written out, five touch-points, `topology-scope §WP-A`) becomes live. Re-run this probe when the
2026 archive lands. That is a data-driven trigger, not a schedule.

## 4. What a zone split cannot reach, at any granularity

| year | SCED intervals | ≥1 constraint binds | interface GTC binds | nodal binds | **NODAL-ONLY** | distinct nodal |
|---|---|---|---|---|---|---|
| 2023 | 98,787 | 84.5 % | 48.1 % | 78.4 % | **36.4 %** | 515 |
| 2024 | 103,691 | 88.8 % | 41.6 % | 85.0 % | **47.2 %** | 549 |
| 2025 | 105,822 | 94.4 % | 56.3 % | 90.2 % | **38.1 %** | 599 |

**NODAL-ONLY** = a station-to-station constraint binds while **no** interface GTC binds at all:
**36–47 % of every SCED interval in the year.** Those are single 138/345 kV elements with 30–500 MW
limits (BURNS_RIOHONDO 184 MW, LARDVN_LASCRU 273 MW, HAINE_LA_PAL 211 MW, 6520__E 217 MW, …),
515–599 distinct per year. Representing them zonally would need hundreds of zones, and each caps one
line, not an interface. **No zone split reaches this congestion** — which is the majority of it.

## 5. Where the wind lane actually goes

The scope doc's WP-B is the route, and its **nodal layer is the unbuilt piece**:
aggregate the station-to-station binding rows — today dropped by `curate_gtc_limits._gtc_only` —
whose stations sit in West/Panhandle/CREZ geography into a measured curtailment-pressure frequency,
on the same net-load × hour × season axis the existing `ercot_wtx_curtailment_driver` already uses.
It needs a **station → area crosswalk**, which the repo does not yet have; the archive carries
`FromStationkV` to filter to the 138/345 kV elements that curtail wind. That is a `data-intake`
job (schema-first, `write_clean`/`read_clean`), not a topology edit.

This also reconciles ERCOT-114's attribution. Its "86–89 % of the level effect is TOPOLOGY" is
correct as stated — the depth is a minor actor and congestion is the dominant one — but "topology"
there means the **sub-zonal nodal network**, not the zonal corridor split. ERCOT-114's Panhandle
price collapse (−3.15 → −3.27 $/MWh) is the *already-modelled* PNHNDL link binding at its measured
2,680 MW, which is the model working, not a missing zone.

**Consequence for the wind lane:** the per-zone wind shape (`ercot_wind_zone_shape`) stays
**unrefuted and unadopted**, but it is **not** blocked on a topology split, because there is no
admissible split to do. It is blocked on the nodal layer. ERCOT-114's statement that the shape
"cannot be adjudicated until the corridor it loads is represented correctly" stands — the corridor
is represented correctly at interface scale *already*, and what remains unrepresented is sub-zonal
and unreachable by zoning.

## 6. Rules observed

No mechanism was reverted or weakened because a residual moved (rules 1/13/14): no TTC was changed,
no gate flipped, the keeper is untouched. The `ercot_wtx_curtailment_driver` stays armed and the
depth default stays 0.1004. The measured limits were preferred over estimates throughout (rule 14),
and the one apparent measured-vs-model gap was traced to a basis mismatch rather than buried in an
input (rule 14's misalignment clause — documented in §2, not silently reconciled). Nothing was
re-derived without a source-data change (rule 23); this is a *read* of the committed archive. No
out-of-training year was touched (rule 22): the scan covers 2023–2025 only.
