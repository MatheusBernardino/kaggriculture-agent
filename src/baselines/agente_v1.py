"""
Agente Kaggriculture V1 (Extraído de agente.ipynb)

Contém a implementação original da função `agent(obs)` e seus métodos auxiliares.
O arquivo original `agente.ipynb` foi preservado intacto.
"""

# Listas globais de rastreamento/debug utilizadas pelas funções do agente
action_debug = []
plant_debug = []
money_debug = []
sell_debug = []



# ============================================================
# CROP DATA
# Static information provided by the Kaggriculture competition.
#
# These values describe how each crop behaves.
# Current market prices are NOT stored here because they
# change during the game and are provided by obs["market"].
# ============================================================

CROP_DATA = {

    # Wheat is a one-time crop.
    # Without fertilizer, its maximum yield is 4.
    # With fertilizer, its maximum yield is 6.
    "WHEAT": {
        "yield_type": "ONE_TIME",
        "seed_cost": 10,
        "base_price": 25,
        "first_yield_day": 2,
        "max_yield_day": 4,
        "max_yield": 6,
        "unfertilized_max_yield": 4,
        "yield_per_tile_day": 0.80,
    },

    # Carrot is a one-time crop.
    "CARROT": {
        "yield_type": "ONE_TIME",
        "seed_cost": 20,
        "base_price": 35,
        "first_yield_day": 2,
        "max_yield_day": 3,
        "max_yield": 4,
        "unfertilized_max_yield": 3,
        "yield_per_tile_day": 0.75,
    },

    # Tomato is an ongoing crop with four scheduled yields.
    "TOMATO": {
        "yield_type": "ONGOING",
        "seed_cost": 50,
        "base_price": 60,
        "first_yield_day": 8,
        "max_yield_day": 11,
        "max_yield": 4,
        "subsequent_yield_interval": 1,
        "yield_per_tile_day": 0.33,
    },

    # Strawberry is an ongoing crop with four scheduled yields.
    "STRAWBERRY": {
        "yield_type": "ONGOING",
        "seed_cost": 100,
        "base_price": 120,
        "first_yield_day": 10,
        "max_yield_day": 16,
        "max_yield": 4,
        "subsequent_yield_interval": 2,
        "yield_per_tile_day": 0.24,
    },

    # Melon is a one-time crop with a high base market price.
    "MELON": {
        "yield_type": "ONE_TIME",
        "seed_cost": 80,
        "base_price": 250,
        "first_yield_day": 10,
        "max_yield_day": 10,
        "max_yield": 6,
        "unfertilized_max_yield": 6,
        "yield_per_tile_day": 0.55,
    },
}


# ============================================================
# ANIMAL DATA
# Static information provided by the Kaggriculture competition.
#
# Each animal produces a specific product over time.
# Animal production continues as long as the animal survives.
# ============================================================

ANIMAL_DATA = {

    # Geese live on a COOP and produce eggs every day
    # after the initial production delay.
    "GOOSE": {
        "product": "EGG",
        "purchase_cost": 300,
        "base_price": 50,
        "first_yield_day": 4,
        "yield_interval_days": 1,
        "max_held": 4,
        "structure": "COOP",
        "yield_per_tile_day": 1.00,
    },

    # Cows live on a PASTURE and produce milk every two days.
    "COW": {
        "product": "MILK",
        "purchase_cost": 400,
        "base_price": 160,
        "first_yield_day": 8,
        "yield_interval_days": 2,
        "max_held": 6,
        "structure": "PASTURE",
        "yield_per_tile_day": 0.50,
    },

    # Sheep live on a PASTURE and produce wool every three days.
    "SHEEP": {
        "product": "WOOL",
        "purchase_cost": 500,
        "base_price": 200,
        "first_yield_day": 6,
        "yield_interval_days": 3,
        "max_held": 6,
        "structure": "PASTURE",
        "yield_per_tile_day": 0.33,
    },
}


# ============================================================
# PRODUCT DATA
# Describes where each market product comes from.
#
# The current market price is NOT stored here.
# It must always be read from:
# obs["market"]["prices"][product]
# ============================================================

