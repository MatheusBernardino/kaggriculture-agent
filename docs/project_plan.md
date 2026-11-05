# Kaggriculture Agent - Project Plan

## 1. Objective

Develop an autonomous agent for the Kaggriculture simulation competition.

The agent's primary objective is to maximize the amount of money in the bank at the end of a 720-turn season.

The agent must make decisions autonomously based on the observation (`obs`) received from the environment.

---

## 2. Environment

Each episode consists of:

- 2 competing players
- 30 in-game days (0–29)
- 24 turns per day (0–23)
- 720 total turns (0–719)
- $3000 starting money
- An initially unlocked 5×5 farm quadrant (NW)
- Up to four 5×5 quadrants through `BUY_LAND` ($1000, $2000, $4000)
- Shed at center tiles (4,4), (4,5), (5,4), (5,5) — capacity 100 items
- Shared market with dynamic pricing driven by inventory levels
- Town shops that drain market inventory automatically every 4 turns

The agent can control:

- The main `farmer` (permanent, 1 action per turn)
- Temporary `hands` hired during the day (1 action per turn each)
- `market` actions (up to 10 per turn, independent from farmer/hand actions)

---

## 3. Observation

The agent receives an observation containing:

- `player` — player index (0 or 1)
- `step` — global turn counter (0–719)
- `day` — current day (0–29)
- `hour` — current hour within day (0–23)
- `farms` — list of both players' farm states (tiles, farmer/hand positions, money)
- `market` — shared market state (`inventory` and `prices` per product)
- `town` — list of `unlocked_shops`
- `private` — player-only data (`shed`, `seeds`, `inventories` per unit)

---

## 4. Scoring

- Leaderboard uses continuous Bradley-Terry ranking from live matches.
- Final evaluation is a tournament after the deadline.
- **Only `farm["money"]` at turn 720 counts.** Items in shed, inventory, or on tiles have zero value.
- 5 submissions per day. Only the 2 most recent remain active for final evaluation.

---

## 5. Competition Timeline

- **Entry Deadline**: September 23, 2026
- **Team Merger Deadline**: September 23, 2026
- **Final Submission Deadline**: September 30, 2026

**Remaining time: ~4 weeks (as of Sep 2, 2026)**

---

## 6. Development Stages

Stages reordered by competitive impact and feasibility within the remaining timeline.

### Phase 1 — Foundation (DONE)

#### V1 - Environment Observer ✅

Understand `obs` structure and how state evolves over time.

#### V2 - Single-Crop Baseline ✅

Implement a complete production loop: BUY_SEED → PLANT → WATER → HARVEST → DROP → SELL.
Tested with WHEAT and later CARROT.

#### V3 - Multi-Tile Production + Farm Hands ✅

Manage multiple plants simultaneously with priority-based targeting.
Hire hands and coordinate them to avoid tile conflicts.

---

### Phase 2 — Core Competitive Features (NEXT)

#### V4 - Market Strategy 🔴 HIGH PRIORITY

**Why first**: Without price awareness, all production improvements are neutralized when prices crash to $1.

The agent must:

- Read `obs["market"]["prices"][product]` before selling
- Set a minimum sell threshold per product (e.g., 70% of base price)
- Limit sell volume per turn (max 3–5 units) to avoid walking down the price curve
- Force full liquidation on days 28–29 regardless of price
- Track `obs["market"]["inventory"]` to estimate price direction

Key insight: Selling is **unit-by-unit** — each unit sold raises market inventory by 1 and lowers the price for the next unit.

Price fragility by product:

| Product | Base | Curve | Excess +T Price | Risk |
|---------|------|-------|-----------------|------|
| WHEAT | $25 | log | $20 | 🟢 Safe |
| EGG | $50 | log | $40 | 🟢 Safe |
| CARROT | $35 | sqrt | $10 | 🟡 Medium |
| TOMATO | $60 | sqrt | $24 | 🟡 Medium |
| FERTILIZER | $100 | linear | $60 | 🟡 Medium |
| STRAWBERRY | $120 | linear | $1 | 🔴 Fragile |
| MILK | $160 | linear | $1 | 🔴 Fragile |
| MELON | $250 | sq | $1 | 🔴 Extremely Fragile |
| WOOL | $200 | sq | $1 | 🔴 Extremely Fragile |

#### V5 - Dynamic Multi-Crop Selection 🔴 HIGH PRIORITY

**Why**: MELON yields $142/day/tile but needs 11 days. CARROT yields $21/day/tile but only needs 4 days. Combining them maximizes coverage of the full 30-day season.

The agent must select the best crop to plant based on:

- Days remaining in the season
- Current market price of each crop
- Crop cycle length vs. remaining time

Target strategy:

| Days Remaining | Crop | Rationale |
|---------------|------|-----------|
| ≥ 12 | MELON | Highest $/day if price holds |
| ≥ 12 (price crashed) | CARROT | Fast fallback |
| 4–11 | CARROT | 4-day cycle fits |
| 3 | WHEAT | Minimum viable cycle |
| < 3 | None | No time to harvest |

