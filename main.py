"""
Kaggriculture Autonomous Agent - Submission File
Arquivo autocontido compilado para execucao direta no sandbox do Kaggle.
Ponto de entrada oficial: def agent(obs)
"""

from typing import Dict, List, Optional, Set, Tuple

# ======================================================================
# MODULO: src/kaggriculture_agent/config.py
# ======================================================================
"""
Hiperparametros e limiares estrategicos do agente Kaggriculture.

Todos os "numeros magicos" da estrategia ficam centralizados aqui para que
experimentos de benchmark alterem um unico ponto do codigo. Os valores atuais
reproduzem o agente V5 (front-running + epocas) com as correcoes da V6.
"""

# ============================================================
# TABULEIRO E TEMPORADA
# ============================================================

# Celeiro central (shed) no grid 10x10, coordenadas (x, y).
POSICOES_CELEIRO: frozenset = frozenset({(4, 4), (4, 5), (5, 4), (5, 5)})
ULTIMO_DIA: int = 29
MAX_ORDENS_MERCADO: int = 10

# ============================================================
# CULTURAS: dias restantes minimos para que a semente ainda gere receita
# ============================================================
# MELON precisa de ~11 dias ate o rendimento maximo; CARROT de 3-4; WHEAT de 2-3.
DIAS_MINIMOS_CULTURA: dict = {"MELON": 12, "CARROT": 4, "WHEAT": 3}

# Ordem de preferencia ao reaproveitar sementes ja compradas (maior valor primeiro).
PREFERENCIA_SEMENTES: tuple = ("MELON", "CARROT", "WHEAT")

# MELON so e plantado se o preco atual estiver acima desta fracao do preco-base.
PRECO_MIN_RELATIVO_MELAO: float = 0.60

# ============================================================
# COMPRA DE SEMENTES
# ============================================================
ESTOQUE_MAX_SEMENTES: int = 4
LOTE_COMPRA_SEMENTES: int = 2
CUSTO_SEMENTE_PADRAO: int = 20

# ============================================================
# VENDA (fracoes do preco-base)
# ============================================================
LIMIAR_PRECO_ALTO: float = 0.80
LOTE_PRECO_ALTO: int = 5
LIMIAR_PRECO_MEDIO: float = 0.50
LOTE_PRECO_MEDIO: int = 2

# Celeiro com mais itens que isso vende mesmo a preco baixo (capacidade = 100).
LIMITE_PRESSAO_CELEIRO: int = 80
LOTE_PRESSAO_CELEIRO: int = 2

# Liquidacao: no dia 28 vende em lotes para nao derrubar a curva;
# no ultimo dia vende tudo, ja que estoque no turno 720 vale $0.
DIA_INICIO_LIQUIDACAO: int = 28
LOTE_LIQUIDACAO_GRADUAL: int = 5

# ============================================================
# FRONT-RUNNING (antecipar a colheita em massa do rival)
# ============================================================
LIMIAR_FRONT_RUNNING: float = 0.40
LOTE_FRONT_RUNNING: int = 5
# Quantas plantas quase maduras do rival disparam o alerta por cultura.
GATILHO_DUMP_RIVAL: dict = {"MELON": 1}
GATILHO_DUMP_RIVAL_PADRAO: int = 2

# ============================================================
# EPOCAS ESTRATEGICAS (balanced / protect / convert)
# ============================================================
TURNO_INICIO_EPOCAS: int = 432  # dia 18
DURACAO_EPOCA: int = 72  # 3 dias
DELTA_CAIXA_EPOCA: float = 1000.0
INDICE_Q_MAX_PROTECT: float = 0.78
INDICE_Q_MIN_CONVERT: float = 0.82
PRODUTOS_PREMIO: tuple = ("MELON", "STRAWBERRY", "WOOL")

LIMIAR_PROTECT: float = 0.90
LOTE_PROTECT: int = 1
LIMIAR_CONVERT: float = 0.40
LOTE_CONVERT: int = 10

# ============================================================
# AJUDANTES (hands)
# ============================================================
DIA_LIMITE_CONTRATACAO: int = 28
PLANTAS_PARA_SEGUNDO_AJUDANTE: int = 15

# ============================================================
# COLHEITA E TAREFAS
# ============================================================
MARGEM_SEGURA_CRESCIMENTO: int = 4
MARGEM_URGENTE_DECAIMENTO: int = 2
RENDIMENTO_MAXIMO_PADRAO: int = 4

