"""
Agente Kaggriculture V4 — Seleção Dinâmica de Culturas + Estratégia de Mercado.

Refatorado para consumir diretamente os dados e parâmetros de `data.py`.
Nomes de variáveis, métodos e comentários em português, mantendo
a interface e contratos esperados pela engine do Kaggle.

Ponto de entrada esperado: agent(obs)
"""

try:
    from data import CROPS, MARKET_PARAMS, get_crop, get_product_base_price, BONUS_WINDOWS
except ImportError:
    # Fallback caso seja executado dentro de subpacote
    from .data import CROPS, MARKET_PARAMS, get_crop, get_product_base_price, BONUS_WINDOWS

# ============================================================
# CONSTANTES GERAIS DA FAZENDA
# ============================================================

# Coordenadas do celeiro (shed) central no grid 10x10
POSICOES_CELEIRO = {(4, 4), (4, 5), (5, 4), (5, 5)}
MAX_PLANTAS = 25
MAX_SEMENTES = 4


# ============================================================
# SELEÇÃO DINÂMICA DE CULTURAS
# ============================================================

def escolher_cultura(obs):
    """
    Seleciona a melhor cultura para plantar no turno atual,
    levando em consideração os dias restantes da temporada e o preço no mercado.
    """
    dias_restantes = 29 - obs["day"]
    precos_mercado = obs.get("market", {}).get("prices", {})

    # Fase 1: tempo suficiente para o MELON (precisa de pelo menos 11 dias)
    if dias_restantes >= 12:
        preco_base_melao = get_product_base_price("MELON")
        preco_atual_melao = precos_mercado.get("MELON", preco_base_melao)
        # Só planta melão se o preço atual estiver saudável (>= 60% da base)
        if preco_atual_melao >= preco_base_melao * 0.60:
            return "MELON"
        # Se o preço do melão colapsou, faz fallback para CARROT

    # Fase 2: tempo suficiente para CARROT (ciclo de 4 dias)
    if dias_restantes >= 4:
        return "CARROT"

    # Fase 3: tempo apenas para WHEAT (primeiro rendimento aos 2 dias)
    if dias_restantes >= 3:
        return "WHEAT"

    # Menos de 3 dias restantes: não compensa semear nada novo
    return None


# ============================================================
# ESTRATÉGIA DE MERCADO (Venda consciente de preços)
# ============================================================

def obter_acoes_venda(obs):
    """
    Decide quais produtos e quais quantidades vender no turno atual.
    Evita vender em excesso de uma só vez para não derrubar as curvas de preço.
    """
    celeiro = obs["private"]["shed"]
    precos_mercado = obs.get("market", {}).get("prices", {})
    dia = obs["day"]
    acoes_venda = []

    for produto, quantidade in celeiro.items():
        if quantidade <= 0:
            continue

        try:
            preco_base = get_product_base_price(produto)
        except (KeyError, AttributeError):
            preco_base = 0

        if preco_base == 0:
            continue

        preco_atual = precos_mercado.get(produto, preco_base)

        # Fim de jogo (dias 28 e 29): liquidação total a qualquer preço
        if dia >= 28:
            quantidade_venda = min(quantidade, 5)
            acoes_venda.append(["SELL", produto, quantidade_venda])
            continue

        # Preço bom (>= 80% do preço-base): vende lote de até 5 unidades
        if preco_atual >= preco_base * 0.80:
            quantidade_venda = min(quantidade, 5)
            acoes_venda.append(["SELL", produto, quantidade_venda])
            continue

        # Preço aceitável (>= 50% do preço-base): vende lote pequeno (até 2 unidades)
        if preco_atual >= preco_base * 0.50:
            quantidade_venda = min(quantidade, 2)
            acoes_venda.append(["SELL", produto, quantidade_venda])
            continue

        # Preço muito baixo (< 50%): segura estoque, a menos que o celeiro esteja quase lotado
        total_no_celeiro = sum(celeiro.values())
        if total_no_celeiro >= 80:
            quantidade_venda = min(quantidade, 2)
            acoes_venda.append(["SELL", produto, quantidade_venda])

    return acoes_venda


