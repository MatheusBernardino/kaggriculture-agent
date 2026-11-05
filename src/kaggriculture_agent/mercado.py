"""
Gestao de ordens de mercado: compras, contratacoes, front-running e vendas.

Resolve o bug critico das versoes anteriores: no final da temporada (dias 28 e 29),
a liquidacao do celeiro e executada PRIORITARIAMENTE, antes de qualquer restricao
dos modos 'protect' ou 'convert'. Itens no celeiro no turno 720 valem $0.
"""

from typing import List, Set
from .config import (
    CUSTO_SEMENTE_PADRAO,
    DIA_INICIO_LIQUIDACAO,
    DIA_LIMITE_CONTRATACAO,
    ESTOQUE_MAX_SEMENTES,
    GATILHO_DUMP_RIVAL,
    GATILHO_DUMP_RIVAL_PADRAO,
    LIMIAR_CONVERT,
    LIMIAR_FRONT_RUNNING,
    LIMIAR_PRECO_ALTO,
    LIMIAR_PRECO_MEDIO,
    LIMIAR_PROTECT,
    LIMITE_PRESSAO_CELEIRO,
    LOTE_COMPRA_SEMENTES,
    LOTE_CONVERT,
    LOTE_FRONT_RUNNING,
    LOTE_LIQUIDACAO_GRADUAL,
    LOTE_PRECO_ALTO,
    LOTE_PRECO_MEDIO,
    LOTE_PRESSAO_CELEIRO,
    LOTE_PROTECT,
    MAX_ORDENS_MERCADO,
    PLANTAS_PARA_SEGUNDO_AJUDANTE,
    RENDIMENTO_MAXIMO_PADRAO,
    ULTIMO_DIA,
)
from .dados import get_crop, get_product_base_price
from .fazenda import (
    contar_plantas,
    contar_tiles_cultivaveis,
    fazenda_do_jogador,
    indice_rival,
    total_itens,
)


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