PRODUCT_DATA = {

    # Crop products
    "WHEAT": {
        "source_type": "CROP",
        "source": "WHEAT",
    },

    "CARROT": {
        "source_type": "CROP",
        "source": "CARROT",
    },

    "TOMATO": {
        "source_type": "CROP",
        "source": "TOMATO",
    },

    "STRAWBERRY": {
        "source_type": "CROP",
        "source": "STRAWBERRY",
    },

    "MELON": {
        "source_type": "CROP",
        "source": "MELON",
    },

    # Animal products
    "EGG": {
        "source_type": "ANIMAL",
        "source": "GOOSE",
    },

    "MILK": {
        "source_type": "ANIMAL",
        "source": "COW",
    },

    "WOOL": {
        "source_type": "ANIMAL",
        "source": "SHEEP",
    },

    # Fertilizer is produced by all surviving animals.
    "FERTILIZER": {
        "source_type": "ANIMAL_BYPRODUCT",
        "source": "ALL_ANIMALS",
    },
}

def is_crop_ready_to_harvest(obs,tile):
    """
    Determine whether a crop has reached its configured harvest point.

    The decision is based on:
    - the tile being a plant;
    - the crop having available yield;
    - the crop's age;
    - the crop's configured max_yield_day.
    """

    if tile is None:
        return False

    if tile.get("kind") != "PLANT":
        return False
    crop_name = tile["crop"]
    crop = CROP_DATA[crop_name]

    age = obs["day"] - tile["planted_day"]

    min_harvest_yield = max(
        1,
        crop["unfertilized_max_yield"] - 1
    )

    return (tile.get("yield_units", 0) >= min_harvest_yield 
            and age >= crop["max_yield_day"]
    )

def get_harvest_priority(obs, tile, x, y, fx, fy):

    if tile is None or tile.get("kind") != "PLANT":
        return None
    
    crop = CROP_DATA[tile["crop"]]
    yield_units = tile.get("yield_units", 0)
    max_yield = crop["unfertilized_max_yield"]  # use max_yield sem fertilizante

    if yield_units <= 0:
        return None

    steps_to_decay = (
        tile["max_lifespan_step"] - obs["step"]
    )

    distance = abs(x - fx) + abs(y - fy)

    # Quanto tempo sobra depois de chegar à planta
    slack = steps_to_decay - distance

    # ---------------------------------------------------------
    # YIELD MÁXIMO
    # ---------------------------------------------------------
    if yield_units >= max_yield:

        # Está perto demais do decay.
        #if slack <= 2:
            return 0

        # Já está no máximo, mas ainda pode esperar.
       #return None

    # ---------------------------------------------------------
    # YIELD 2
    # ---------------------------------------------------------
    if yield_units >= max_yield - 1:

        # Se ainda há tempo razoável para continuar crescendo,
        # não colher ainda.
        if slack > 2:
            return None

        # Está ficando perigoso esperar.
        return 0

    # ---------------------------------------------------------
    # YIELD 1
    # ---------------------------------------------------------
    return None

# ============================================================
# CURRENT EXPERIMENT
# ============================================================
# Crop currently being used by the experimental agent.
# Changing this value will allow the same agent logic
# to be tested with different crops later.

CROP = "MELON"

# Get the static information for the selected crop.
crop = CROP_DATA[CROP]



if __name__ == '__main__':
    print(f"Selected crop: {CROP}")
    print(f"Seed cost: {crop['seed_cost']}")
    print(f"Base price: {crop['base_price']}")
    print(f"First yield day: {crop['first_yield_day']}")
    print(f"Max yield day: {crop['max_yield_day']}")
    print(f"Max yield: {crop['max_yield']}")


def get_farmer_tile(obs):
    player = obs["player"]
    farm = obs["farms"][player]

    x, y = farm["farmer"]

    return farm["tiles"][y][x]

# Returns one movement action that reduces the Manhattan distance
# between the farmer's current position and the target position.
# The function moves horizontally first, then vertically.
# Returns None when the farmer is already at the target.
'''def step_toward(fx, fy, tx, ty):
    if fx > tx:
        return "WEST"
    if fx < tx:
        return "EAST"
    if fy > ty:
        return "NORTH"
    if fy < ty:
        return "SOUTH"
    return None'''
