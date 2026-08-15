# Kaggriculture Agent - Project Plan

## 1. Objective

Develop an autonomous agent for the Kaggriculture simulation competition.

The agent's primary objective is to maximize the amount of money in the bank at the end of a 720-turn season.

The agent must make decisions autonomously based on the observation (`obs`) received from the environment.

---

## 2. Environment

Each episode consists of:

- 2 competing players
- 30 in-game days
- 24 turns per day
- 720 total turns
- 3000 starting money
- An initially unlocked 5x5 farm quadrant
- Up to four 5x5 quadrants through `BUY_LAND`

The agent can control:

- The main `farmer`
- Temporary `hands` hired during the day
- `market` actions

---

## 3. Observation

The agent receives an observation containing:

- `player`
- `day`
- `hour`
- `farms`
- `market`
- `town`
- `private`

The agent must use this information to determine its actions.

---

## 4. Main Actions

### Farmer and Farm Hand Actions

- `NORTH`
- `SOUTH`
- `EAST`
- `WEST`
- `PLANT`
- `WATER`
- `HARVEST`
- `FERTILIZE`
- `FEED`
- `CARE`
- `COLLECT_FERTILIZER`
- `DIG`
- `BUILD_COOP`
- `BUILD_PASTURE`
- `PLACE`
- `PICKUP`
- `DROP`
- `PASS`

### Market Actions

- `BUY_SEED`
- `BUY_ANIMAL`
- `BUY_PRODUCT`
- `SELL`
- `HIRE`
- `BUY_LAND`

---

## 5. Development Stages

### V1 - Environment Observer

Create an agent that records and displays relevant information from `obs`.

The purpose of this version is to understand how the environment state changes over time.

### V2 - Wheat Baseline

Implement a simple Wheat production loop:

1. Buy `WHEAT` seeds.
2. Move to an available tile.
3. `PLANT WHEAT`.
4. `WATER` the plant.
5. Wait until the crop is ready.
6. `HARVEST`.
7. Move the harvested `WHEAT` to the shed.
8. `SELL WHEAT`.
9. Repeat the production cycle.

### V3 - Farm Management

Improve tile management and allow the agent to manage multiple plants simultaneously.

### V4 - Crop Selection

Compare different crops based on:

- Seed cost
- Base market price
- Time to yield
- Yield
- Tile occupancy
- Watering requirements
- Expected profit

### V5 - Market Strategy

Use current market prices and market inventory to improve selling decisions.

### V6 - Fertilizer

Implement `FERTILIZE` and `COLLECT_FERTILIZER`.

Evaluate whether fertilizer increases expected profit enough to justify its opportunity cost.

### V7 - Animals

Implement:

- `BUILD_COOP`
- `BUILD_PASTURE`
- `BUY_ANIMAL`
- `PLACE`
- `FEED`
- `CARE`
- `HARVEST`

Evaluate Goose, Cow and Sheep production.

### V8 - Farm Hands

Implement `HIRE` and evaluate whether additional labor generates more value than its cost.

### V9 - Land Expansion

Implement `BUY_LAND` and determine when expansion becomes economically justified.

### V10 - Strategic Agent

Combine crop selection, animals, fertilizer, labor, land expansion and market decisions.

### V11 - Advanced Decision Making

Evaluate whether more advanced methods such as optimization, simulation, machine learning or reinforcement learning can improve the rule-based strategy.

---

## 6. Evaluation

Local experiments should record:

- Final money
- Profit
- Production
- Sales
- Lost resources
- Farm utilization
- Farm hand utilization
- Land purchased
- Fertilizer usage
- Animal production
- Performance against different opponents

---

## 7. Development Principle

The agent will be developed incrementally.

Each major strategy change should be tested locally before being submitted to Kaggle.

Experiments should change a limited number of variables at a time so that improvements or regressions can be attributed to specific changes.

---

## 8. Versioning

Each significant strategy should receive a version identifier.

Example:

- V1 - Observer
- V2 - Wheat baseline
- V3 - Multi-tile Wheat
- V4 - Crop selection
- V5 - Market strategy

Experimental results should be recorded in `experiments.md`.