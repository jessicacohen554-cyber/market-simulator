# PREREG ADDENDUM 2 nyiso-127 — the attribution covers ALL FOUR border links, because attributing only `SCH - PJ - NY` is not implementable without a chosen number

**Filed BEFORE any solve.** No LP has run in this session. This is a
**scope expansion** of
`results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md` §5,
authorised by the owner on 2026-08-05 ("Expand scope: rebuild all four seam
caps") after Phase 0 established that the pre-registered scope cannot be built
without violating the parent's own §3. It is filed so the wider construction,
its DOF delta and its kill gates are on the record **before** any result exists.

Reads with: addendum 1
(`PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md`),
which changed the availability source and measured the split.

---

## §1 — the blocker, stated exactly

The parent PREREG §5 scopes the change to *"the zonal attribution of
`SCH - PJ - NY` only"* and leaves *"the armed downstate
`nyiso_seam_deliverability_envelope` … unchanged"*.

**That scope is not implementable.** The model hosts the entire NYISO seam on one
external star node (`NYISO_external`) with four per-zone border links carrying
flat static MW (`interchange.spec.IMPORT_NODE_LINKS["NYISO"]`: `Upstate_West`
3,000, `Capital_Hudson` 1,600, `NYC` 1,000, `Long_Island` 1,200). There is **no
per-neighbour structure on the NYISO seam at all** — `INTERFACE_NEIGHBORS` has
entries for PJM, MISO and CAISO only, and `INTERFACE_NEIGHBORS["NYISO"]` is
`None`. Each static therefore lumps PJM together with Hydro-Québec, Ontario and
New England.

To state "46 % of the PJM-AC schedule lands in Zone G" as a link cap, the PJM
component of that link must be separable. Separating it requires numbers that
exist only as **modelling choices in a code comment** — `IMPORT_NODE_LINKS`'s own
annotation gives `Capital_Hudson` as *"PJM Ramapo (~1,000 MW) + ISO-NE AC
(~600 MW)"*. Those are not published, not measured, and not derivable.

Parent §3's kill condition is unambiguous: *"if implementation requires any value
that is not [a published constant or a measured state], this pre-registration is
violated and the lane stops."* **Under the parent's scope as written, the lane
stops.** The owner was given that outcome as an explicit option and chose the
expansion instead.

## §2 — the expanded object, and why it needs no chosen number

**Rebuild every border-link cap from the measured P-32 per-neighbour schedules,
attributing each posted row to the model zone its ties physically land in.**
Every row is already intaken (`data/raw/NYISO/interface-flows/`, the
`nyiso-interface-flows` clean datatype), and every landing is a published tie
geography, not a modelling choice:

| P-32 row | NY-side ties | NYCA zone | model zone | basis |
|---|---|---|---|---|
| `SCH - OH - NY` | Ontario / Niagara | A–B | `Upstate_West` | Gold Book external interconnections |
| `SCH - HQ - NY` | Chateauguay–Massena | D | `Upstate_West` | same |
| `SCH - HQ_CEDARS` | Cedars Rapids | D | `Upstate_West` | same |
| `SCH - NE - NY` | New Scotland / Pleasant Valley AC | F–G | `Capital_Hudson` | same; already the cited basis of the incumbent `Capital_Hudson` static |
| `SCH - PJ - NY` | Ramapo + Waldwick + Goethals/Farragut + western AC | A, G, J | **split 46 / 7 / 47 hourly** | the NY-NJ PAR posting × published PAR availability (addendum 1) |
| `SCH - PJM_HTP`, `SCH - PJM_VFT` | HTP, Linden VFT | J | `NYC` | armed nyiso-125 map, unchanged |
| `SCH - PJM_NEPTUNE`, `SCH - NPX_CSC`, `SCH - NPX_1385` | Neptune, Cross Sound, Northport-Norwalk | K | `Long_Island` | armed nyiso-125 map, unchanged |
| `SCH - HQ_IMPORT_EXPORT` | — | — | **EXCLUDED** | accounting duplicate of `SCH - HQ - NY`, already flagged in `data.nyiso_seam_envelope.NYISO_SEAM_ACCOUNTING_DUPLICATE` |

The model's five zones aggregate NYCA A–K as A–E → `Upstate_West`, F–G →
`Capital_Hudson`, H–I → `Lower_Hudson`, J → `NYC`, K → `Long_Island`
(`iso_configs` NYISO docstring). `Lower_Hudson` has no external ties and
correctly has no border link.

The envelope construction is **unchanged from the armed nyiso-125 mechanism**:
within each (month × hour-of-day) bin, the `NYISO_SEAM_FLOW_PERCENTILE` (90.0,
the repo-wide definitional convention, pre-registered never-swept, identical to
`MISO_SEAM_FLOW_PERCENTILE` and `PJM_SEAM_FLOW_PERCENTILE`) of the
directionally-clipped attributed net. Source hours are binned by their OWN local
(month, hour); Feb 29 is dropped so a leap year contributes the model's calendar.

**No MW is chosen anywhere.** Every cap is a percentile of NYISO's own measured
schedules under a definitional convention, attributed by published tie geography
and published PAR shares.

## §3 — rule 19 `[R-ONE-MECH]`: this REPLACES the armed envelope, never stacks

The new mechanism computes `NYC` and `Long_Island` from the **same** measured
rows the armed `nyiso_seam_deliverability_envelope` uses, so running both would
be two mechanisms for one phenomenon. **They are mutually exclusive by
construction**: when `nyiso_seam_par_attribution` is on it computes all four
links and `nyiso_seam_deliverability_envelope` is not applied. The one
substantive difference on those two links is that `NYC` now also carries the ABC
AC share — a *different physical tie set*, summed before the envelope is taken,
which is composition of capability, not stacking of mechanisms.

## §4 — the DOF ledger delta

**`n_residual` must stay at 6.** Unchanged kill condition.

| entry | value | identification source | swept? |
|---|---|---|---|
| `nyiso_par_share_ramapo` / `_jk` / `_abc` / `_west` | 0.32 / 0.15 / 0.21 / 0.32 | NY-NJ PAR posting table 1 | never |
| PAR ↔ PTID identity (8) | published | P-33 `outSched` `Equipment Name` | never |
| PAR in-service state | measured | P-33 `outSched` windows | never |
| P-32 row → model zone (8 rows) | published | Gold Book external interconnections / NYCA zone aggregation | never |
| envelope percentile | 90.0 | `NYISO_SEAM_FLOW_PERCENTILE`, definitional repo-wide convention | never |

**`n_entries` rises; `n_residual` does not.** If any implementation step needs a
value outside this table, **the lane stops** — that remains the kill condition and
is not negotiable at the time.

Registry: `ScenarioConfig.nyiso_seam_par_attribution` (rule 24 `[R-REGISTRY]`),
in `run_config.json`, matrix row in the same PR (rule 28 duty c).

## §5 — blast radius, restated for the wider scope

* **In scope now:** all four `NYISO_external` border-link caps, rebuilt from
  measured per-neighbour P-32 rows; the PAR split of `SCH - PJ - NY`; a `NYC` AC
  path that does not exist today.
* **Untouched:** `NYISO_INTERFACE_TTC_BY_MONTH` / `_BY_YEAR` (internal
  interfaces — Tier-3 re-grounding is REFUTED/CONFIRMED-closed, nyiso-122/124);
  nyiso-100's retired 4,350 MW `NYISO_simultaneous_import` scalar, **not**
  re-installed and no aggregate cap introduced; every scarcity, ORDC, floor and
  reserve mechanism — **this construction carries no scarcity parameter**
  (rule 19).
* **Newly in scope versus the parent, and named as such:** the HQ, Ontario and
  New England seams are now re-homed by the same measured construction. This is
  the material widening the owner authorised, and it is why this addendum exists.
* All three years, one invocation, one bundle (rule 16); years sequential
  (rule 12); 2023-2025 only (rule 22).

## §6 — predictions: the parent's stand, with P2 already weakened

Parent §6 P1/P2/P3 are **not rewritten**. Restated with what Phase 0 now knows:

**P1** (unchanged) — `Capital_Hudson` stops being permanently bound and
Central-East utilisation moves further toward the measured 0.807 / 0.616 / 0.591
than nyiso-125's 0.668 / 0.335 / 0.383.

**P2** (unchanged text, **weakened threefold by measurement**) — zonal price
separation appears. Addendum 1 §4 measured the Zone-J share at **~7 %, not 21 %**,
so the mechanism by which P2 was expected to act is a third of its assumed size.
P2 will be scored against its original text.

**P3** (unchanged, and the honest one) — **this does NOT predict C3a-2025
closes.** nyiso-126 showed the −10.2 % is 138 % attributable to decile 10 and
nyiso-120 measured ~94 % of it as pre-existing. **If this arm closes C3a-2025
that is a surprise to be explained, not a success to be claimed.**

**P4 — NEW, and registered now because the wider scope creates it.** Re-homing
the HQ / Ontario / New England seams by measurement is a *bigger* change to
`Upstate_West` than the PAR split alone. The pre-registered expectation is that
`Upstate_West`'s import capability **falls** relative to its 3,000 MW static
(its measured p90 attributed envelope is the test), and that this is what drives
P1 rather than the PAR split by itself. **If `Upstate_West` instead RISES, the
attribution is not doing what §2 claims and that is a stop**, not a result to
bank.

## §7 — kill gates

Parent §7 K1–K7 stand as written and will be scored as written. K7 is already
discharged (addendum 1 §6). Two additions the wider scope makes necessary:

* **K8 — the accounting duplicate must not double-count.** If including
  `SCH - HQ_IMPORT_EXPORT` would change any zone's envelope, it is being
  double-counted somewhere ⇒ stop. It is excluded by construction; this gate
  checks the exclusion held.
* **K9 — every posted row must be attributed exactly once.** The union of the
  attribution map must cover every `SCH -` row in the clean partition, with no
  row in two zones ⇒ stop otherwise. A silently dropped row would delete real
  seam capability, and a duplicated one would invent it.

## §8 — the decision rule

Parent §8 stands **unchanged**, including its named adverse case (routing east
over-relieves Central-East and pushes C3a-2023 through +10 %, converting a PASS
to a FAIL, *reported as a FAIL and not rescued by scoping the share to a year, a
zone or a season*).

**No tuning under any branch.** No band widened, no share swept, no leg unarmed,
no row re-attributed, nothing scoped in response to a score.
