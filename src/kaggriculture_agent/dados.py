'''
Dados estaticos da competicao Kaggriculture.

Concentra as constantes publicadas no README oficial da competicao
(https://www.kaggle.com/competitions/kaggriculture/data) e validadas contra
a engine `kaggle_environments.envs.kaggriculture`.
'''

# ---------------------------------------------------------------------------
# Configuração geral
# ---------------------------------------------------------------------------

CONFIG_DEFAULTS = {
    'episodeSteps': 720,
    'boardSize': 10,
    'startingMoney': 3000,
    'maxMarketOrdersPerTurn': 10,
    'turnsPerDay': 24,
    'shedCapacity': 100,
    'weedSpawnChance': 0.005,
    'townShopUnlockInterval': 3,
    'townShopSellInterval': 4,
    'townCenterSellInterval': 24,
}

DAYS_PER_SEASON = 30
TURNS_PER_DAY = 24
SEASON_TURNS = DAYS_PER_SEASON * TURNS_PER_DAY

BOARD_SIZE = 10
QUADRANT_SIZE = 5
QUADRANTS = ('NW', 'NE', 'SW', 'SE')

LAND_COSTS = (1000, 2000, 4000)

SHED_CAPACITY = 100
MAX_MARKET_ORDERS_PER_TURN = 10


# ---------------------------------------------------------------------------
# Culturas e animais
# ---------------------------------------------------------------------------
# yield_type:
#   'one_time' = uma colheita principal
#   'ongoing'  = produção recorrente
#
# max_yield:
#   Para culturas, é o limite de produção.
#   Para animais, é o limite de produto não colhido acumulado no animal.

CROPS = {
    'WHEAT': {
        'yield_type': 'one_time',
        'seed_cost': 10,
        'base_price': 25,
        'first_yield_days': 2,
        'max_yield_day': 4,
        'subsequent_yields': None,
        'max_yield': 6,
        'max_yield_unfertilized': 4,
        'action_cost': 1,
        'yield_per_tile_day': 0.80,
    },
    'CARROT': {
        'yield_type': 'one_time',
        'seed_cost': 20,
        'base_price': 35,
        'first_yield_days': 2,
        'max_yield_day': 3,
        'subsequent_yields': None,
        'max_yield': 4,
        'max_yield_unfertilized': 3,
        'action_cost': 1,
        'yield_per_tile_day': 0.75,
    },
    'TOMATO': {
        'yield_type': 'ongoing',
        'seed_cost': 50,
        'base_price': 60,
        'first_yield_days': 8,
        'max_yield_day': 11,
        'subsequent_yields': 'daily',
        'max_yield': 4,
        'action_cost': 1,
        'yield_per_tile_day': 0.33,
        'production_interval_days': 1,
        'production_ages': (8, 9, 10, 11),
    },
    'STRAWBERRY': {
        'yield_type': 'ongoing',
        'seed_cost': 100,
        'base_price': 120,
        'first_yield_days': 10,
        'max_yield_day': 16,
        'subsequent_yields': 'every_other_day',
        'max_yield': 4,
        'action_cost': 1,
        'yield_per_tile_day': 0.24,
        'production_interval_days': 2,
        'production_ages': (10, 12, 14, 16),
    },
    'MELON': {
        'yield_type': 'one_time',
        'seed_cost': 80,
        'base_price': 250,
        'first_yield_days': 10,
        'max_yield_day': 12,
        'subsequent_yields': None,
        'max_yield': 6,
        'action_cost': 1,
        'yield_per_tile_day': 0.55,
        'bonus_window': (6, 12),
    },
}


ANIMALS = {
    'GOOSE': {
        'product': 'EGG',
        'structure': 'COOP',
        'seed_cost': 300,
        'base_price': 50,
        'first_yield_days': 4,
        'production_interval_days': 1,
        'max_held': 4,
        'action_cost': 1,
        'build_action_cost': 1,
        'yield_per_tile_day': 1.00,
    },
    'COW': {
        'product': 'MILK',
        'structure': 'PASTURE',
        'seed_cost': 400,
        'base_price': 160,
        'first_yield_days': 8,
        'production_interval_days': 2,
        'max_held': 6,
        'action_cost': 1,
        'build_action_cost': 1,
        'yield_per_tile_day': 0.50,
    },
    'SHEEP': {
        'product': 'WOOL',
        'structure': 'PASTURE',
        'seed_cost': 500,
        'base_price': 200,
        'first_yield_days': 6,
        'production_interval_days': 3,
        'max_held': 6,
        'action_cost': 1,
        'build_action_cost': 1,
        'yield_per_tile_day': 0.33,
    },
}


# Produtos que podem ser produzidos/negociados.
PRODUCTS = (
    'WHEAT',
    'CARROT',
    'TOMATO',
    'STRAWBERRY',
    'MELON',
    'EGG',
    'MILK',
    'WOOL',
    'FERTILIZER',
)

SEEDS = tuple(CROPS.keys())
ANIMAL_PRODUCTS = tuple(animal['product'] for animal in ANIMALS.values())


