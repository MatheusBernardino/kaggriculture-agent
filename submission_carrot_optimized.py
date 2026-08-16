"""Carrot throughput agent for the Kaggriculture competition.

The agent uses one hand per day.  Farmer and hand choose different tiles in
the same observation and market actions are returned alongside both workers'
actions on every turn.
"""

CROP = "CARROT"
SEED_COST = 20
MAX_CROPS = 25
SEED_BUFFER = 2
# The agent does not use fertilizer.  Carrot therefore tops out at three units;
# the environment's fourth unit requires a fertilized watering action.
TARGET_HARVEST_YIELD = 3
SHED_TILES = ((4, 4), (4, 5), (5, 4), (5, 5))


def _step_toward(x, y, target_x, target_y):
    if x > target_x:
        return "WEST"
    if x < target_x:
        return "EAST"
    if y > target_y:
        return "NORTH"
    if y < target_y:
        return "SOUTH"
    return None


def _distance(x, y, target_x, target_y):
    return abs(x - target_x) + abs(y - target_y)


def _is_carrot(tile):
    return isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == CROP


def _ready_to_harvest(obs, tile):
    """Harvest only after the day-3 watering has delivered full yield.

    ``max_yield_day`` is day 3, but WATER is the operation that increases a
    one-time crop's yield.  At the start of day 3 a normal carrot can still
    have two units; it becomes a three-unit carrot only after that day's
    watering.  On day 4, harvest whatever remains before decay removes it.
    """
    if not _is_carrot(tile):
        return False
    age = obs["day"] - tile["planted_day"]
    yield_units = tile.get("yield_units", 0)
    return yield_units > 0 and (
        (age >= 3 and yield_units >= TARGET_HARVEST_YIELD)
        or age > 3
    )


def _farm_tasks(obs, x, y, have_seed, excluded_position=None, priorities=None):
    """Return the closest highest-priority actionable crop tile.

    Only ``None`` tiles are candidates for planting.  Locked tiles are never
    selected for agricultural actions.
    """
    farm = obs["farms"][obs["player"]]
    candidates = []
    priorities = priorities or {"water": 0, "harvest": 1, "plant": 2}

    for tile_y, row in enumerate(farm["tiles"]):
        for tile_x, tile in enumerate(row):
            if (tile_x, tile_y) == excluded_position:
                continue

            if tile is None:
                if have_seed:
                    candidates.append((tile_x, tile_y, "plant"))
                continue

            if not _is_carrot(tile):
                continue

            if not tile.get("watered_today", False):
                candidates.append((tile_x, tile_y, "water"))
            if _ready_to_harvest(obs, tile):
                candidates.append((tile_x, tile_y, "harvest"))

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda task: (
            priorities[task[2]],
            _distance(x, y, task[0], task[1]),
        ),
    )


def _action_for_target(x, y, target):
    if target is None:
        return ["PASS"]

    target_x, target_y, purpose = target
    step = _step_toward(x, y, target_x, target_y)
    if step is not None:
        return [step]
    if purpose == "plant":
        return ["PLANT", CROP]
    if purpose == "water":
        return ["WATER"]
    if purpose == "harvest":
        return ["HARVEST"]
    if purpose == "drop":
        return ["DROP"]
    return ["PASS"]


def _hand_target(obs, hand_index, have_seed, excluded_position):
    farm = obs["farms"][obs["player"]]
    hand_x, hand_y = farm["hands"][hand_index]
    inventory = obs["private"]["inventories"][hand_index + 1]

    # This is deliberately first: harvested goods reach the shed immediately,
    # leaving the hand free to collect again after the market sells them.
    if any(quantity > 0 for quantity in inventory.values()):
        shed_x, shed_y = min(
            SHED_TILES,
            key=lambda position: _distance(hand_x, hand_y, position[0], position[1]),
        )
        return (shed_x, shed_y, "drop")

    return _farm_tasks(
        obs,
        hand_x,
        hand_y,
        have_seed,
        excluded_position=excluded_position,
        priorities={"water": 0, "harvest": 1, "plant": 2},
    )


def carrot_throughput_agent(obs):
    player = obs["player"]
    farm = obs["farms"][player]
    private = obs["private"]
    seeds = private["seeds"].get(CROP, 0)
    shed_carrots = private["shed"].get(CROP, 0)

    active_crops = sum(
        1
        for row in farm["tiles"]
        for tile in row
        if _is_carrot(tile)
    )

    market = []
    # Market actions are independent from movement/actions, so do not return
    # early after selling or hiring.
    if obs["hour"] == 0 and farm.get("hires_today", 0) == 0:
        market.append(["HIRE"])
    if shed_carrots > 0:
        market.append(["SELL", CROP, shed_carrots])

    desired_seeds = min(SEED_BUFFER, MAX_CROPS - active_crops)
    seed_order = max(0, desired_seeds - seeds)
    affordable_seeds = int(farm["money"] // SEED_COST)
    seed_order = min(seed_order, affordable_seeds)
    if seed_order:
        market.append(["BUY_SEED", CROP, seed_order])

    have_seed = seeds > 0
    farmer_x, farmer_y = farm["farmer"]
    farmer_target = _farm_tasks(
        obs,
        farmer_x,
        farmer_y,
        have_seed,
        priorities={"water": 0, "harvest": 1, "plant": 2},
    )
    farmer = _action_for_target(farmer_x, farmer_y, farmer_target)

    hands = []
    if farm["hands"]:
        hand_x, hand_y = farm["hands"][0]
        reserved_position = farmer_target[:2] if farmer_target is not None else None
        hand_target = _hand_target(obs, 0, have_seed, reserved_position)
        hands.append(_action_for_target(hand_x, hand_y, hand_target))

    return {"farmer": farmer, "hands": hands, "market": market}


# Kaggle accepts a callable agent; this alias matches the conventional name.
agent = carrot_throughput_agent
