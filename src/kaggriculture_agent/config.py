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

