"""
Bateria de Testes Unitarios e Integracao (Kaggriculture Agent)
Utiliza unittest (standard library Python) para execucao deterministica sem dependencias externas.
"""

import unittest
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.kaggriculture_agent.dados import (
    CROPS,
    MARKET_PARAMS,
    PRODUCTS,
    get_crop,
    get_product_base_price,
    crop_seed_cost,
)
from src.kaggriculture_agent.navegacao import (
    calcular_distancia,
    passo_em_direcao,
    celeiro_mais_proximo,
)
from src.kaggriculture_agent.fazenda import (
    contar_plantas,
    total_itens,
    dias_restantes,
    contar_tiles_cultivaveis,
)
from src.kaggriculture_agent.estrategia import (
    classificar_modo,
    cultura_viavel,
    escolher_cultura,
)
from src.kaggriculture_agent.mercado import calcular_lote_venda
from src.kaggriculture_agent import agent


class TestDados(unittest.TestCase):
    def test_culturas_existentes(self):
        for crop in ("WHEAT", "CARROT", "MELON", "TOMATO", "STRAWBERRY"):
            self.assertIn(crop, CROPS)
            info = get_crop(crop)
            self.assertIn("seed_cost", info)
            self.assertGreater(info["seed_cost"], 0)

    def test_precos_base(self):
        self.assertEqual(get_product_base_price("WHEAT"), 25)
        self.assertEqual(get_product_base_price("CARROT"), 35)
        self.assertEqual(get_product_base_price("MELON"), 250)


class TestNavegacao(unittest.TestCase):
    def test_distancia_manhattan(self):
        self.assertEqual(calcular_distancia(0, 0, 3, 4), 7)
        self.assertEqual(calcular_distancia(5, 5, 5, 5), 0)

    def test_passo_em_direcao(self):
        self.assertEqual(passo_em_direcao(0, 0, 2, 0, primeiro_eixo="x"), "EAST")
        self.assertEqual(passo_em_direcao(2, 0, 0, 0, primeiro_eixo="x"), "WEST")
        self.assertEqual(passo_em_direcao(0, 0, 0, 2, primeiro_eixo="y"), "SOUTH")
        self.assertEqual(passo_em_direcao(0, 2, 0, 0, primeiro_eixo="y"), "NORTH")
        self.assertIsNone(passo_em_direcao(1, 1, 1, 1))

    def test_celeiro_mais_proximo(self):
        cx, cy = celeiro_mais_proximo(0, 0)
        self.assertIn((cx, cy), {(4, 4), (4, 5), (5, 4), (5, 5)})
        self.assertEqual((cx, cy), (4, 4))


class TestFazenda(unittest.TestCase):
    def test_contar_plantas(self):
        fazenda = {
            "tiles": [
                [{"kind": "PLANT", "crop": "WHEAT"}, None],
                ["LOCKED", {"kind": "WEED"}],
            ]
        }
        self.assertEqual(contar_plantas(fazenda), 1)
        self.assertEqual(contar_tiles_cultivaveis(fazenda), 3)

    def test_total_itens(self):
        self.assertEqual(total_itens({"WHEAT": 5, "CARROT": 3}), 8)

    def test_dias_restantes(self):
        self.assertEqual(dias_restantes({"day": 0}), 29)
        self.assertEqual(dias_restantes({"day": 28}), 1)
        self.assertEqual(dias_restantes({"day": 29}), 0)


class TestEstrategia(unittest.TestCase):
    def test_cultura_viavel(self):
        self.assertTrue(cultura_viavel("MELON", 12))
        self.assertFalse(cultura_viavel("MELON", 11))
        self.assertTrue(cultura_viavel("CARROT", 4))
        self.assertFalse(cultura_viavel("CARROT", 3))
        self.assertTrue(cultura_viavel("WHEAT", 3))
        self.assertFalse(cultura_viavel("WHEAT", 2))

    def test_classificar_modo(self):
        # Lider confortavel, mercado premium deprimido -> protect
        self.assertEqual(classificar_modo(1500, 0.70, -2, False), "protect")
        # Em desvantagem, mercado favoravel -> convert
        self.assertEqual(classificar_modo(-1200, 0.85, 2, False), "convert")
        # Padrao -> balanced
        self.assertEqual(classificar_modo(0, 0.80, 0, False), "balanced")


class TestMercado(unittest.TestCase):
    def test_liquidacao_prevalece_sobre_protect(self):
        # No dia 29, deve liquidar o celeiro mesmo que o modo seja 'protect'
        lote = calcular_lote_venda(
            produto="MELON",
            quantidade=20,
            preco_atual=100.0,
            preco_base=250.0,
            dia=29,
            modo_atual="protect",
            produtos_em_risco=set(),
            total_no_celeiro=20,
        )
        self.assertEqual(lote, 10)  # Max ordens de mercado permitidas

    def test_front_running(self):
        lote = calcular_lote_venda(
            produto="MELON",
            quantidade=5,
            preco_atual=150.0,
            preco_base=250.0,
            dia=10,
            modo_atual="balanced",
            produtos_em_risco={"MELON"},
            total_no_celeiro=5,
        )
        self.assertEqual(lote, 5)


class TestSmokeIntegration(unittest.TestCase):
    def test_rodar_smoke_simulacao(self):
        from kaggle_environments import make
        env = make("kaggriculture", configuration={"episodeSteps": 5}, debug=False)
        env.run([agent, "random"])
        self.assertGreater(len(env.steps), 1)


if __name__ == "__main__":
    unittest.main()