PESOS_TAREFA_FAZENDEIRO: dict = {"harvest": 0, "water": 1, "dig": 1, "plant": 2}
PESOS_TAREFA_AJUDANTE: dict = {"harvest": 0, "water": 1, "dig": 2, "plant": 2}

# Ultimo dia: horarios para recolher todos ao celeiro e descarregar (DROP).
HORA_RETORNO_AJUDANTES: int = 12
HORA_RETORNO_FAZENDEIRO: int = 18

# ============================================================
# EXPANSAO DE TERRENO (BUY_LAND)
# ============================================================
COMPRAR_TERRENO: bool = False
DIA_MAX_COMPRA_TERRENO: int = 6
CUSTOS_TERRENO: tuple = (1000, 2000, 4000)
MAX_QUADRANTES_EXTRAS: int = 1
RESERVA_CAIXA_TERRENO: float = 500.0


# ======================================================================
# MODULO: src/kaggriculture_agent/dados.py
# ======================================================================
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

# ======================================================================
# MODULO: src/kaggriculture_agent/navegacao.py
# ======================================================================
"""
Navegacao no grid: movimento cardeal e distancias.

Convencao de coordenadas da engine: posicoes sao (x, y) e os tiles sao
acessados como `tiles[y][x]`. NORTH diminui y, SOUTH aumenta y.
"""


Posicao = tuple  # (x, y)


def calcular_distancia(x1: int, y1: int, x2: int, y2: int) -> int:
    """Distancia Manhattan, equivalente ao numero de turnos de movimento."""
    return abs(x1 - x2) + abs(y1 - y2)


def passo_em_direcao(
    origem_x: int,
    origem_y: int,
    destino_x: int,
    destino_y: int,
    primeiro_eixo: str = "x",
) -> str | None:
    """
    Retorna o proximo movimento cardeal rumo ao destino.

    Args:
        origem_x, origem_y: Posicao atual do trabalhador.
        destino_x, destino_y: Posicao alvo.
        primeiro_eixo: "x" percorre o eixo horizontal antes do vertical; "y" o contrario.

    Returns:
        "EAST" | "WEST" | "SOUTH" | "NORTH", ou None se ja estiver no destino.
    """
    delta_x = destino_x - origem_x
    delta_y = destino_y - origem_y
    horizontal = "EAST" if delta_x > 0 else "WEST" if delta_x < 0 else None
    vertical = "SOUTH" if delta_y > 0 else "NORTH" if delta_y < 0 else None
    if primeiro_eixo == "x":
        return horizontal or vertical
    return vertical or horizontal


def celeiro_mais_proximo(x: int, y: int) -> Posicao:
    """Retorna o tile de acesso ao celeiro mais proximo de (x, y)."""
    return min(POSICOES_CELEIRO, key=lambda p: calcular_distancia(x, y, p[0], p[1]))


# ======================================================================
# MODULO: src/kaggriculture_agent/fazenda.py
# ======================================================================
"""
Leitura do estado da fazenda a partir da observacao (`obs`) da engine.

Funcoes puras, sem efeitos colaterais, reutilizadas por estrategia, mercado e alvos.
"""


def fazenda_do_jogador(obs: dict, jogador: int | None = None) -> dict:
    """Retorna o dicionario da fazenda do jogador (padrao: o proprio agente)."""
    indice = obs["player"] if jogador is None else jogador
    return obs["farms"][indice]


def indice_rival(obs: dict) -> int:
    """Indice do oponente; em partidas solo retorna o proprio jogador."""
    jogador = obs["player"]
    return 1 - jogador if len(obs["farms"]) > 1 else jogador


def eh_planta(tile: object) -> bool:
    """Indica se o tile contem uma planta."""
    return isinstance(tile, dict) and tile.get("kind") == "PLANT"


def contar_plantas(fazenda: dict) -> int:
    """Numero de plantas ativas no tabuleiro da fazenda."""
    return sum(1 for linha in fazenda["tiles"] for tile in linha if eh_planta(tile))


def contar_tiles_cultivaveis(fazenda: dict) -> int:
    """
    Tiles desbloqueados que podem receber plantas: vazios, plantas e ervas daninhas.

    Exclui tiles "LOCKED" e estruturas (COOP/PASTURE), de modo que a capacidade
    cresce automaticamente apos um BUY_LAND.
    """
    total = 0
    for linha in fazenda["tiles"]:
        for tile in linha:
            if tile is None:
                total += 1
            elif isinstance(tile, dict) and tile.get("kind") in ("PLANT", "WEED"):
                total += 1
    return total