def step_toward(x, y, tx, ty, first_axis="x"):
    """
    Retorna o próximo movimento em direção ao alvo.

    first_axis:
        "x" -> tenta X primeiro
        "y" -> tenta Y primeiro
    """

    dx = tx - x
    dy = ty - y

    if first_axis == "x":

        if dx > 0:
            return "EAST"
        if dx < 0:
            return "WEST"

        if dy > 0:
            return "SOUTH"
        if dy < 0:
            return "NORTH"

    else:  # first_axis == "y"

        if dy > 0:
            return "SOUTH"
        if dy < 0:
            return "NORTH"

        if dx > 0:
            return "EAST"
        if dx < 0:
            return "WEST"

    return None


def find_nearby_harvest(obs, x, y, max_distance=6):
    farm = obs["farms"][obs["player"]]

    candidates = []

    for ty, row in enumerate(farm["tiles"]):
        for tx, tile in enumerate(row):

            if not isinstance(tile, dict):
                continue

            if tile.get("kind") != "PLANT":
                continue

            harvest_priority = get_harvest_priority(
                obs,
                tile,
                tx,
                ty,
                x,
                y
            )

            if harvest_priority is None:
                continue

            distance = abs(tx - x) + abs(ty - y)

            if distance <= max_distance:
                candidates.append(
                    (
                        harvest_priority,
                        distance,
                        tx,
                        ty
                    )
                )

    if not candidates:
        return None

    candidates.sort()

    _, _, tx, ty = candidates[0]

    return (tx, ty)

def find_final_harvest_target(obs):
    """
    Encontra qualquer crop ainda plantado para colheita final.
    Ignora completamente yield, prioridade e tempo de crescimento.
    """

    player = obs["player"]
    farm = obs["farms"][player]

    fx, fy = farm["farmer"]

    candidates = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):

            if not isinstance(tile, dict):
                continue

            if tile.get("kind") != "PLANT":
                continue

            distance = abs(x - fx) + abs(y - fy)

            candidates.append(
                (x, y, "harvest", distance)
            )

    if not candidates:
        return None

    # Pega o crop mais próximo
    candidates.sort(key=lambda c: c[3])

    return candidates[0][:3]

# Finds the best available farm task based on the current observation.
# Tasks are prioritized as harvest, water, and plant.
# Within the same task priority, the nearest tile is selected
# using Manhattan distance.
# The target is recalculated from the current state each turn.
def find_target(obs, have_seed):
    player = obs["player"]
    farm = obs["farms"][player]

    fx, fy = farm["farmer"]
    candidates_farmer = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            # -------------------------------------------------
            # TILE VAZIO → PLANT
            # -------------------------------------------------
            if tile is None:
                if have_seed:
                                                   
                    days_remaining = 29 - obs["day"]

                    # Para carrot, precisamos de 2 dias
                    # para chegar ao yield 2.
                    min_days_to_yield = crop["first_yield_day"]

                    if days_remaining >= min_days_to_yield:
                        candidates_farmer.append((x, y, "plant")
                        )
                continue
            
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "WEED":
                candidates_farmer.append((x, y, "dig"))
                continue
            if tile.get("kind") != "PLANT":
                continue
            # -------------------------------------------------
            # HARVEST
            # -------------------------------------------------
            harvest_priority = get_harvest_priority(
                obs,
                tile,
                x,
                y,
                fx,
                fy
            )

            if harvest_priority is not None:
                candidates_farmer.append(
                    (x, y, "harvest",harvest_priority)
                )

            # A crop needs to be watered today.
            if (not tile["watered_today"]) and tile.get("kind") == "PLANT":
                candidates_farmer.append((x, y, "water"))

            # The crop is ready to harvest.
            #if is_crop_ready_to_harvest(obs, tile):
             #   candidates_farmer.append((x, y, "harvest"))

    if not candidates_farmer:
        return None

    priority = {
        "water": 1,
        "dig": 1,
        "plant": 1,
        "harvest": 0
        
    }

    candidates_farmer.sort(
        key=lambda c: (
            priority[c[2]],
            c[3] if c[2] == "harvest" else 999,
            0 if c[0] == 4 else 1,
            abs(c[0] - fx) + abs(c[1] - fy),
        )
    )
    '''    debug_targets.append({
        "day": obs["day"],
        "hour": obs["hour"],
        "seed": have_seed,
        "candidates": candidates_farmer.copy(),
    })'''
    best = candidates_farmer[0]
    return best[:3]

