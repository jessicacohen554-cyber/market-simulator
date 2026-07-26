# FINDING — caiso-122 STEP 1: the C3a-2025 HEAD drift is **NOT the arrival of the CAISO CAMPD outage extract** (measured and REFUTED), and the keeper's recorded provenance **cannot anchor a bisect at all** — `meta.git_sha` is unreachable and `meta.timestamp` preserves only the original *date* across a replay. The outage overlay's own sensitivity is large and now quantified (**λ +2.08 /MWh, +5.7 % on 2025**), but it is not the drift. **The drift source remains OPEN** (2026-07-26)

**Status: STEP 1 PARTIALLY resolved. The CAISO lane is NOT yet unblocked.** Keeper
`2026-07-23-caiso-netrev-margin-keeper` UNCHANGED. Nothing armed, nothing
promoted, no revert proposed.

> **Correction notice.** The first revision of this finding (commit `e688275d9`)
> concluded that the drift *was* the outage extract arriving, and that the keeper
> had solved with zero unit outages. **That conclusion is refuted by §3 below**,
> measured after it was written. The forensic §1/§4 content survives; the §5
> verdict of the first revision does not. It is corrected here rather than
> silently amended.

---

## §1 — the keeper's recorded provenance is not a usable basis anchor

caiso-121 recommended bisecting `abb0fcd..HEAD`. That range cannot be
constructed, and the timestamp fallback is also unsound:

1. **`abb0fcd` is unreachable.** It resolves to no object after
   `git fetch --unshallow` (8,839 commits, all `origin` refs) — a session-local
   commit on a branch that did not survive to `main`.
2. **`meta.timestamp` is a hybrid after any replay.** `scripts/replay_keeper.py`
   line 324 writes
   `new_meta["timestamp"] = orig_ts[:10] + new_ts[10:]` — it restores the
   original **date** and keeps the **replay's time-of-day**, so the dashboard run
   id is stable. A keeper replayed on 2026-07-25 at 22:29:35 UTC is therefore
   stamped `2026-07-23T22:29:35`. The recorded date says nothing about the code
   or data the committed bytes were produced from.

   The CAISO lane replays keepers routinely (caiso-102, caiso-119, caiso-121 all
   used `replay_keeper` A/B arms), so this is the expected case, not an exotic
   one.

**Consequence — a governance defect worth fixing independently of this lane:** a
committed keeper bundle carries no field that reliably identifies the basis of
its own bytes. `git_sha` may point at a destroyed branch commit; `timestamp` may
be a hybrid. Any future "why did this keeper move?" question hits the same wall.

## §2 — what was measured (three arms, one year, same box)

CAISO 2025, CA demand-weighted λ ($/MWh), all arms solved this session at the
session-pinned HEAD (`de62eb1`; the branch was deliberately **not** rebased
mid-session so every arm shares one basis):

| arm | CA λ | vs keeper |
|---|---|---|
| committed keeper (`caiso_netrev_margin`, its own bytes) | 38.0221 | — |
| **HEAD control** — keeper recipe, no delta | **38.5585** | **+0.5363 (+1.411 %)** |
| **HEAD counterfactual** — same, `campd-unit-outages-CAISO.csv` hidden | **36.4778** | −1.5443 (−4.062 %) |

The HEAD control reproduces caiso-121's arm A independently: CC_REGULAR
36.7448 → 36.2892 TWh (**−1.24 %**) and import 42.3418 → 42.7364 TWh
(**+0.93 %**) match its §0 table to the reported precision. The drift is real
and stable.

**The outage overlay's own sensitivity, now quantified:** hiding the extract
moves CAISO 2025 λ by **−2.0807 /MWh (−5.4 %)** and CC_CHP by **+2.12 TWh**.
That is a large lever and is worth recording on its own account.

## §3 — REFUTED: the keeper did NOT solve without the outage overlay

The first revision inferred a silent degradation from the fact that
`data/raw/campd-unit-outages-CAISO.csv` is *created* by `59f8bc30d`
(2026-07-24 04:45 UTC) and that `unit_outage_derate_factors` returns `{}` for a
missing file. Both of those statements are still true. The inference from them
is not, because **`meta.timestamp` does not date the bytes** (§1).