def total_itens(inventario: dict) -> int:
    """Soma das quantidades de um inventario {item: quantidade}."""
    return sum(inventario.values())


def dias_restantes(obs: dict, ultimo_dia: int = 29) -> int:
    """Dias completos restantes ate o fim da temporada."""
    return ultimo_dia - obs["day"]


# ======================================================================
# MODULO: src/kaggriculture_agent/estrategia.py
# ======================================================================
"""
Estrategia de alto nivel: modos de epoca e selecao de culturas.

Modos de epoca (avaliados a cada 72 turnos a partir do dia 18):
    - balanced: venda guiada apenas pelo preco.
    - protect:  lider com folga de caixa e mercado premium fraco -> vende pouco e caro.
    - convert:  atras no caixa e mercado premium forte -> converte estoque em dinheiro.
"""


MODO_PADRAO = "balanced"

# Estado da epoca indexado por jogador: evita que dois agentes do mesmo
# modulo (self-play local) compartilhem a decisao um do outro.
ESTADO_EPOCAS: dict = {}


def calcular_sinais_economicos(obs: dict) -> tuple:
    """
    Calcula os sinais que definem o modo de epoca.

    Returns:
        (delta_c, q, delta_k), onde
        - delta_c: caixa proprio menos caixa do rival;
        - q: preco medio relativo (preco atual / base) dos produtos premium;
        - delta_k: capacidade produtiva do rival menos a propria
          (plantas no campo, mais itens carregados pelo fazendeiro no caso proprio).
    """
    propria = fazenda_do_jogador(obs)
    rival = fazenda_do_jogador(obs, indice_rival(obs))
    delta_c = propria.get("money", 0) - rival.get("money", 0)

    precos = obs.get("market", {}).get("prices", {})
    razoes = []
    for produto in PRODUTOS_PREMIO:
        base = get_product_base_price(produto) or 1
        razoes.append(precos.get(produto, base) / base)
    q = sum(razoes) / len(razoes)

    k_proprio = contar_plantas(propria) + total_itens(obs["private"]["inventories"][0])
    delta_k = contar_plantas(rival) - k_proprio
    return delta_c, q, delta_k


def classificar_modo(delta_c: float, q: float, delta_k: int, celeiro_pressionado: bool) -> str:
    """Regra de decisao do modo de epoca a partir dos sinais economicos."""
    if (
        delta_c >= DELTA_CAIXA_EPOCA
        and q <= INDICE_Q_MAX_PROTECT
        and not celeiro_pressionado
        and delta_k <= 0
    ):
        return "protect"
    if delta_c <= -DELTA_CAIXA_EPOCA and q >= INDICE_Q_MIN_CONVERT and delta_k >= 0:
        return "convert"
    return MODO_PADRAO


