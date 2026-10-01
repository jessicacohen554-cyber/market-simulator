# CORRECTION 1 — capx D78-R2: D78-R's registered arm DOES carry its evolution ledgers

**What was wrong.** PRECOMMIT §2 and ADDENDUM A §A.1 each gave three reasons why
D78-R's bundles cannot serve as this lane's control. The **third** reason was
stated as: *"its arm is registered SLIM (`meta.json`, `run_config.json`,
`forecast_verdict.json` only) — it carries no `evolution_<year>.json`, so the
whole-ledger diff §4 requires could not be taken against it at any code state."*

**That is false.** The registered slim set for a PJM T1-H run is larger than I
assumed. `git ls-files results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate`
returns `evolution_2021.json` … `evolution_2025.json`, `score.json`,
`screen_signal_diag_*.npz`, `meta.json` and `run_config.json` — the five evolution
ledgers **are** committed, and the whole-ledger diff could read them.

**What does not change, and why the decision stands.** The re-solve of both legs
was never resting on that reason. Either of the other two is sufficient on its own,
and both are unaffected:

1. **D78-R's legs are at a different solve-code state.** Its control-P was guarded
   at `cbf98979` and its arm at `99245361`, both before `main` took D67-ARM, D81,
   D74 and D75-R: `git diff --stat 99245361 <HEAD> -- src/market_sim scripts/` is
   19 files / +2,975 −54, including `retirements.py`, `capacity_market.py` and
   `adequacy.py` — LIVE on PJM's clearing path. Rule 29(b) earns a control solve on
   that alone.
2. **D78-R's control-P does not exist.** It was deleted before merge under rule
   29(c), so there is no control leg to difference an arm against, whatever the arm
   carries.

So the conclusion — **both legs re-solved at one HEAD, nothing of D78-R's reused as
a control** — is unchanged, and no gate, edge, declared class, STOP or
flip-condition limb moves. What changes is only that one of three supporting
reasons was wrong and is withdrawn.

**Recorded rather than patched.** The PRECOMMIT and ADDENDUM A are merged to
`main`; a pre-registration is not silently rewritten after the fact, so the
erroneous sentence stays where it is and this correction stands beside it. It is
carried into the FINDING's limitations.

*(Incidentally the mistake ran in the safe direction: it argued for MORE
independent measurement, not less. Had it run the other way — assuming a committed
artifact carried something it did not — the lane would have graded against a file
that was not there.)*
