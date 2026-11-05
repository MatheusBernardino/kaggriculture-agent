"""
Estrategia de alto nivel: modos de epoca e selecao de culturas.

Modos de epoca (avaliados a cada 72 turnos a partir do dia 18):
    - balanced: venda guiada apenas pelo preco.
    - protect:  lider com folga de caixa e mercado premium fraco -> vende pouco e caro.
    - convert:  atras no caixa e mercado premium forte -> converte estoque em dinheiro.
"""

from .config import (
    DELTA_CAIXA_EPOCA,
    DIAS_MINIMOS_CULTURA,
    DURACAO_EPOCA,
    INDICE_Q_MAX_PROTECT,
    INDICE_Q_MIN_CONVERT,
    LIMITE_PRESSAO_CELEIRO,
    PRECO_MIN_RELATIVO_MELAO,
    PREFERENCIA_SEMENTES,
    PRODUTOS_PREMIO,
    TURNO_INICIO_EPOCAS,
    ULTIMO_DIA,
)
from .dados import get_product_base_price
from .fazenda import contar_plantas, dias_restantes, fazenda_do_jogador, indice_rival, total_itens

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