def atualizar_modo_epoca(obs: dict) -> str:
    """Retorna o modo vigente, recalculando-o apenas na virada de cada epoca."""
    jogador = obs["player"]
    step = obs["step"]
    estado = ESTADO_EPOCAS.setdefault(jogador, {"turno_decisao": -1, "modo": MODO_PADRAO})

    if step < TURNO_INICIO_EPOCAS:
        estado["turno_decisao"] = -1
        estado["modo"] = MODO_PADRAO
        return MODO_PADRAO

    inicio_epoca = TURNO_INICIO_EPOCAS + DURACAO_EPOCA * ((step - TURNO_INICIO_EPOCAS) // DURACAO_EPOCA)
    if inicio_epoca != estado["turno_decisao"]:
        delta_c, q, delta_k = calcular_sinais_economicos(obs)
        pressionado = total_itens(obs["private"]["shed"]) > LIMITE_PRESSAO_CELEIRO
        estado["modo"] = classificar_modo(delta_c, q, delta_k, pressionado)
        estado["turno_decisao"] = inicio_epoca
    return estado["modo"]


def cultura_viavel(cultura: str, dias: int) -> bool:
    """Indica se uma semente plantada agora ainda amadurece antes do fim da temporada."""
    minimo = DIAS_MINIMOS_CULTURA.get(cultura)
    return minimo is not None and dias >= minimo


def escolher_cultura(obs: dict) -> str | None:
    """
    Escolhe a cultura a comprar/plantar com base no tempo restante e no preco.

    MELON (maior receita por tile) quando ha tempo e o preco esta saudavel;
    CARROT (ciclo curto) como padrao; WHEAT como ultima janela; None no fim.
    """
    dias = dias_restantes(obs, ULTIMO_DIA)
    precos = obs.get("market", {}).get("prices", {})

    if cultura_viavel("MELON", dias):
        base_melao = get_product_base_price("MELON")
        if precos.get("MELON", base_melao) >= base_melao * PRECO_MIN_RELATIVO_MELAO:
            return "MELON"
    if cultura_viavel("CARROT", dias):
        return "CARROT"
    if cultura_viavel("WHEAT", dias):
        return "WHEAT"
    return None


def escolher_semente_para_plantar(obs: dict, cultura_preferida: str | None) -> str | None:
    """
    Define qual semente do estoque sera plantada neste turno.

    Prioriza a cultura escolhida para o momento; se nao houver semente dela,
    reaproveita sementes ja compradas de outra cultura ainda viavel, evitando
    que o investimento em sementes termine a temporada sem retorno.
    """
    sementes = obs["private"]["seeds"]
    dias = dias_restantes(obs, ULTIMO_DIA)

    if cultura_preferida and sementes.get(cultura_preferida, 0) > 0:
        return cultura_preferida
    for cultura in PREFERENCIA_SEMENTES:
        if sementes.get(cultura, 0) > 0 and cultura_viavel(cultura, dias):
            return cultura
    return None


# ======================================================================
# MODULO: src/kaggriculture_agent/mercado.py
# ======================================================================
"""
Gestao de ordens de mercado: compras, contratacoes, front-running e vendas.

Resolve o bug critico das versoes anteriores: no final da temporada (dias 28 e 29),
a liquidacao do celeiro e executada PRIORITARIAMENTE, antes de qualquer restricao
dos modos 'protect' ou 'convert'. Itens no celeiro no turno 720 valem $0.
"""



def estimar_risco_dump_rival(obs: dict) -> Set[str]:
    """
    Identifica quais produtos o rival esta prestes a colher em massa.

    Monitora os tiles da fazenda adversaria em busca de lavouras quase maduras.
    Se o rival estiver prestes a colher, ele inundara o mercado logo em seguida,
    derrubando os precos na curva de excesso de oferta.
    """
    fazenda_rival = fazenda_do_jogador(obs, indice_rival(obs))
    contagem_quase_maduras: dict = {}

    for linha in fazenda_rival["tiles"]:
        for tile in linha:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                cultura = tile.get("crop")
                rendimento = tile.get("yield_units", 0)
                try:
                    info = get_crop(cultura)
                    rendimento_alvo = info.get(
                        "max_yield_unfertilized",
                        info.get("max_yield", RENDIMENTO_MAXIMO_PADRAO),
                    ) - 1
                except (KeyError, AttributeError):
                    rendimento_alvo = 3

                if rendimento >= max(2, rendimento_alvo):
                    contagem_quase_maduras[cultura] = contagem_quase_maduras.get(cultura, 0) + 1

    produtos_em_risco = set()
    for crop, qtd in contagem_quase_maduras.items():
        gatilho = GATILHO_DUMP_RIVAL.get(crop, GATILHO_DUMP_RIVAL_PADRAO)
        if qtd >= gatilho:
            produtos_em_risco.add(crop)

    return produtos_em_risco


def calcular_lote_venda(
    produto: str,
    quantidade: int,
    preco_atual: float,
    preco_base: float,
    dia: int,
    modo_atual: str,
    produtos_em_risco: Set[str],
    total_no_celeiro: int,
) -> int:
    """
    Determina o tamanho do lote de venda para um produto especifico.

    Retorna 0 se o produto nao deve ser vendido no turno corrente.
    """
    # 1. LIQUIDACAO FINAL (dias 28 e 29) - PREVALECE SOBRE QUALQUER MODO
    if dia == ULTIMO_DIA:
        # No ultimo dia, desova total imediata para nao perder valor
        return min(quantidade, MAX_ORDENS_MERCADO)
    if dia >= DIA_INICIO_LIQUIDACAO:
        # No dia 28, liquidacao progressiva para manter preco aceitavel
        return min(quantidade, LOTE_LIQUIDACAO_GRADUAL)

    # 2. FRONT-RUNNING: Rival esta prestes a inundar o mercado
    if produto in produtos_em_risco and preco_atual >= preco_base * LIMIAR_FRONT_RUNNING:
        return min(quantidade, LOTE_FRONT_RUNNING)

    # 3. MODO DE EPOCA: PROTECT (Lider protegendo precos do mercado)
    if modo_atual == "protect":
        if preco_atual >= preco_base * LIMIAR_PROTECT:
            return min(quantidade, LOTE_PROTECT)
        return 0

    # 4. MODO DE EPOCA: CONVERT (Atrasado no placar, gerando caixa agressivo)
    if modo_atual == "convert":
        if preco_atual >= preco_base * LIMIAR_CONVERT:
            return min(quantidade, LOTE_CONVERT)
        return 0

    # 5. MODO PADRAO (BALANCED): Regras economicas graduadas por patamar de preco
    if preco_atual >= preco_base * LIMIAR_PRECO_ALTO:
        return min(quantidade, LOTE_PRECO_ALTO)
    if preco_atual >= preco_base * LIMIAR_PRECO_MEDIO:
        return min(quantidade, LOTE_PRECO_MEDIO)
    if total_no_celeiro >= LIMITE_PRESSAO_CELEIRO:
        # Celeiro perto da capacidade maxima (100) ameaca bloquear colheitas
        return min(quantidade, LOTE_PRESSAO_CELEIRO)

    return 0


def gerar_acoes_venda(obs: dict, modo_atual: str) -> List[list]:
    """Gera a lista de ordens de venda do celeiro para o turno atual."""
    celeiro = obs["private"]["shed"]
    precos_mercado = obs.get("market", {}).get("prices", {})
    dia = obs["day"]
    produtos_em_risco = estimar_risco_dump_rival(obs)
    total_no_celeiro = total_itens(celeiro)

    acoes_venda = []
    ordens_usadas = 0

    for produto, quantidade in celeiro.items():
        if quantidade <= 0 or ordens_usadas >= MAX_ORDENS_MERCADO:
            continue

        try:
            preco_base = get_product_base_price(produto)
        except (KeyError, AttributeError):
            preco_base = 0.0

        if preco_base <= 0:
            continue

        preco_atual = precos_mercado.get(produto, preco_base)
        qtd_venda = calcular_lote_venda(
            produto=produto,
            quantidade=quantidade,
            preco_atual=preco_atual,
            preco_base=preco_base,
            dia=dia,
            modo_atual=modo_atual,
            produtos_em_risco=produtos_em_risco,
            total_no_celeiro=total_no_celeiro,
        )

        if qtd_venda > 0:
            qtd_venda = min(qtd_venda, MAX_ORDENS_MERCADO - ordens_usadas)
            acoes_venda.append(["SELL", produto, qtd_venda])
            ordens_usadas += 1

    return acoes_venda


def gerar_acoes_contratacao(obs: dict) -> List[list]:
    """Gera ordens de contratacao de ajudantes (HIRE) no primeiro turno de cada dia."""
    fazenda = fazenda_do_jogador(obs)
    dia = obs["day"]
    hora = obs["hour"]

    if hora != 0 or dia >= DIA_LIMITE_CONTRATACAO:
        return []

    plantas_ativas = contar_plantas(fazenda)
    contratacoes_hoje = fazenda.get("hires_today", 0)
    ajudantes_desejados = 2 if (plantas_ativas > PLANTAS_PARA_SEGUNDO_AJUDANTE or dia > 1) else 1

    precisa_contratar = max(0, ajudantes_desejados - contratacoes_hoje)
    return [["HIRE"] for _ in range(precisa_contratar)]


def gerar_acoes_compra_sementes(obs: dict, cultura_escolhida: str | None) -> List[list]:
    """
    Gera ordens de compra de sementes (BUY_SEED).

    Bloqueia novas compras a partir do dia 28 para evitar desperdicio de caixa
    com sementes que nao terao tempo habil de amadurecer.
    """
    if cultura_escolhida is None:
        return []

    dia = obs["day"]
    if dia >= DIA_INICIO_LIQUIDACAO:
        return []

    fazenda = fazenda_do_jogador(obs)
    privado = obs["private"]

    try:
        custo_semente = get_crop(cultura_escolhida)["seed_cost"]
    except (KeyError, AttributeError):
        custo_semente = CUSTO_SEMENTE_PADRAO

    sementes_disponiveis = privado["seeds"].get(cultura_escolhida, 0)
    total_todas_sementes = total_itens(privado["seeds"])
    plantas_ativas = contar_plantas(fazenda)
    capacidade_terreno = contar_tiles_cultivaveis(fazenda)

    if (
        plantas_ativas + total_todas_sementes < capacidade_terreno
        and sementes_disponiveis < ESTOQUE_MAX_SEMENTES
        and fazenda["money"] >= custo_semente
    ):
        quantidade_compra = min(LOTE_COMPRA_SEMENTES, ESTOQUE_MAX_SEMENTES - sementes_disponiveis)
        return [["BUY_SEED", cultura_escolhida, quantidade_compra]]

    return []


def gerar_acoes_mercado(obs: dict, cultura_escolhida: str | None, modo_atual: str) -> List[list]:
    """Orquestra todas as ordens de mercado do turno corrente (limite de 10 ordens)."""
    acoes = []
    acoes.extend(gerar_acoes_contratacao(obs))
    acoes.extend(gerar_acoes_compra_sementes(obs, cultura_escolhida))
    acoes.extend(gerar_acoes_venda(obs, modo_atual))
    return acoes[:MAX_ORDENS_MERCADO]


# ======================================================================
# MODULO: src/kaggriculture_agent/alvos.py
# ======================================================================
"""
Selecao e priorizacao de tarefas espaciais para fazendeiro e ajudantes.

Tarefas possiveis por tile:
    - harvest: colher planta madura ou prestes a apodrecer;
    - water:   irrigar plantas secas ou em janela de bonus;
    - dig:     capinar erva daninha (WEED) para liberar o terreno;
    - plant:   plantar semente viavel no solo desocupado;
    - drop:    descarregar produtos colhidos no celeiro central.
"""


# Estrutura do alvo: (x, y, tipo_tarefa, [urgencia_colheita])
Alvo = Tuple


def obter_prioridade_colheita(
    obs: dict,
    tile: dict,
    tile_x: int,
    tile_y: int,
    trabalhador_x: int,
    trabalhador_y: int,
) -> Optional[int]:
    """
    Avalia se uma planta deve ser colhida neste turno ou se deve aguardar maturar mais.

    Returns:
        0: urgente / madura;
        1: na iminencia de decaimento;
        None: deve continuar crescendo com seguranca.
    """
    if tile is None or tile.get("kind") != "PLANT":
        return None

    unidades = tile.get("yield_units", 0)
    if unidades <= 0:
        return None

    cultura = tile.get("crop")
    try:
        info = get_crop(cultura)
        rendimento_maximo = info.get(
            "max_yield_unfertilized",
            info.get("max_yield", RENDIMENTO_MAXIMO_PADRAO),
        )
    except (KeyError, AttributeError):
        rendimento_maximo = RENDIMENTO_MAXIMO_PADRAO

    passo_decaimento = tile.get("max_lifespan_step", obs["step"] + 999) - obs["step"]
    distancia = calcular_distancia(tile_x, tile_y, trabalhador_x, trabalhador_y)
    margem_tempo = passo_decaimento - distancia

    if unidades >= rendimento_maximo:
        return 0

    if unidades >= rendimento_maximo - 1:
        if margem_tempo > MARGEM_SEGURA_CRESCIMENTO:
            return None
        return 0

    if margem_tempo <= MARGEM_URGENTE_DECAIMENTO:
        return 1

    return None


def precisa_irrigacao(obs: dict, tile: dict) -> bool:
    """Verifica se a planta deve ser regada hoje."""
    if tile.get("watered_today", False):
        return False
    if tile.get("consecutive_unwatered", 0) >= 1:
        return True

    cultura = tile.get("crop")
    janela = BONUS_WINDOWS.get(cultura)
    if janela:
        idade = obs["day"] - tile.get("planted_day", 0)
        if janela[0] <= idade < janela[1]:
            return True
    return False


def encontrar_alvo_fazendeiro(
    obs: dict,
    tem_semente: bool,
    cultura_para_plantar: Optional[str],
) -> Optional[tuple]:
    """Encontra a melhor tarefa disponivel para o fazendeiro principal."""
    fazenda = fazenda_do_jogador(obs)
    fx, fy = fazenda["farmer"]
    candidatos = []

    for y, linha in enumerate(fazenda["tiles"]):
        for x, tile in enumerate(linha):
            if tile is None:
                if tem_semente and cultura_para_plantar is not None:
                    candidatos.append((x, y, "plant", 999))
                continue

            if not isinstance(tile, dict):
                continue

            tipo = tile.get("kind")
            if tipo == "WEED":
                candidatos.append((x, y, "dig", 999))
                continue

            if tipo == "PLANT":
                prio_colheita = obter_prioridade_colheita(obs, tile, x, y, fx, fy)
                if prio_colheita is not None:
                    candidatos.append((x, y, "harvest", prio_colheita))
                elif precisa_irrigacao(obs, tile):
                    candidatos.append((x, y, "water", 999))

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda c: (
            PESOS_TAREFA_FAZENDEIRO.get(c[2], 9),
            c[3],
            calcular_distancia(c[0], c[1], fx, fy),
        )
    )
    return candidatos[0][:3]


