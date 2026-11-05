"""
Pacote oficial do agente para a competicao Kaggriculture.

Exporta a funcao principal `agent(obs)` compativel com a engine kaggle_environments.
"""

from .agente import agent
from .dados import CROPS, MARKET_PARAMS, PRODUCTS

__all__ = ["agent", "CROPS", "MARKET_PARAMS", "PRODUCTS"]