def find_hand_target(obs, hand_idx, have_seed, excluded_targets=None):
    if excluded_targets is None:
        excluded_targets = set()
    player = obs["player"]
    farm = obs["farms"][player]

    # ---------------------------------------------------------
    # Posição do hand
    # ---------------------------------------------------------
    hx, hy = farm["hands"][hand_idx]

    # Inventário:
    # inventories[0] = farmer
    # inventories[1] = hand 1
    #inventory = obs["private"]["inventories"][hand_idx + 1]

    # ---------------------------------------------------------
    # Procurar tarefas
    # ---------------------------------------------------------
    candidates = []

    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):

            if (x, y) in excluded_targets:
                continue
            # -------------------------------------------------
            # PLANT
            # -------------------------------------------------
            if tile is None:
                if have_seed:
                    candidates.append((x, y, "plant"))
                    
            if not isinstance(tile, dict):
                continue

            if tile.get("kind") == "WEED":
                candidates.append((x, y, "dig"))
                continue
            if tile.get("kind") != "PLANT":
                continue
            # -------------------------------------------------
            # WATER
            # -------------------------------------------------
            # A crop needs to be watered today.
            if (not tile["watered_today"]) and tile.get("kind") == "PLANT":
                # Não deixa o hand regar a mesma planta
                # que o farmer já escolheu.
                candidates.append((x, y, "water"))

            # -------------------------------------------------
            # HARVEST
            # -------------------------------------------------
            harvest_priority = get_harvest_priority(
                obs,
                tile,
                x,
                y,
                hx,
                hy
            )

            if harvest_priority is not None:
                candidates.append(
                    (x, y, "harvest",harvest_priority)
                )

    if not candidates:
        return None

    # ---------------------------------------------------------
    # Prioridade do HAND
    #
    # WATER   = 1
    # HARVEST = 2
    # PLANT   = 4
    # DIG     = 3
    #
    # DROP já é tratado antes.
    # ---------------------------------------------------------
    priority = {
        "water": 1,
        "plant": 1,
        "dig": 2,
        "harvest": 0
        
    }

    candidates.sort(
        key=lambda c: (
            priority[c[2]],
            c[3] if c[2] == "harvest" else 999,
            0 if c[1] == 4 else 1,
            abs(c[0] - hx) + abs(c[1] - hy),
        )
    )

    return candidates[0]

def get_sell_actions(obs):

    shed = obs["private"]["shed"]
    actions = []

    for product, quantity in shed.items():

        if quantity <= 0:
            continue
        elif quantity >= 5:
        # regras específicas de venda
            actions.append(["SELL", product, 5])
        else:
            actions.append(["SELL",product,quantity])

    return actions

def save_action(obs, action):
    farm = obs["farms"][obs["player"]]

    action_debug.append({
        "step": obs["step"],
        "day": obs["day"],
        "hour": obs["hour"],
        "farmer_pos": tuple(farm["farmer"]),
        "hands_pos": [tuple(h) for h in farm["hands"]],
        "farmer": action["farmer"],
        "hands": action["hands"],
        "market": action["market"],
    })

    return action

def get_crop(obs):
    return "STRAWBERRY" if obs["day"] <= 20 else "TOMATO"

