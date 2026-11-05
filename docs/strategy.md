# Kaggriculture Agent - Strategy

## Current Agent: `submission_carrot_optimized.py`

Carrot throughput agent. Plants CARROT only, hires 1 hand/day, sells everything immediately.

**Strengths**: Clean code, hand coordination, smart harvest timing.
**Weaknesses**: No price awareness, single crop, no weed management, no end-game.

---

## V4 - Market Strategy

### Problem

The agent sells all products every turn without checking market prices.
CARROT has a `sqrt` above-curve with `above_target=0.70` — price drops from $35 to $1 when the market is oversaturated.

### Strategy

```
SELL decision per product per turn:

1. Read current_price = obs["market"]["prices"][product]
2. Read base_price from CROP_DATA or ANIMAL_DATA

3. IF day >= 28:
     → Sell everything (liquidation mode)

4. IF current_price >= base_price * 0.80:
     → Sell min(quantity_in_shed, 5)

5. IF current_price >= base_price * 0.50:
     → Sell min(quantity_in_shed, 2)

6. IF current_price < base_price * 0.50:
     → Hold (wait for town shops to drain inventory)
     → UNLESS shed is near capacity (>80 items): sell 2 to make room

7. Never sell more than 5 units of a single product per turn
   (prevents walking down the price curve too aggressively)
```

### Implementation Notes

- Market actions are independent from farmer movement — selling does not cost a turn
- `obs["market"]["prices"]` provides the current price per product
- `obs["market"]["inventory"]` shows total market stock — useful to predict price direction
- Town shops drain inventory every 4 turns — prices recover over time if you wait

---

## V5 - Dynamic Multi-Crop Selection

### Problem

The agent plants only CARROT. MELON yields $142/day/tile (7× more than CARROT at $21/day) but takes 11 days.
Planting MELON after day 18 wastes the tile since it can't mature before day 29.

### Strategy

```
choose_crop(obs):

  days_remaining = 29 - obs["day"]
  melon_price = obs["market"]["prices"].get("MELON", 250)

  IF days_remaining >= 12 AND melon_price >= 150:
    → MELON

  IF days_remaining >= 4:
    → CARROT

  IF days_remaining >= 3:
    → WHEAT

  ELSE:
    → None (don't plant)
```

### Critical Considerations

- When multiple crop types coexist on the field:
  - `HARVEST` reads `tile["crop"]` — works regardless of crop type
  - `WATER` is crop-agnostic — works on any plant
  - `PLANT` must specify the selected crop name
  - `_ready_to_harvest()` must handle different `max_yield_day` values per crop

- Seed purchasing must match the selected crop:
  - Buy MELON seeds early in the season
  - Switch to buying CARROT seeds around day 18
  - Stop buying all seeds around day 27

---

## V6 - Weed Management

### Problem

Weeds spawn randomly on empty tiles (0.5% chance per tile per turn).
They block planting and reduce productive area.

### Strategy

```
Add to _farm_tasks:

  IF tile["kind"] == "WEED":
    → Add (x, y, "dig") to candidates
    → Priority: between HARVEST and PLANT

Add to _action_for_target:

  IF purpose == "dig":
    → return ["DIG"]
```

---

## V7 - End-Game Liquidation

### Problem

At turn 720, everything stops. Items in inventories or on tiles are worth $0.
Only `farm["money"]` counts.

### Strategy

```
Day 27 (hour 0):
  - Stop buying seeds
  - Stop hiring hands (unless needed for final harvest)
  - Focus on harvesting remaining crops

Day 28:
  - All workers: harvest anything with yield > 0
  - After harvesting: move to shed and DROP
  - Sell everything in shed at any price

Day 29:
  - Emergency sweep: harvest any remaining plants
  - All workers return to shed
  - DROP all inventory
  - SELL everything remaining in shed

  IF farmer has items in inventory AND not at shed:
    → Move to nearest shed tile
    → DROP when arrived
```

### Key detail

Products are auto-dropped to shed at end of each day (hour 23 → hour 0 transition).
But relying on this for day 29 is risky — manual DROP is safer.

---

## V8 - Fertilizer Strategy

### Analysis