def encontrar_alvo_ajudante(
    obs: dict,
    indice_ajudante: int,
    tem_semente: bool,
    cultura_para_plantar: Optional[str],
    alvos_excluidos: Optional[Set[Tuple[int, int]]] = None,
) -> Optional[tuple]:
    """Encontra a melhor tarefa para um ajudante especifico, evitando alvos ja ocupados."""
    if alvos_excluidos is None:
        alvos_excluidos = set()

    fazenda = fazenda_do_jogador(obs)
    hx, hy = fazenda["hands"][indice_ajudante]
    candidatos = []

    for y, linha in enumerate(fazenda["tiles"]):
        for x, tile in enumerate(linha):
            if (x, y) in alvos_excluidos:
                continue

            if tile is None:
                if tem_semente and cultura_para_plantar is not None:
                    candidatos.append((x, y, "plant", 999))
                continue

            if not isinstance(tile, dict):
                continue

            tipo = tile.get("kind")
            if tipo == "WEED":
                candidatos.append((x, y, "dig", 999))
                continue

            if tipo == "PLANT":
                # Irrigacao e prioritaria para ajudantes liberando o fazendeiro
                if precisa_irrigacao(obs, tile):
                    candidatos.append((x, y, "water", 999))
                else:
                    prio_colheita = obter_prioridade_colheita(obs, tile, x, y, hx, hy)
                    if prio_colheita is not None:
                        candidatos.append((x, y, "harvest", prio_colheita))

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda c: (
            PESOS_TAREFA_AJUDANTE.get(c[2], 9),
            c[3],
            calcular_distancia(c[0], c[1], hx, hy),
        )
    )
    return candidatos[0][:3]


