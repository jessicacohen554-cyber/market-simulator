# W2 — Wire CAISO RA Must-Offer P2 Trigger into runner.py

**Gap ID:** A10 (MEDIUM)  
**Model tier:** Sonnet  
**Estimated diff:** ~15 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`, around lines 4327–4340) has a `caiso_ra` gate that triggers a P2 (commitment) solve even when `commitment_enabled` is False:

```python
caiso_ra = getattr(config, "caiso_ra_mustoffer", False) and iso == "CAISO"
if config.commitment_enabled or as_aware or caiso_ra:
    # P2 solve with commitment screen
```

The forecast path (`runner.py`, line 834) only checks:
```python
if config.commitment_enabled or as_aware:
```

It has no `caiso_ra` gate. When a CAISO forecast runs with `caiso_ra_mustoffer: true` but `commitment_enabled: false`, the P2 midday must-offer bridge is silently skipped — the commitment screen never fires, so RA-obligated units aren't force-committed during midday solar hours.

## What to Do

1. **In runner.py**, before the P2 gate (line 834), add the CAISO RA flag:
   ```python
   caiso_ra = (
       getattr(config, "caiso_ra_mustoffer", False)
       and iso == "CAISO"
   )
   if config.commitment_enabled or as_aware or caiso_ra:
   ```

2. This is a one-line addition to the existing condition. No new imports needed.

## What NOT to Do

- Do NOT change the commitment logic inside the P2 block.
- Do NOT change the calibration script.
- Do NOT modify `dispatch.py` or `commitment.py`.

## Acceptance Criteria

1. A CAISO forecast with `caiso_ra_mustoffer: true` and `commitment_enabled: false` enters the P2 block and runs the commitment screen.
2. The P1 result is saved as `_p1` pass before the P2 solve.
3. A non-CAISO ISO with the same config does NOT trigger the P2 block (unless `commitment_enabled` is True).
4. Existing tests pass unchanged.