# ============================================================
# MOVIMENTAÇÃO E NAVEGAÇÃO
# ============================================================

def passo_em_direcao(origem_x, origem_y, destino_x, destino_y, primeiro_eixo="x"):
    """
    Retorna a próxima ação de movimento cardeal para aproximar o trabalhador do destino.
    Retorna None se já estiver na posição de destino.
    """
    delta_x = destino_x - origem_x
    delta_y = destino_y - origem_y

    if primeiro_eixo == "x":
        if delta_x > 0:
            return "EAST"
        if delta_x < 0:
            return "WEST"
        if delta_y > 0:
            return "SOUTH"
        if delta_y < 0:
            return "NORTH"
    else:
        if delta_y > 0:
            return "SOUTH"
        if delta_y < 0:
            return "NORTH"
        if delta_x > 0:
            return "EAST"
        if delta_x < 0:
            return "WEST"

    return None


def calcular_distancia(x1, y1, x2, y2):
    """Calcula a distância Manhattan entre duas coordenadas."""
    return abs(x1 - x2) + abs(y1 - y2)


# ============================================================
# PRIORIDADE DE COLHEITA
# ============================================================

def obter_prioridade_colheita(obs, tile, tile_x, tile_y, trabalhador_x, trabalhador_y):
    """
    Avalia se uma planta deve ser colhida agora ou se deve continuar crescendo.
    Retorna um nível de prioridade (quanto menor, mais urgente) ou None para aguardar.
    """
    if tile is None or tile.get("kind") != "PLANT":
        return None

    nome_cultura = tile["crop"]
    unidades_rendimento = tile.get("yield_units", 0)

    if unidades_rendimento <= 0:
        return None

    try:
        info_cultura = get_crop(nome_cultura)
        rendimento_maximo = info_cultura.get(
            "max_yield_unfertilized",
            info_cultura.get("max_yield", 4)
        )
    except (KeyError, AttributeError):
        return 0

    passo_decaimento = tile.get("max_lifespan_step", obs["step"] + 999) - obs["step"]
    distancia_ate_planta = calcular_distancia(tile_x, tile_y, trabalhador_x, trabalhador_y)
    margem_tempo = passo_decaimento - distancia_ate_planta

    # Já atingiu o rendimento máximo da cultura sem fertilizante
    if unidades_rendimento >= rendimento_maximo:
        return 0

    # Falta apenas 1 unidade para atingir o máximo
    if unidades_rendimento >= rendimento_maximo - 1:
        if margem_tempo > 4:
            return None  # Ainda há tempo seguro para deixar crescer
        return 0

    # Rendimento baixo: só colhe se estiver na iminência de decair/apodrecer
    if margem_tempo <= 2:
        return 1

    return None


# ============================================================
# SELEÇÃO DE TAREFAS (Fazendeiro e Ajudantes)
# ============================================================

def encontrar_alvo_fazendeiro(obs, tem_semente, cultura_escolhida):
    """Encontra a tarefa de maior prioridade mais próxima para o fazendeiro principal."""
    jogador = obs["player"]
    fazenda = obs["farms"][jogador]
    fazendeiro_x, fazendeiro_y = fazenda["farmer"]
    candidatos = []

    for y, linha in enumerate(fazenda["tiles"]):
        for x, tile in enumerate(linha):
            # Tile vazio: oportunidade de plantio
            if tile is None:
                if tem_semente and cultura_escolhida is not None:
                    candidatos.append((x, y, "plant"))
                continue
            if not isinstance(tile, dict):
                continue

            tipo_tile = tile.get("kind")

            # Erva daninha (WEED): capinar
            if tipo_tile == "WEED":
                candidatos.append((x, y, "dig"))
                continue

            if tipo_tile != "PLANT":
                continue
            janela_bonus = BONUS_WINDOWS.get(tile.get("crop",0))
            # Avaliar necessidade de colheita
            prioridade_colheita = obter_prioridade_colheita(obs, tile, x, y, fazendeiro_x, fazendeiro_y)
            if prioridade_colheita is not None:
                candidatos.append((x, y, "harvest", prioridade_colheita))

            # Avaliar necessidade de irrigação
            if (((tile.get("consecutive_unwatered", 0) >= 1) or (obs["day"] - tile.get("planted_day",0)) in range(janela_bonus[0], janela_bonus[1]))
                and ( tile.get("watered_today",0) == False)):
                candidatos.append((x, y, "water"))

    if not candidatos:
        return None

    # Mapeamento de urgência das tarefas
    pesos_prioridade = {"harvest": 0, "water": 1, "dig": 1, "plant": 2}

    candidatos.sort(
        key=lambda c: (
            pesos_prioridade[c[2]],
            c[3] if c[2] == "harvest" else 999,
            calcular_distancia(c[0], c[1], fazendeiro_x, fazendeiro_y),
        )
    )

    return candidatos[0][:3]