def encontrar_alvo_colheita_final(obs: dict) -> Optional[tuple]:
    """Varredura de emergencia para o dia final: colhe qualquer planta com rendimento positivo."""
    fazenda = fazenda_do_jogador(obs)
    fx, fy = fazenda["farmer"]
    candidatos = []

    for y, linha in enumerate(fazenda["tiles"]):
        for x, tile in enumerate(linha):
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                if tile.get("yield_units", 0) > 0:
                    dist = calcular_distancia(x, y, fx, fy)
                    candidatos.append((x, y, "harvest", dist))

    if not candidatos:
        return None

    candidatos.sort(key=lambda c: c[3])
    return candidatos[0][:3]


def gerar_acao_para_alvo(
    posicao_x: int,
    posicao_y: int,
    alvo: Optional[tuple],
    cultura_para_plantar: Optional[str],
) -> List[str]:
    """Converte a posicao e a tupla do alvo em comando compativel com a engine."""
    if alvo is None:
        return ["PASS"]

    destino_x, destino_y, objetivo = alvo[:3]
    movimento = passo_em_direcao(posicao_x, posicao_y, destino_x, destino_y)
    if movimento is not None:
        return [movimento]

    if objetivo == "plant" and cultura_para_plantar is not None:
        return ["PLANT", cultura_para_plantar]
    if objetivo == "water":
        return ["WATER"]
    if objetivo == "harvest":
        return ["HARVEST"]
    if objetivo == "dig":
        return ["DIG"]
    if objetivo == "drop":
        return ["DROP"]

    return ["PASS"]


