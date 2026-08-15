# Kaggriculture Agent - Strategy

## V1 - Environment Observer

### Objective

Understand the structure and evolution of the observation (`obs`) during an episode.

The observer should monitor:

- `day`
- `hour`
- `farms`
- `market`
- `town`
- `private`

The observer should not attempt to optimize the game.

---

# V2 - Wheat Baseline


## Production Cycle

The initial production strategy will focus exclusively on `WHEAT`.

The production cycle is:

```text
BUY_SEED
    ↓
MOVE
    ↓
PLANT
    ↓
WATER
    ↓
WAIT
    ↓
HARVEST
    ↓
DROP / SHED
    ↓
SELL
    ↓
REPEAT
```
Seed Purchase

IF the agent has no available WHEAT seeds
AND the agent has enough money to purchase a seed:
BUY_SEED WHEAT 1

Planting

IF the current tile is empty
AND a WHEAT seed is available:
PLANT WHEAT

Watering

IF the current tile contains a WHEAT plant
AND watered_today is False:

WATER

Harvesting

IF the current tile contains a WHEAT plant
AND the plant has reached the appropriate harvest age:

HARVEST
Selling

IF the shed contains harvested WHEAT:

SELL WHEAT <amount>
Movement

The agent must move between the shed and production tiles when necessary.

Movement logic will initially be deterministic.


# V3 - Multi-Tile Production

The agent should maintain several Wheat plants simultaneously.

The agent should track:

- Available empty tiles
- Existing Wheat plants
- Plant age
- watered_today
- Expected harvest time

The goal is to avoid leaving productive tiles unused.

# V4 - Crop Selection

For each crop, estimate:

- Expected Revenue
- Expected Cost
- Expected Profit
- Profit per Tile
- Profit per Day

The agent should compare:

- WHEAT
- CARROT
- TOMATO
- STRAWBERRY
- MELON

before deciding which crop to produce.

# V5 - Market Strategy

The agent should consider:

- Current market price
- Base price
- Market inventory
- Expected future production
- Town demand

The agent should avoid automatically selling every product if waiting for a better price is economically advantageous.

# V6 - Fertilizer Strategy

The agent should evaluate whether using FERTILIZE increases expected profit.

Fertilizer decisions should consider:

- Fertilizer cost
- Additional expected yield
- Crop value
- Remaining growth window
- Opportunity cost of the action

# V7 - Animal Strategy

The agent should evaluate animals based on:

- Purchase cost
- Required structure
- Feed requirements
- Production interval
- Product price
- Care bonus
- Fertilizer production
- Expected return over the remaining season

# V8 - Farm Hand Strategy

The agent should calculate whether hiring a hand is economically justified.

A hand should be hired only when:

Expected additional value generated > Hiring cost

The agent should prioritize actions with the highest economic value.

# V9 - Land Expansion Strategy

The agent should evaluate BUY_LAND based on:

Expected additional production value > Land purchase cost

The agent should avoid purchasing land when the remaining season is too short to recover the investment.

# V10 - Integrated Strategy

The agent will combine:

- Production
- Crop selection
- Market decisions
- Fertilizer
- Animals
- Farm hands
- Land expansion

The agent should prioritize decisions according to expected economic return.