def encontrar_alvo_ajudante(obs, indice_ajudante, tem_semente, cultura_escolhida, alvos_excluidos=None):
    """Encontra a melhor tarefa para um ajudante específico, evitando alvos já reservados."""
    if alvos_excluidos is None:
        alvos_excluidos = set()

    jogador = obs["player"]
    fazenda = obs["farms"][jogador]
    ajudante_x, ajudante_y = fazenda["hands"][indice_ajudante]
    candidatos = []

    for y, linha in enumerate(fazenda["tiles"]):
        for x, tile in enumerate(linha):
            if (x, y) in alvos_excluidos:
                continue

            if tile is None:
                if tem_semente and cultura_escolhida is not None:
                    candidatos.append((x, y, "plant"))
                continue
            if not isinstance(tile, dict):
                continue

            tipo_tile = tile.get("kind")

            if tipo_tile == "WEED":
                candidatos.append((x, y, "dig"))
                continue

            if tipo_tile != "PLANT":
                continue
            janela_bonus = BONUS_WINDOWS.get(tile.get("crop",0))
            # Irrigação para ajudante tem prioridade imediata
            if (((tile.get("consecutive_unwatered", 0) >= 1) or (obs["day"] - tile.get("planted_day",0)) in range(janela_bonus[0], janela_bonus[1]))
                and ( tile.get("watered_today",0) == False)):
                candidatos.append((x, y, "water"))

            prioridade_colheita = obter_prioridade_colheita(obs, tile, x, y, ajudante_x, ajudante_y)
            if prioridade_colheita is not None:
                candidatos.append((x, y, "harvest", prioridade_colheita))

    if not candidatos:
        return None

    pesos_prioridade = {"harvest": 0, "water": 1, "dig": 2, "plant": 2}

    candidatos.sort(
        key=lambda c: (
            pesos_prioridade[c[2]],
            c[3] if c[2] == "harvest" else 999,
            calcular_distancia(c[0], c[1], ajudante_x, ajudante_y),
        )
    )

    return candidatos[0]


def encontrar_alvo_colheita_final(obs):
    """Varredura de emergência para o dia 29: colhe qualquer planta com rendimento positivo."""
    jogador = obs["player"]
    fazenda = obs["farms"][jogador]
    fazendeiro_x, fazendeiro_y = fazenda["farmer"]
    candidatos = []

    for y, linha in enumerate(fazenda["tiles"]):
        for x, tile in enumerate(linha):
            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
                continue
            if tile.get("yield_units", 0) <= 0:
                continue

            dist = calcular_distancia(x, y, fazendeiro_x, fazendeiro_y)
            candidatos.append((x, y, "harvest", dist))

    if not candidatos:
        return None

    candidatos.sort(key=lambda c: c[3])
    return candidatos[0][:3]


# ============================================================
# CONVERSÃO DE ALVO EM AÇÃO
# ============================================================