# ---------------------------------------------------------------------------
# Mercado
# ---------------------------------------------------------------------------
# f(inv) = shape da curva.
#
# O preço é:
#   base + sign * amp * f(abs(inv - I0))
#
# sign = +1 quando inv < I0
# sign = -1 quando inv > I0
#
# amp = target * base / f(T)

MARKET_PARAMS = {
    'WHEAT': {
        'base': 25,
        'I0': 10_000,
        'T': 400,
        'below_func': 'sqrt',
        'below_target': 0.80,
        'above_func': 'log',
        'above_target': 0.20,
    },
    'CARROT': {
        'base': 35,
        'I0': 10_000,
        'T': 450,
        'below_func': 'log',
        'below_target': 0.20,
        'above_func': 'sqrt',
        'above_target': 0.70,
    },
    'TOMATO': {
        'base': 60,
        'I0': 10_000,
        'T': 200,
        'below_func': 'linear',
        'below_target': 0.40,
        'above_func': 'sqrt',
        'above_target': 0.60,
    },
    'STRAWBERRY': {
        'base': 120,
        'I0': 10_000,
        'T': 100,
        'below_func': 'sqrt',
        'below_target': 0.70,
        'above_func': 'linear',
        'above_target': 1.60,
    },
    'MELON': {
        'base': 250,
        'I0': 10_000,
        'T': 300,
        'below_func': 'log',
        'below_target': 0.20,
        'above_func': 'sq',
        'above_target': 3.60,
    },
    'EGG': {
        'base': 50,
        'I0': 10_000,
        'T': 332,
        'below_func': 'linear',
        'below_target': 0.40,
        'above_func': 'log',
        'above_target': 0.20,
    },
    'MILK': {
        'base': 160,
        'I0': 10_000,
        'T': 122,
        'below_func': 'sqrt',
        'below_target': 0.60,
        'above_func': 'linear',
        'above_target': 1.60,
    },
    'WOOL': {
        'base': 200,
        'I0': 10_000,
        'T': 105,
        'below_func': 'log',
        'below_target': 0.20,
        'above_func': 'sq',
        'above_target': 3.20,
    },
    'FERTILIZER': {
        'base': 100,
        'I0': 10_000,
        'T': 200,
        'below_func': 'linear',
        'below_target': 0.40,
        'above_func': 'linear',
        'above_target': 0.40,
    },
}
#---------------------------------------------------------------------------
#             (venda)
# Produto	    Base	Escassez -T	    Normal	Excesso +T	Muito excesso +2T
# Wheat	        $25	    $45	            $25	    $20	        $19
# Carrot	    $35	    $42	            $35	    $10	        $1
# Tomato	    $60	    $84	            $60	    $24         $9
# Strawberry	$120	$204	        $120	$1	        $1
# Melon	        $250	$300	        $250	$1	        $1
# Egg	        $50	    $70	            $50	    $40	        $39
# Milk	        $160	$256	        $160	$1	        $1
# Tool	        $200	$240	        $200	$1	        $1
# Fertilizer	$100	$140	        $100	$60	        $20
#---------------------------------------------------------------------------


# Preços na vizinhança dos pontos de calibração fornecidos no README.
MARKET_REFERENCE_PRICES = {
    'WHEAT':       {'minus_T': 45,  'plus_T': 20, 'plus_2T': 19},
    'CARROT':      {'minus_T': 42,  'plus_T': 10, 'plus_2T': 1},
    'TOMATO':      {'minus_T': 84,  'plus_T': 24, 'plus_2T': 9},
    'STRAWBERRY':  {'minus_T': 204, 'plus_T': 1,  'plus_2T': 1},
    'MELON':       {'minus_T': 300, 'plus_T': 1,   'plus_2T': 1},
    'EGG':         {'minus_T': 70,  'plus_T': 40,  'plus_2T': 39},
    'MILK':        {'minus_T': 256, 'plus_T': 1,   'plus_2T': 1},
    'WOOL':        {'minus_T': 240, 'plus_T': 1,   'plus_2T': 1},
    'FERTILIZER':  {'minus_T': 140, 'plus_T': 60,  'plus_2T': 20},
}

# Somente estes produtos podem ser comprados com BUY_PRODUCT.
BUYABLE_PRODUCTS = ('WHEAT', 'FERTILIZER')


# ---------------------------------------------------------------------------
# Lojas da cidade e demanda
# ---------------------------------------------------------------------------

SHOP_DEMAND = {
    'BAKERY': {
        'products': ('EGG', 'WHEAT'),
    },
    'PIZZA_SHOP': {
        'products': ('MILK', 'TOMATO', 'WHEAT'),
    },
    'BRUNCH_SPOT': {
        'products': ('EGG', 'WHEAT', 'STRAWBERRY'),
    },
    'YARN_STORE': {
        'products': ('WOOL',),
        'multiplier': {'WOOL': 2},
    },
    'ICE_CREAM_SHOP': {
        'products': ('STRAWBERRY', 'MILK', 'WHEAT'),
    },
    'PET_CAFE': {
        'products': ('CARROT',),
        'multiplier': {'CARROT': 2},
    },
    'SMOOTHIE_SHOP': {
        'products': ('STRAWBERRY', 'MILK'),
    },
    'FARMERS_MARKET': {
        'products': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'),
    },
}

