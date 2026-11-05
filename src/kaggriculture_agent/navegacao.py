"""
Navegacao no grid: movimento cardeal e distancias.

Convencao de coordenadas da engine: posicoes sao (x, y) e os tiles sao
acessados como `tiles[y][x]`. NORTH diminui y, SOUTH aumenta y.
"""

from .config import POSICOES_CELEIRO

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