def agent(obs):

    '''observations.append(obs)
    try:
        # Toda a sua lógica principal entra aqui
        action = my_main_logic(obs)
        return action
    except Exception as e:
        print(f"Erro capturado no Step: {e}")
         Retorna uma ação neutra válida no formato esperado pelo Kaggriculture
        return {"farmer": "PASS", "hands": [], "market": []}'''
    # ---------------------------------------------------------
    # ESTADO
    # ---------------------------------------------------------
    CROP = get_crop(obs)
    crop = CROP_DATA[CROP]
    player = obs["player"]
    farm = obs["farms"][player]

    fx, fy = farm["farmer"]
    hands = farm["hands"]

    seeds = obs["private"]["seeds"].get(CROP, 0)
    shed = obs["private"]["shed"].get(CROP, 0)

    farmer_inventory = obs["private"]["inventories"][0]
    inventory = farmer_inventory.get(CROP, 0)

    # ---------------------------------------------------------
    # DEBUG
    # ---------------------------------------------------------
    plant_debug.append({
        "step": obs["step"],
        "day": obs["day"],
        "hour": obs["hour"],
        "plants": [
            {
                "pos": (x, y),
                "yield": tile.get("yield_units", 0),
                "planted_day": tile.get("planted_day"),
                "lifespan_step": tile.get("max_lifespan_step"),
                "steps_to_decay": (
                    tile.get("max_lifespan_step", 0)
                    - obs["step"]
                ),
            }
            for y, row in enumerate(farm["tiles"])
            for x, tile in enumerate(row)
            if isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
        ]
    })
    money_debug.append({
        
        "step": obs["step"],
        "day": obs["day"],
        "hour": obs["hour"],
        "money": farm["money"],
        "seed": seeds,
        "inventory": inventory,
        "shed": shed,

        "active_crops": sum(
            1
            for row in farm["tiles"]
            for tile in row
            if isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
        ),

        "hands": len(hands),
    })

    sell_debug.append({
        "day": obs["day"],
        "hour": obs["hour"],
        "money": farm["money"],
        "shed": shed,
        "seeds": seeds,
        "inventory": inventory,
    })

    # ---------------------------------------------------------
    # MERCADO
    # ---------------------------------------------------------

    market_actions = []

    # Contrata 2 hand por dia
    HANDS_PER_DAY = 1
    max_yield_day = crop["max_yield_day"]
    if (
        obs["day"] > 2
        and (obs["day"] ) % max_yield_day == 0
    ):
        HANDS_PER_DAY = 2
    if obs["hour"] == 0 and obs["day"]<29:
        # Contrata 2 hand por dia a partir do dia 9
        #if obs["day"] >= 29 :#and obs["day"] < 28:
         #   HANDS_PER_DAY = 2

        hires_needed = HANDS_PER_DAY - farm["hires_today"]

        for _ in range(max(0, hires_needed)):
            market_actions.append(["HIRE"])
    # ---------------------------------------------------------
    # CONTROLE DE SEMENTES
    # ---------------------------------------------------------

    MAX_CROPS = 25
    MAX_SEEDS = 4

    active_crops = sum(
        1
        for row in farm["tiles"]
        for tile in row
        if (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
        )
    )

    # Compra apenas quando existe capacidade real
    # de colocar a semente no campo.
                    
    days_remaining = 29 - obs["day"]
    # Para carrot, precisamos de 2 dias
    # para chegar ao yield 2.
    min_days_to_yield = crop["first_yield_day"]
    if (
        active_crops + seeds < MAX_CROPS
        and seeds < MAX_SEEDS 
        and days_remaining >= min_days_to_yield
        and (obs["day"] < 27)
    ):
        market_actions.append(
            ["BUY_SEED", CROP, 2]
        )

    # ---------------------------------------------------------
    # VENDA
    #
    # IMPORTANTE:
    # vender NÃO deve interromper o farmer.
    # ---------------------------------------------------------
    sell_action = get_sell_actions(obs)
    market_actions.extend(sell_action)
    '''if shed <= 5 or obs["day"]>28:
        market_actions.append(
            ["SELL", CROP, shed]
        )
    else:
        market_actions.append(
            ["SELL", CROP, 5]
        )'''

    # ---------------------------------------------------------
    # TARGET DO FARMER
    # ---------------------------------------------------------

    have_seed = seeds > 0

    if obs["day"] >= 29 and active_crops > 0:
        target = find_final_harvest_target(obs)
    else:
        target = find_target(
            obs,
            have_seed
        )
    farmer_target = None

    if target is not None:
        farmer_target = (target[0], target[1])
    elif (obs["day"]==0 and obs["hour"]== 0):
            return {
            "farmer": ["NORTH"],
            "hands": [],
            "market": market_actions,
        }
    # ---------------------------------------------------------
    # TARGET DO FARM HAND
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # TARGET DOS FARM HANDS
    # ---------------------------------------------------------

    hands_actions = []

    # O alvo do farmer fica reservado.
    reserved_targets = set()

    if farmer_target is not None:
        reserved_targets.add(farmer_target)

    # Se o farmer vai plantar agora, uma semente já está comprometida.
    farmer_will_plant = (
        target is not None
        and target[2] == "plant"
        and step_toward(fx, fy, target[0], target[1]) is None
    )

    seeds_available_for_hands = seeds

    if farmer_will_plant:
        seeds_available_for_hands -= 1

    # Cria uma ação para cada hand contratado.
    for hand_idx, (hx, hy) in enumerate(hands):

        hand_target = find_hand_target(
            obs,
            hand_idx=hand_idx,
            have_seed=seeds_available_for_hands > 0,
            excluded_targets=reserved_targets,
        )

        if hand_target is None:
            hand_action = ["PASS"]

        else:
            tx, ty, purpose ,*rest = hand_target

            move = step_toward(hx, hy, tx, ty,first_axis="y")

            if move is not None:
                hand_action = [move]
                

            elif purpose == "water":
                hand_action = ["WATER"]

            elif purpose == "plant":
                hand_action = ["PLANT", CROP]

            elif purpose == "harvest":
                hand_action = ["HARVEST"]

            elif purpose == "dig":
                hand_action = ["DIG"]
            else:
                hand_action = ["PASS"]

            # Reserva o alvo para o próximo hand.
            reserved_targets.add((tx, ty))

            # Não deixa dois hands tentarem plantar com a mesma semente.
            if hand_action[0] == "PLANT":
                seeds_available_for_hands -= 1
        hands_actions.append(hand_action)

    # ---------------------------------------------------------
    # FINAL DA PARTIDA — DIA 29
    # ---------------------------------------------------------

    shed_positions = {
        (4, 4),
        (4, 5),
        (5, 4),
        (5, 5),
    }

    FINAL_DAY_RETURN_HOUR = 20

    if obs["day"] == 29 and obs["hour"] >= FINAL_DAY_RETURN_HOUR:

        if inventory > 0 and active_crops == 0:

            # Já está no shed
            if (fx, fy) in shed_positions:

                return {
                    "farmer": ["DROP"],
                    "hands": hands_actions,
                    "market": market_actions,
                }

            # Vai para o shed
            target_shed = min(
                shed_positions,
                key=lambda p:
                    abs(p[0] - fx) +
                    abs(p[1] - fy)
            )

            move = step_toward(
                fx,
                fy,
                target_shed[0],
                target_shed[1]
            )

            if move is not None:

                return {
                    "farmer": [move],
                    "hands": hands_actions,
                    "market": market_actions,
                }
                
        # ---------------------------------------------------------
        # EXECUTAR TARGET DO FARMER
        # ---------------------------------------------------------

    if target is not None:

        tx, ty, purpose,*rest = target

        move = step_toward(
            fx,
            fy,
            tx,
            ty
        )

        if move is not None:
            return {
            "farmer": [move],
            "hands": hands_actions,
            "market": market_actions,
            }

        # ---------------------------------------------
        # Chegou ao alvo
        # ---------------------------------------------

        if purpose == "plant":

            return {
                "farmer": ["PLANT", CROP],
                "hands": hands_actions,
                "market": market_actions,
            }

        if purpose == "water":

            return {
                "farmer": ["WATER"],
                "hands": hands_actions,
                "market": market_actions,
            }

        if purpose == "harvest":

            return {
                "farmer": ["HARVEST"],
                "hands": hands_actions,
                "market": market_actions,
            }
        if purpose == "dig":

            return {
            "farmer": ["DIG"],
            "hands": hands_actions,
            "market": market_actions,
            }


    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    '''if obs["hour"] == 0:

        return save_action(obs, {
            "farmer": ["WATER"],
            "hands": [hand_action] if hand_action else [],
            "market": market_actions,
        })'''

    return {
        "farmer": ["PASS"],
        "hands": hands_actions,
        "market": market_actions,
    }