def gerar_acao_para_alvo(posicao_x, posicao_y, alvo, cultura_escolhida):
    """Converte uma tupla de alvo (x, y, objetivo) na lista de comando aceita pela engine."""
    if alvo is None:
        return ["PASS"]

    destino_x, destino_y, objetivo = alvo[:3]
    movimento = passo_em_direcao(posicao_x, posicao_y, destino_x, destino_y)
    if movimento is not None:
        return [movimento]

    # Se já chegou na coordenada do alvo, realiza a ação devida
    if objetivo == "plant" and cultura_escolhida is not None:
        return ["PLANT", cultura_escolhida]
    if objetivo == "water":
        return ["WATER"]
    if objetivo == "harvest":
        return ["HARVEST"]
    if objetivo == "dig":
        return ["DIG"]
    if objetivo == "drop":
        return ["DROP"]

    return ["PASS"]


# ============================================================
# AGENTE PRINCIPAL (Entrada Kaggle)
# ============================================================

def agent(obs):
    """
    Função principal chamada a cada turno pela simulação da competição Kaggriculture.
    """
    jogador = obs["player"]
    fazenda = obs["farms"][jogador]
    privado = obs["private"]
    dia = obs["day"]
    hora = obs["hour"]

    fazendeiro_x, fazendeiro_y = fazenda["farmer"]
    ajudantes = fazenda["hands"]

    # 1. Seleção dinâmica da cultura para o momento
    cultura_escolhida = escolher_cultura(obs)

    custo_semente = 20
    if cultura_escolhida is not None:
        try:
            custo_semente = get_crop(cultura_escolhida)["seed_cost"]
        except (KeyError, AttributeError):
            custo_semente = 20

    sementes_disponiveis = privado["seeds"].get(cultura_escolhida, 0) if cultura_escolhida else 0
    inventario_fazendeiro = privado["inventories"][0]
    total_itens_fazendeiro = sum(inventario_fazendeiro.values())

    plantas_ativas = sum(
        1
        for linha in fazenda["tiles"]
        for tile in linha
        if isinstance(tile, dict) and tile.get("kind") == "PLANT"
    )

    # ---------------------------------------------------------
    # GESTÃO DE AÇÕES DE MERCADO
    # ---------------------------------------------------------
    acoes_mercado = []

    # Contratação diária de ajudantes (à meia-noite, até o dia 27)
    if hora == 0 and dia < 28:
        contratacoes_hoje = fazenda.get("hires_today", 0)
        ajudantes_desejados = 1
        # Contrata um ajudante extra em períodos com muitas plantas no campo
        if plantas_ativas > 15 or dia > 1:
            ajudantes_desejados = 2

        precisa_contratar = ajudantes_desejados - contratacoes_hoje
        for _ in range(max(0, precisa_contratar)):
            acoes_mercado.append(["HIRE"])

    # Compra de sementes para a cultura selecionada
    if cultura_escolhida is not None:
        total_todas_sementes = sum(privado["seeds"].values())
        if (
            plantas_ativas + total_todas_sementes < MAX_PLANTAS
            and sementes_disponiveis < MAX_SEMENTES
            and fazenda["money"] >= custo_semente
        ):
            quantidade_compra = min(2, MAX_SEMENTES - sementes_disponiveis)
            acoes_mercado.append(["BUY_SEED", cultura_escolhida, quantidade_compra])

    # Ações de venda com base nas cotações e regras de liquidação
    acoes_de_venda = obter_acoes_venda(obs)
    acoes_mercado.extend(acoes_de_venda)

    # ---------------------------------------------------------
    # DEFINIÇÃO DO ALVO DO FAZENDEIRO
    # ---------------------------------------------------------
    tem_semente = sementes_disponiveis > 0

    if dia >= 29 and plantas_ativas > 0:
        alvo_fazendeiro = encontrar_alvo_colheita_final(obs)
    else:
        alvo_fazendeiro = encontrar_alvo_fazendeiro(obs, tem_semente, cultura_escolhida)

    coordenada_alvo_fazendeiro = None
    if alvo_fazendeiro is not None:
        coordenada_alvo_fazendeiro = (alvo_fazendeiro[0], alvo_fazendeiro[1])

    # ---------------------------------------------------------
    # DEFINIÇÃO DOS ALVOS DOS AJUDANTES (Hands)
    # ---------------------------------------------------------
    acoes_ajudantes = []
    alvos_reservados = set()

    if coordenada_alvo_fazendeiro is not None:
        alvos_reservados.add(coordenada_alvo_fazendeiro)

    # Verifica se o fazendeiro já vai consumir uma semente neste turno
    fazendeiro_vai_plantar = (
        alvo_fazendeiro is not None
        and alvo_fazendeiro[2] == "plant"
        and passo_em_direcao(fazendeiro_x, fazendeiro_y, alvo_fazendeiro[0], alvo_fazendeiro[1]) is None
    )

    sementes_para_ajudantes = sementes_disponiveis
    if fazendeiro_vai_plantar:
        sementes_para_ajudantes -= 1

    for indice_ajudante, (hx, hy) in enumerate(ajudantes):
        inventario_ajudante = privado["inventories"][indice_ajudante + 1]
        total_itens_ajudante = sum(inventario_ajudante.values())

        # Se o ajudante coletou itens, prioriza descarregar no celeiro (DROP)
        if (dia == 29 and hora > 12) and total_itens_ajudante > 0:
            posicao_celeiro_proxima = min(
                POSICOES_CELEIRO,
                key=lambda p: calcular_distancia(hx, hy, p[0], p[1]),
            )
            acao_ajudante = gerar_acao_para_alvo(
                hx, hy, (posicao_celeiro_proxima[0], posicao_celeiro_proxima[1], "drop"), cultura_escolhida
            )
        else:
            alvo_ajudante = encontrar_alvo_ajudante(
                obs,
                indice_ajudante=indice_ajudante,
                tem_semente=sementes_para_ajudantes > 0,
                cultura_escolhida=cultura_escolhida,
                alvos_excluidos=alvos_reservados,
            )

            if alvo_ajudante is None:
                acao_ajudante = ["PASS"]
            else:
                destino_ax, destino_ay, objetivo_a = alvo_ajudante[:3]
                acao_ajudante = gerar_acao_para_alvo(
                    hx, hy, (destino_ax, destino_ay, objetivo_a), cultura_escolhida
                )

                alvos_reservados.add((destino_ax, destino_ay))

                if acao_ajudante[0] == "PLANT":
                    sementes_para_ajudantes -= 1

        acoes_ajudantes.append(acao_ajudante)

    # ---------------------------------------------------------
    # FINAL DE PARTIDA: Dia 29 — Fazendeiro volta para o celeiro
    # ---------------------------------------------------------
    if dia == 29 and hora >= 18:
        if total_itens_fazendeiro > 0 and plantas_ativas == 0:
            if (fazendeiro_x, fazendeiro_y) in POSICOES_CELEIRO:
                return {"farmer": ["DROP"], "hands": acoes_ajudantes, "market": acoes_mercado}

            posicao_celeiro_alvo = min(
                POSICOES_CELEIRO, key=lambda p: calcular_distancia(fazendeiro_x, fazendeiro_y, p[0], p[1])
            )
            movimento_celeiro = passo_em_direcao(fazendeiro_x, fazendeiro_y, posicao_celeiro_alvo[0], posicao_celeiro_alvo[1],primeiro_eixo="y")
            if movimento_celeiro is not None:
                return {"farmer": [movimento_celeiro], "hands": acoes_ajudantes, "market": acoes_mercado}

    # ---------------------------------------------------------
    # EXECUÇÃO DO COMANDO DO FAZENDEIRO
    # ---------------------------------------------------------
    if dia==0 and hora== 0:
        return {"farmer": ["NORTH"], "hands": [], "market": acoes_mercado}

    if alvo_fazendeiro is not None:
        acao_fazendeiro = gerar_acao_para_alvo(fazendeiro_x, fazendeiro_y, alvo_fazendeiro, cultura_escolhida)
        return {"farmer": acao_fazendeiro, "hands": acoes_ajudantes, "market": acoes_mercado}

    # Fallback caso não haja ação pendente
    return {"farmer": ["PASS"], "hands": acoes_ajudantes, "market": acoes_mercado}



