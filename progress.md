# Campus Crowd — Progress Log

---

## 2026-04-26 — Adoption-Rate Adjusted Crowd Density

### Problem with the old check-in crowding system

The original `/status` endpoint calculated crowd density as:

```
crowding = active_checkins_at_spot / spot_capacity
```

This is misleading when only a small fraction of the real campus population
uses the app. If a spot holds 50 people but only 2 users checked in, the
system reported 2/50 = 4% density — which could mean the spot is nearly empty
OR it could mean 20 out of 50 people are there but 90% of them don't use the app.

### Solution: Adoption-Rate Scaling

The fix introduces a two-step calculation:

#### Step 1 — Compute the campus adoption rate

At every `/status` request, count the total number of **active check-ins across
all spots** (each spot has its own `stay_minutes` window).

```
total_active = sum of active check-ins in every spot right now
adoption_rate = total_active / TOTAL_CAMPUS_CAPACITY
```

`TOTAL_CAMPUS_CAPACITY` is set to **1000** (the number of people the whole
campus can hold at once). If 100 people are actively checked in campus-wide,
the adoption rate is 100/1000 = **10%** — meaning we estimate 10% of the
campus population is using the app.

#### Step 2 — Scale each spot's effective capacity

```
effective_capacity = spot_nominal_capacity × adoption_rate
crowding           = spot_active_checkins / effective_capacity   (capped at 1.0)
```

**Worked example** (mirrors the user's description):
- Campus capacity: 1000
- Total active check-ins: 100  →  adoption_rate = 0.10 (10 %)
- Spot Med C: nominal capacity 50  →  effective_capacity = 50 × 0.10 = **5**
- Med C has 2 active check-ins  →  crowding = 2 / 5 = **0.40** → label: "moderate"

Without the adjustment the same situation would show 2/50 = 0.04 → "quiet",
which is likely wrong.

### New constants added to `app.py`

| Name | Value | Purpose |
|---|---|---|
| `USE_ADOPTION_RATE_ADJUSTMENT` | `True` | Feature flag — set to `False` to revert |
| `TOTAL_CAMPUS_CAPACITY` | `1000` | Total people the campus can hold at once |

### New response fields from `/status`

The endpoint now also returns two extra diagnostic fields per spot:

| Field | Example | Meaning |
|---|---|---|
| `adoption_rate` | `0.1` | Fraction of campus using the app right now |
| `effective_capacity` | `5.0` | Scaled-down capacity used for density calc |

These are safe to ignore on the frontend but useful for debugging.

---

## How to CANCEL / DISABLE this system

### Option A — One-line flag (recommended)

Open `app.py` and change line:

```python
USE_ADOPTION_RATE_ADJUSTMENT = True
```
to:
```python
USE_ADOPTION_RATE_ADJUSTMENT = False
```

The code will immediately fall back to the original `count / capacity` formula.
No other changes needed. Restart Flask after editing.

### Option B — Set campus capacity to 0

```python
TOTAL_CAMPUS_CAPACITY = 0
```

The guard `if USE_ADOPTION_RATE_ADJUSTMENT and TOTAL_CAMPUS_CAPACITY > 0`
will be False, so the plain formula is used. Same effect as Option A.

### Option C — Full revert (delete the new code blocks)

Remove the two blocks marked with the comment banners
`# ---- Adoption-rate adjustment ... ----` in `app.py` and replace the
`/status` crowding line with the original one-liner:

```python
crowding = min(count / config["capacity"], 1.0)
```

Also remove `adoption_rate` and `effective_capacity` from the `result` dict.

---

## Files changed

| File | Change |
|---|---|
| `app.py` | Added `USE_ADOPTION_RATE_ADJUSTMENT`, `TOTAL_CAMPUS_CAPACITY`; rewrote crowding logic in `/status` |
| `index.html` | No changes needed — new fields are backward-compatible extras |
| `progress.md` | This file — created |

---

## What was NOT changed

- The 1–10 manual rating system (`/rate` endpoint) is untouched.
- Check-in cooldown logic is untouched.
- All SPOTS config is untouched.
- The frontend HTML/JS is untouched.