The agent must handle **multiple crop types on the field simultaneously** — targeting, watering, and harvesting based on each tile's actual crop, not a global constant.

#### V6 - Weed Management

Weeds spawn randomly (`weedSpawnChance = 0.005` per empty tile per turn) and block productive tiles.

- Add `DIG` as a task in the targeting system
- Priority: higher than `PLANT`, lower than `WATER` and `HARVEST`
- Track weed count to assess farm health

#### V7 - End-Game Liquidation

Items left in farmer inventory, hand inventory, or as unharvested crops at turn 720 are **worth $0**.

The agent must:

- Day 28: Stop planting. Harvest everything possible. All hands focus on harvest + DROP
- Day 29: Emergency harvest sweep. Farmer and hands return to shed to DROP
- Final hours: Sell everything in shed at any price

---

### Phase 3 — Optimization (if time permits)

#### V8 - Fertilizer

Evaluate whether FERTILIZE increases expected profit enough to justify:

- Fertilizer cost ($100 at market, or free from animals)
- Action cost (1 turn to apply)
- Additional yield (+50% for one-time crops if applied during bonus window)

Best candidates for fertilizer:

| Crop | Unfertilized | Fertilized | Extra Revenue | Worth it? |
|------|-------------|-----------|---------------|-----------|
| WHEAT | 4 × $25 = $100 | 6 × $25 = $150 | +$50 | Only if fertilizer is free |
| CARROT | 3 × $35 = $105 | 4 × $35 = $140 | +$35 | No at $100 cost |
| MELON | 6 × $250 = $1500 | 6 × $250 = $1500 | +$0 | ❌ Same yield |

**Conclusion**: Fertilizer only makes sense for WHEAT if collected free from animals.

#### V9 - Land Expansion

Evaluate `BUY_LAND` ROI:

- NE quadrant: $1000 → needs ~$1000 of extra production to break even
- SW quadrant: $2000 → needs ~$2000
- SE quadrant: $4000 → almost never worth it

Rule of thumb: Only buy if `days_remaining × expected_daily_profit_per_tile × 25 > land_cost × 2`

Must also consider: more tiles = more walking distance = more idle turns for farmer.

#### V10 - Animals

Animals provide:

- Recurring product income (EGG, MILK, WOOL)
- Free fertilizer (COLLECT_FERTILIZER)
- But require: structure build, purchase, daily FEED (1 WHEAT), CARE, HARVEST

ROI analysis:

| Animal | Cost | Revenue/Day | Break-even Day |
|--------|------|-------------|---------------|
| GOOSE | $300 + structure | $50/day (EGG) | Day 10 |
| COW | $400 + structure | $80/2 days (MILK) | Day 18 |
| SHEEP | $500 + structure | $67/3 days (WOOL) | Day 21+ |

**Conclusion**: Only GOOSE is viable within 30-day season. Must be placed early (day 0–5) and requires dedicated tile + daily WHEAT feed.

#### V11 - Advanced Hands Management

Optimize hand hiring based on ROI:

- Hire cost follows Fibonacci: 1st=$1, 2nd=$1, 3rd=$2, 4th=$3, 5th=$5...
- Each hand provides 24 actions per day
- Calculate: `expected_value_of_24_actions > hire_cost`
- Hire more hands on harvest days, fewer on quiet days
- Stop hiring after day 27

#### V12 - Advanced Decision Making

If time permits, evaluate:

- Monte Carlo simulation of remaining days to estimate best crop mix
- Opponent observation: read `obs["farms"][1-player]` to predict their selling
- Town shop tracking: time sells to coincide with shop demand ticks

---

## 7. Evaluation

Each experiment must record in `experiments.md`:

- Agent version and strategy description
- Opponent type (random, self-play, previous version)
- Final money (both players)
- Win/loss/draw
- Key observations (crop utilization, idle turns, market prices, weeds)
- Hypothesis tested and conclusion

Minimum metrics per run:

- Final money
- Total units produced
- Total units sold
- Average sell price per product
- Number of weeds encountered
- Tiles utilized / total tiles
- Hands hired and utilization rate

---

## 8. Development Principles

1. **Measure first**: No strategy change without a baseline measurement.
2. **One variable at a time**: Each experiment should isolate a single change.
3. **Use the carrot agent as baseline**: `submission_carrot_optimized.py` is the current best — compare against it.
4. **Test locally before submitting**: Use `kaggle_environments` with `env.run([agent, "random"])`.
5. **Keep submissions lean**: Remove all debug lists and print statements before submitting.
6. **Single file for submission**: Kaggle expects a single `main.py` or a notebook. All code must be self-contained.

---

## 9. Submission Checklist

Before each Kaggle submission:

- [ ] Remove all debug lists (`money_debug`, `action_debug`, etc.)
- [ ] Remove all `print()` statements
- [ ] Verify agent works with `env.run([agent, "random"])` for full 720 turns
- [ ] Test against previous agent version (`env.run([new_agent, old_agent])`)
- [ ] Record result in `experiments.md`
- [ ] Rename entry point to `agent` or ensure `main.py` exports it