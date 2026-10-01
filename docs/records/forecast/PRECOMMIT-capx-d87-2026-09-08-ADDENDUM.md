# ADDENDUM to PRECOMMIT-capx-d87-2026-09-08 — the D88 stop, and gate G7 that substitutes for it

**Written BEFORE the edit and BEFORE any solve**, so the gate below cannot be shaped by a result.
Date 2026-09-08 · branch `claude/capx-d87-ccs-clean-tier-seam` · HEAD `origin/main` `cbf9be9f`.

## 1. The situation

The charter sequences capx **D88** first — *"D88 installs a duplicate-id GUARD, and your screen
should run with it armed so that if folding the dual grows the NYISO retrofit set into a later
re-mint, the SCREEN says so instead of a downstream scorer"* — and stops this lane's **edit** and
**screen** (not its session) until D88 is on `main`.

**Measured at the time of writing:** D88 has not started. `git ls-remote --heads origin` carries
`capx-d83-…`, `capx-d87-…` (this lane) and `capx-d89-…` and **no D88 branch**; there are **no open
pull requests**; and `origin/main:src/market_sim/data/fleet/arrays.py` carries no uniqueness guard
at `:3651`. The director's own ledger r#61 records the risk in its own words — *"TWO OF MY FOUR
CHARTERS WERE NEVER DISPATCHED"* → doctrine **"the queue's middle and tail are where lanes go
missing."**

## 2. The owner's ruling (2026-09-08, this session)

**PROCEED NOW, with G7 substituting for the guard.** The question was put with the alternative of
holding the edit; the owner chose to proceed. The reasoning recorded at the time: this container is
ephemeral, so LP spent later is LP spent twice, and the stop's *stated reason* is screen-safety —
which this lane can supply itself, from its own artifacts, without touching any file D88 owns.

## 3. Gate G7 — the duplicate-`unit_id` census, on the ARM's own ledgers

Added to §6.2's pre-registered gates. **STOP-ONLY**, like every other gate there: it may kill the
arm, never promote it, and it is never read against a residual.

> **G7.** Over every `evolution_<year>.json` the ARM writes (2026–2030), and over the CONTROL's
> same five, reconstruct the fleet's `unit_id` multiset the way D88's READ did over the 496
> committed ledgers, and assert:
>
> - **(a)** no `unit_id` appears twice in any year's fleet in either arm;
> - **(b)** no `unit_id` recorded in a `ccs_retrofits` row is recorded again in a LATER year's
>   `ccs_retrofits` — the impossibility signature D88's census found on all nine NEISO T3 variants
>   (one id retrofitted in 2031, 2040, 2042 **and** 2044), since a retrofit is irreversible and a
>   converted unit is never a candidate again (`ccs.py:400`);
> - **(c)** no id retrofitted in year *Y* is re-minted by an economic `gas_cc` entry in a year
>   ≥ *Y* — i.e. no legacy-form `gas_cc_<bin>_<zone>` id is both a retrofit row and, later, an
>   entry-attributable id.
>
> **A failure in the ARM that is absent from the CONTROL kills the arm** — that is exactly the
> outcome the charter wanted the guard to catch, and it is caught here at the screen. A failure
> present in BOTH arms is **not** this lane's object: it is D88's, and it is reported to D88 with
> the ledgers rather than repaired here (this lane owns neither `arrays.py:3651` nor `ccs.py`'s
> conversion block).

**Why this is a faithful substitute, and where it is weaker.** It answers the same question on the
same evidence class D88's own READ used, at zero LP, and it is scoped precisely to the risk the
charter named (a NYISO retrofit set grown by this arm colliding with a later re-mint). It is
**weaker** in exactly one way, stated rather than smoothed: D88's guard is an assertion at
`generators_to_fleet_arrays`, so it fires on **every** future run and on collisions from sources
the ledgers do not record; G7 is a post-hoc census over two bundles' ledgers in one ISO over five
years. It is the screen's protection, not the program's — **D88 remains owed**, and this addendum
is not an argument against chartering it.

**Prior probability, from the record, that G7 fires here: low.** D88's own census over the 496
committed ledgers found the trigger in exactly two families — NEISO T3 (2031→2050) and ERCOT
`d65br` (2030) — and found **no collision in any NYISO bundle**: NYISO T1-F's 2028
`gas_cc_h_class_NYC` and 2030 `…Upstate_West` retrofits are followed by no economic `gas_cc` build
in the same zone. The arm can only change that by retrofitting MORE and thereby freeing more
`gas_cc` headroom for a later build, which is precisely why the census is run on the arm and not
assumed from the control.

## 4. Nothing else in the PRECOMMIT changes

Gates G1–G6, the screen year (2030), the recipe, the A/B-at-HEAD posture earned by §5.3's one LIVE
hunk, the blast radius, the epoch scope and the rule-31 retention posture are all unchanged.