| Crop | Extra Yield | Extra Revenue | Fertilizer Cost | Net Gain |
|------|------------|---------------|-----------------|----------|
| WHEAT | +2 units | +$50 | $100 (buy) | -$50 ❌ |
| WHEAT | +2 units | +$50 | $0 (animal) | +$50 ✅ |
| CARROT | +1 unit | +$35 | $100 (buy) | -$65 ❌ |
| MELON | +0 units | $0 | Any | ❌ No benefit |

### Conclusion

Only worth using fertilizer if it's free (collected from animals).
Best target: WHEAT during bonus window (days 2–4 after planting).

---

## V9 - Land Expansion Strategy

### ROI Framework

```
expected_roi = (days_remaining * daily_profit_per_tile * 25) - land_cost

BUY_LAND IF expected_roi > 0 AND days_remaining > 15

Costs:
  - NE (2nd quadrant): $1,000
  - SW (3rd quadrant): $2,000
  - SE (4th quadrant): $4,000
```

### Practical thresholds

- NE: Buy if day ≤ 10 and producing CARROT ($21/day/tile → $21 × 25 × 19 = $9,975 - $1,000 = +$8,975)
- SW: Buy if day ≤ 8 and cash > $5,000
- SE: Almost never worth it ($4,000 cost + increased walking distance)

### Warning

More land = more walking distance. Each extra quadrant adds ~5 turns of movement per trip.
Must hire additional hands to compensate.

---

## V10 - Animals Strategy

### ROI Analysis

```
GOOSE:
  Cost: $300 animal + structure action
  Produces: 1 EGG/day starting day 4
  EGG base price: $50 (stable — log curve)
  Revenue over 26 remaining days: 26 × $50 = $1,300
  Feed cost: 26 × $10 (WHEAT seed) = $260
  Net: $1,300 - $300 - $260 = +$740 ✅ IF placed day 0–4

COW:
  Cost: $400 + structure
  Produces: 1 MILK every 2 days starting day 8
  Revenue over 22 remaining days: 11 × $160 = $1,760
  Feed cost: 22 × $10 = $220
  Net: $1,760 - $400 - $220 = +$1,140 ✅ BUT price crashes easily

SHEEP:
  Cost: $500 + structure
  Produces: 1 WOOL every 3 days starting day 6
  Revenue over 24 remaining days: 8 × $200 = $1,600
  Feed cost: 24 × $10 = $240
  Net: $1,600 - $500 - $240 = +$860 ✅ BUT price crashes easily
```

### Key Risks

- MILK and WOOL have fragile price curves — a single glut crashes to $1
- Animals require daily FEED (1 WHEAT) — must buy WHEAT or grow it
- Missing 2 consecutive feeds → animal escapes permanently
- Animals occupy 1 tile permanently — opportunity cost vs. crops

### Recommendation

GOOSE is the safest animal investment if placed early (day 0–4).
EGG has a stable `log` price curve (min $39 even at 2× excess).

---

## V11 - Advanced Hands Management

### Hire Cost (Fibonacci)

| Hire # today | Cost |
|-------------|------|
| 1st | $1 |
| 2nd | $1 |
| 3rd | $2 |
| 4th | $3 |
| 5th | $5 |
| 6th | $8 |

### Strategy

```
hire_count(obs):

  IF day >= 28:
    → 0 (no point)

  IF day < 3:
    → 1 (planting phase)

  IF active_crops > 15:
    → 2 (high maintenance)

  ELSE:
    → 1
```

---

## V12 - Opponent Awareness

### Available Information

`obs["farms"][1 - player]` reveals the opponent's entire farm state:

- What they're growing
- Their money
- Their farmer/hand positions

### Potential Uses

- If opponent is flooding MELON → avoid MELON or hold sales
- If opponent has low money → they can't expand, you can be more aggressive
- Predict opponent's sell timing based on their shed contents

---

## Experiment Protocol

Every strategy change must follow:

1. **Baseline**: Run current best agent vs `random` for 3 games. Record average final money.
2. **Change**: Implement ONE change.
3. **Test**: Run new agent vs `random` for 3 games.
4. **Compare**: Run new agent vs old agent head-to-head for 3 games.
5. **Record**: Log all results in `experiments.md`.
6. **Decide**: Keep change if new agent wins ≥ 2/3 games against old agent.