# ======================================================================
# MODULO: src/kaggriculture_agent/agente.py
# ======================================================================
"""
Ponto de entrada do agente Kaggriculture.

Orquestra a arquitetura modular:
    1. Estrategia macro: modos de epoca e selecao de culturas;
    2. Gestao de mercado: contratacoes, sementes e vendas conscientes de preco;
    3. Alocacao de alvos: coordenacao espacial entre fazendeiro e ajudantes;
    4. End-game: recolhimento ao celeiro e desova total de estoque nos dias finais.
"""



def agent(obs: dict) -> Dict[str, list]:
    """
    Funcao principal invocada a cada turno pela engine de simulacao do Kaggle.

    Args:
        obs: Dicionario de observacao global do turno corrente.

    Returns:
        Dicionario contendo as acoes para o fazendeiro, ajudantes e ordens de mercado:
        {"farmer": [...], "hands": [...], "market": [...]}
    """
    dia = obs["day"]
    hora = obs["hour"]
    fazenda = fazenda_do_jogador(obs)
    privado = obs["private"]

    fx, fy = fazenda["farmer"]
    ajudantes = fazenda["hands"]
    plantas_ativas = contar_plantas(fazenda)

    # 1. Estrategia macro e selecao de culturas
    modo_atual = atualizar_modo_epoca(obs)
    cultura_escolhida = escolher_cultura(obs)
    cultura_para_plantar = escolher_semente_para_plantar(obs, cultura_escolhida)
    tem_semente = cultura_para_plantar is not None

    # 2. Ordens de mercado (vendas, compras e contratacoes)
    acoes_mercado = gerar_acoes_mercado(obs, cultura_escolhida, modo_atual)

    # 3. Definicao de alvo para o fazendeiro principal
    if dia >= ULTIMO_DIA and plantas_ativas > 0:
        alvo_fazendeiro = encontrar_alvo_colheita_final(obs)
    else:
        alvo_fazendeiro = encontrar_alvo_fazendeiro(obs, tem_semente, cultura_para_plantar)

    alvos_reservados = set()
    if alvo_fazendeiro is not None:
        alvos_reservados.add((alvo_fazendeiro[0], alvo_fazendeiro[1]))

    # Verifica se o fazendeiro vai consumir uma semente neste turno
    fazendeiro_vai_plantar = (
        alvo_fazendeiro is not None
        and alvo_fazendeiro[2] == "plant"
        and passo_em_direcao(fx, fy, alvo_fazendeiro[0], alvo_fazendeiro[1]) is None
    )

    # Quantidade de sementes disponiveis para ajudantes apos reserva do fazendeiro
    qtd_semente_atual = privado["seeds"].get(cultura_para_plantar, 0) if cultura_para_plantar else 0
    sementes_ajudantes_restantes = max(0, qtd_semente_atual - (1 if fazendeiro_vai_plantar else 0))

    # 4. Definicao de acoes para os ajudantes (hands)
    acoes_ajudantes: List[list] = []
    for idx, (hx, hy) in enumerate(ajudantes):
        inventario_ajudante = privado["inventories"][idx + 1]
        itens_ajudante = total_itens(inventario_ajudante)

        # Fim de jogo: descarregar tudo no celeiro a partir do meio do ultimo dia
        if dia == ULTIMO_DIA and hora >= HORA_RETORNO_AJUDANTES and itens_ajudante > 0:
            cx, cy = celeiro_mais_proximo(hx, hy)
            acao_hand = gerar_acao_para_alvo(hx, hy, (cx, cy, "drop"), cultura_para_plantar)
        else:
            pode_plantar = sementes_ajudantes_restantes > 0
            alvo_hand = encontrar_alvo_ajudante(
                obs=obs,
                indice_ajudante=idx,
                tem_semente=pode_plantar,
                cultura_para_plantar=cultura_para_plantar,
                alvos_excluidos=alvos_reservados,
            )

            if alvo_hand is None:
                acao_hand = ["PASS"]
            else:
                destino_x, destino_y, objetivo = alvo_hand[:3]
                alvos_reservados.add((destino_x, destino_y))
                acao_hand = gerar_acao_para_alvo(hx, hy, alvo_hand, cultura_para_plantar)
                if acao_hand[0] == "PLANT":
                    sementes_ajudantes_restantes -= 1

        acoes_ajudantes.append(acao_hand)

    # 5. Fim de jogo: retorno e descarregamento do fazendeiro no celeiro
    itens_fazendeiro = total_itens(privado["inventories"][0])
    if dia == ULTIMO_DIA and hora >= HORA_RETORNO_FAZENDEIRO:
        if itens_fazendeiro > 0 and plantas_ativas == 0:
            if (fx, fy) in POSICOES_CELEIRO:
                return {"farmer": ["DROP"], "hands": acoes_ajudantes, "market": acoes_mercado}
            cx, cy = celeiro_mais_proximo(fx, fy)
            mov = passo_em_direcao(fx, fy, cx, cy, primeiro_eixo="y")
            if mov is not None:
                return {"farmer": [mov], "hands": acoes_ajudantes, "market": acoes_mercado}

    # Turno 0: movimento inicial norte para liberar area
    if dia == 0 and hora == 0:
        return {"farmer": ["NORTH"], "hands": [], "market": acoes_mercado}

    # 6. Execucao da acao do fazendeiro
    if alvo_fazendeiro is not None:
        acao_fazendeiro = gerar_acao_para_alvo(fx, fy, alvo_fazendeiro, cultura_para_plantar)
        return {"farmer": acao_fazendeiro, "hands": acoes_ajudantes, "market": acoes_mercado}

    return {"farmer": ["PASS"], "hands": acoes_ajudantes, "market": acoes_mercado}