SHOP_TYPES = tuple(SHOP_DEMAND.keys())
MAX_SHOP_INSTANCES = 8


# ---------------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------------

MOVEMENT_ACTIONS = (
    'NORTH',
    'SOUTH',
    'EAST',
    'WEST',
)

FARM_ACTIONS = (
    'PICKUP',
    'DROP',
    'PLANT',
    'WATER',
    'HARVEST',
    'FERTILIZE',
    'PLACE',
    'FEED',
    'COLLECT_FERTILIZER',
    'CARE',
    'BUILD_COOP',
    'BUILD_PASTURE',
    'DIG',
    'PASS',
)

MARKET_ACTIONS = (
    'BUY_SEED',
    'BUY_ANIMAL',
    'BUY_PRODUCT',
    'SELL',
    'HIRE',
    'BUY_LAND',
)

ALL_ACTIONS = MOVEMENT_ACTIONS + FARM_ACTIONS + MARKET_ACTIONS


# ---------------------------------------------------------------------------
# Estruturas e regras auxiliares
# ---------------------------------------------------------------------------

STRUCTURES = {
    'GOOSE': 'COOP',
    'COW': 'PASTURE',
    'SHEEP': 'PASTURE',
}

PRODUCE_TO_ANIMAL = {
    'EGG': 'GOOSE',
    'MILK': 'COW',
    'WOOL': 'SHEEP',
}

ONE_TIME_CROPS = tuple(
    crop for crop, data in CROPS.items()
    if data['yield_type'] == 'one_time'
)

ONGOING_CROPS = tuple(
    crop for crop, data in CROPS.items()
    if data['yield_type'] == 'ongoing'
)

# Idades a partir das quais a janela de bônus de irrigação começa.
# Para one-time crops: ceil(max_yield_day / 2).
BONUS_WINDOW_START = {
    crop: (data['max_yield_day'] + 1) // 2
    for crop, data in CROPS.items()
    if data['yield_type'] == 'one_time'
}

# Janelas específicas explicitamente documentadas.
BONUS_WINDOWS = {
    'WHEAT': (2, 4),
    'CARROT': (2, 3),
    'MELON': (6, 12),
}


# ---------------------------------------------------------------------------
# Funções pequenas para facilitar o uso pelo agente
# ---------------------------------------------------------------------------

def get_crop(name: str) -> dict:
    '''Retorna os dados de uma cultura pelo nome.'''
    return CROPS[name.upper()]


def get_animal(name: str) -> dict:
    '''Retorna os dados de um animal pelo nome.'''
    return ANIMALS[name.upper()]


def get_market(name: str) -> dict:
    '''Retorna os parâmetros de mercado de um produto.'''
    return MARKET_PARAMS[name.upper()]


def get_product_base_price(name: str) -> float:
    '''Retorna o preço-base de um produto.'''
    return MARKET_PARAMS[name.upper()]['base']


def production_product(animal: str) -> str:
    '''Retorna o produto produzido por um animal.'''
    return ANIMALS[animal.upper()]['product']


def required_structure(animal: str) -> str:
    '''Retorna a estrutura necessária para colocar o animal.'''
    return ANIMALS[animal.upper()]['structure']


def crop_seed_cost(crop: str) -> int:
    '''Retorna o custo do seed de uma cultura.'''
    return CROPS[crop.upper()]['seed_cost']


def animal_cost(animal: str) -> int:
    '''Retorna o custo de compra de um animal.'''
    return ANIMALS[animal.upper()]['seed_cost']


__all__ = [
    'CONFIG_DEFAULTS',
    'DAYS_PER_SEASON',
    'TURNS_PER_DAY',
    'SEASON_TURNS',
    'BOARD_SIZE',
    'QUADRANT_SIZE',
    'QUADRANTS',
    'LAND_COSTS',
    'SHED_CAPACITY',
    'MAX_MARKET_ORDERS_PER_TURN',
    'CROPS',
    'ANIMALS',
    'PRODUCTS',
    'SEEDS',
    'ANIMAL_PRODUCTS',
    'MARKET_PARAMS',
    'MARKET_REFERENCE_PRICES',
    'BUYABLE_PRODUCTS',
    'SHOP_DEMAND',
    'SHOP_TYPES',
    'MAX_SHOP_INSTANCES',
    'MOVEMENT_ACTIONS',
    'FARM_ACTIONS',
    'MARKET_ACTIONS',
    'ALL_ACTIONS',
    'STRUCTURES',
    'PRODUCE_TO_ANIMAL',
    'ONE_TIME_CROPS',
    'ONGOING_CROPS',
    'BONUS_WINDOW_START',
    'BONUS_WINDOWS',
    'get_crop',
    'get_animal',
    'get_market',
    'get_product_base_price',
    'production_product',
    'required_structure',
    'crop_seed_cost',
    'animal_cost',
]
