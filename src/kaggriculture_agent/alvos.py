"""
Selecao e priorizacao de tarefas espaciais para fazendeiro e ajudantes.

Tarefas possiveis por tile:
    - harvest: colher planta madura ou prestes a apodrecer;
    - water:   irrigar plantas secas ou em janela de bonus;
    - dig:     capinar erva daninha (WEED) para liberar o terreno;
    - plant:   plantar semente viavel no solo desocupado;
    - drop:    descarregar produtos colhidos no celeiro central.
"""

from typing import List, Optional, Set, Tuple
from .config import (
    MARGEM_SEGURA_CRESCIMENTO,
    MARGEM_URGENTE_DECAIMENTO,
    PESOS_TAREFA_AJUDANTE,
    PESOS_TAREFA_FAZENDEIRO,
    RENDIMENTO_MAXIMO_PADRAO,
)
from .dados import BONUS_WINDOWS, get_crop
from .fazenda import fazenda_do_jogador
from .navegacao import calcular_distancia, passo_em_direcao

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