Measured directly on the keeper's own committed `class_hourly_2025.parquet`,
against both HEAD arms — `CC_CHP` is the class the overlay dominates:

| comparison | Pearson r | mean abs Δ | max abs Δ |
|---|---|---|---|
| keeper vs **HEAD control** (overlay ON) | **0.99343** | **18.6 MW** | 160.2 MW |
| keeper vs **HEAD counterfactual** (overlay OFF) | 0.57525 | 242.5 MW | 707.0 MW |

Derated-hour sets (hours where CC_CHP sits >50 MW below its overlay-off level):
keeper **6,946** h, HEAD control **6,984** h, **6,742 h in common**.

**The keeper carries the outage overlay, on essentially the same windows as
HEAD.** Presence-vs-absence of the extract is therefore *not* the drift, and the
keeper's `outage_source="historic"` was honoured when its bytes were produced.
The silent-degradation code path (`if df is None: return {}`) is real and still
worth hardening — it is the same class `439cb0329` fixed for PJM — but it did
**not** fire for this keeper.

## §4 — exonerated, with the reason (unchanged from revision 1, plus two)

| candidate | why it cannot move CAISO |
|---|---|
| `31035427f` DAM-first outage overlay (names CAISO) | gated `getattr(config, "caiso_dam_outages", False)`; field lands later as `caiso_dam_outages: bool = False`, absent from the keeper's meta |
| `42747a969` **CAISO resource→EIA crosswalk** (34→58 rows, ~20.9 GW) | consumed **only** by `data/caiso_outages.py`, i.e. the same default-off `caiso_dam_outages` path — inert for this recipe |
| `3babe5f8a` eGRID co-located heat-rate reconciliation | accepted set is exactly `{55641: 6.880}` (MISO); reproduced here — only that plant logs a repair |
| `af7492706` EIA-930 degenerate solar repair | degeneracy-keyed; NYISO solar is the only cell reaching the fallback, other 30 ISO-year-mode CF arrays byte-identical |
| `e411d1fd9` wave-4C retirement revenue | `capacity_evolution/retirements.py`, not on the backcast path |
| `518084e70`, `da3e97900`, `87b95868d`, `e6133a635` | ERCOT-gated |
| `826eac749`, `d4dfe0199` | MISO-gated / instrumentation |
| `439cb0329`, `e19ed0368`, `738aef35a` | PJM-gated |
| `d13a3f2c6` EIA-930 zero-coded filing gaps | scorer/benchmark only, not the solve |

## §5 — what is still open, and the cheapest way to close it

The drift is **+1.411 % λ on 2025**, with the class signature CC_REGULAR
**−0.456 TWh**, import **+0.395 TWh**, CT_PEAKER +0.072, ST_GAS +0.036, CC_CHP
−0.013. Less gas, more imports, higher λ. No candidate above survives as its
cause, and the outage extract is refuted.

The one candidate that remains live and was **not** eliminated is `6a8f285c5`
(neiso-65 guard-corrected CAMPD extracts, 2026-07-26 00:36 UTC), which moved
**810 rows out of the CAISO outage file** into a `layup` companion (economic
layup ≠ forced outage). It is a genuine change to CAISO outage *windows* that
would leave CC_CHP largely intact while shifting CC_REGULAR and imports. Its
naive direction is wrong (fewer outages ⇒ more gas, not less), so it is a
hypothesis, not a conclusion — the interaction with the layup split's
*replacement* rows has not been measured.

**Recommended next step (one 15-minute solve, no LP guesswork):** replay 2025
at HEAD with `data/raw/campd-unit-outages-CAISO.csv` restored to its
`6a8f285c5^` content (`git show 6a8f285c5^:… > …`). If CA λ returns to ≈38.02,
the guard-corrected extract is the drift and the rule-1/rule-14 question is
whether the layup split is the more accurate representation (it is presented as
such by neiso-65, and was adopted ISO-wide). If λ does not move, the drift is
elsewhere and the next cut should be the `data/` tree rather than
`src/market_sim/`, which §4 has now largely exhausted.

**Standing instruction for the lane, unchanged and reinforced:** every CAISO
C3a-2025 comparison is basis-sensitive; always carry a same-HEAD control arm and
never A/B against the committed keeper's bytes.
