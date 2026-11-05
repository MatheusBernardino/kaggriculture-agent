"""
Ponto de entrada do agente Kaggriculture.

Orquestra a arquitetura modular:
    1. Estrategia macro: modos de epoca e selecao de culturas;
    2. Gestao de mercado: contratacoes, sementes e vendas conscientes de preco;
    3. Alocacao de alvos: coordenacao espacial entre fazendeiro e ajudantes;
    4. End-game: recolhimento ao celeiro e desova total de estoque nos dias finais.
"""

from typing import Dict, List
from .alvos import (
    encontrar_alvo_ajudante,
    encontrar_alvo_colheita_final,
    encontrar_alvo_fazendeiro,
    gerar_acao_para_alvo,
)
from .config import (
    HORA_RETORNO_AJUDANTES,
    HORA_RETORNO_FAZENDEIRO,
    POSICOES_CELEIRO,
    ULTIMO_DIA,
)
from .estrategia import atualizar_modo_epoca, escolher_cultura, escolher_semente_para_plantar
from .fazenda import contar_plantas, fazenda_do_jogador, total_itens
from .mercado import gerar_acoes_mercado
from .navegacao import celeiro_mais_proximo, passo_em_direcao


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

