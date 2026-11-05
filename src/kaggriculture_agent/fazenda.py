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

