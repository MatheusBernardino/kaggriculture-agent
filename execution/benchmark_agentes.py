"""
Script de Execução Determinística: Benchmark de Agentes (Kaggriculture)
DOE Framework - Camada de Execução (E)

Executa baterias estatísticas de N partidas entre dois agentes, alternando
as posições de jogador (P0/P1) para eliminar viés de iniciativa e calculando
métricas de winrate, retorno financeiro médio e estabilidade.
"""

import sys
import os
import argparse
import json
import statistics
from datetime import datetime

from typing import Any, Dict

# Garante que o diretório raiz do projeto esteja no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from execution.rodar_partida import executar_partida


def executar_benchmark(
    agente1_ref: str,
    agente2_ref: str,
    num_partidas: int = 4,
    passos: int = 720,
    salvar_json: bool = True,
) -> Dict[str, Any]:
    """
    Executa N partidas com alternância de lados e calcula estatísticas consolidadas.
    """
    vitorias_a1 = 0
    vitorias_a2 = 0
    empates = 0

    dinheiros_a1 = []
    dinheiros_a2 = []
    sobras_celeiro_a1 = []
    sobras_sementes_a1 = []

    historico = []

    print(f"\n" + "=" * 68)
    print(f"       INICIANDO BENCHMARK DOE ({num_partidas} PARTIDAS)")
    print(f"       {agente1_ref} (Agente 1) vs {agente2_ref} (Agente 2)")
    print("=" * 68)

    for i in range(1, num_partidas + 1):
        # Alterna posições: se ímpar, A1 é P0; se par, A2 é P0
        if i % 2 != 0:
            p0_nome, p1_nome = agente1_ref, agente2_ref
            res = executar_partida(p0_nome, p1_nome, passos=passos)
            m_a1 = res["player0"]["money"]
            m_a2 = res["player1"]["money"]
            celeiro_a1 = sum(res["player0"]["shed"].values())
            sementes_a1 = sum(res["player0"]["seeds"].values())
            a1_pos = "P0"
        else:
            p0_nome, p1_nome = agente2_ref, agente1_ref
            res = executar_partida(p0_nome, p1_nome, passos=passos)
            m_a1 = res["player1"]["money"]
            m_a2 = res["player0"]["money"]
            celeiro_a1 = sum(res["player1"]["shed"].values())
            sementes_a1 = sum(res["player1"]["seeds"].values())
            a1_pos = "P1"

        dinheiros_a1.append(m_a1)
        dinheiros_a2.append(m_a2)
        sobras_celeiro_a1.append(celeiro_a1)
        sobras_sementes_a1.append(sementes_a1)

        if m_a1 > m_a2:
            vitorias_a1 += 1
            status = "VITORIA"
        elif m_a2 > m_a1:
            vitorias_a2 += 1
            status = "DERROTA"
        else:
            empates += 1
            status = "EMPATE"

        print(f" Partida {i:>2}/{num_partidas}: [{a1_pos}] {agente1_ref} ${m_a1:>8.2f} | [{status}] vs ${m_a2:>8.2f}")

        historico.append({
            "partida": i,
            "a1_pos": a1_pos,
            "money_a1": m_a1,
            "money_a2": m_a2,
            "status": status,
            "celeiro_a1": celeiro_a1,
            "sementes_a1": sementes_a1
        })

    # Métricas consolidadas
    media_a1 = statistics.mean(dinheiros_a1)
    media_a2 = statistics.mean(dinheiros_a2)
    desvio_a1 = statistics.stdev(dinheiros_a1) if len(dinheiros_a1) > 1 else 0.0
    desvio_a2 = statistics.stdev(dinheiros_a2) if len(dinheiros_a2) > 1 else 0.0
    winrate_a1 = (vitorias_a1 / num_partidas) * 100.0

    sumario = {
        "agente1": agente1_ref,
        "agente2": agente2_ref,
        "total_partidas": num_partidas,
        "vitorias_a1": vitorias_a1,
        "vitorias_a2": vitorias_a2,
        "empates": empates,
        "winrate_a1_pct": winrate_a1,
        "media_dinheiro_a1": media_a1,
        "desvio_dinheiro_a1": desvio_a1,
        "min_dinheiro_a1": min(dinheiros_a1),
        "max_dinheiro_a1": max(dinheiros_a1),
        "media_dinheiro_a2": media_a2,
        "desvio_dinheiro_a2": desvio_a2,
        "min_dinheiro_a2": min(dinheiros_a2),
        "max_dinheiro_a2": max(dinheiros_a2),
        "delta_medio": media_a1 - media_a2,
        "media_sobra_celeiro_a1": statistics.mean(sobras_celeiro_a1),
        "media_sobra_sementes_a1": statistics.mean(sobras_sementes_a1),
        "historico": historico
    }

    # Salva em .tmp/simulacoes
    if salvar_json:
        pasta_sim = os.path.join(BASE_DIR, ".tmp", "simulacoes")
        os.makedirs(pasta_sim, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_json = os.path.join(pasta_sim, f"benchmark_{agente1_ref}_vs_{agente2_ref}_{ts}.json")
        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(sumario, f, indent=2, ensure_ascii=False)
        sumario["log_path"] = arquivo_json

    return sumario


def imprimir_relatorio_benchmark(sumario: Dict[str, Any]) -> None:
    """Formata e imprime as métricas consolidadas."""
    print("\n" + "=" * 68)
    print("                 RESULTADO CONSOLIDADO DO BENCHMARK")
    print("=" * 68)
    print(f" Total de Partidas : {sumario['total_partidas']}")
    print(f" Vitórias [{sumario['agente1']}]: {sumario['vitorias_a1']} ({sumario['winrate_a1_pct']:.1f}%)")
    print(f" Vitórias [{sumario['agente2']}]: {sumario['vitorias_a2']} ({((sumario['vitorias_a2']/sumario['total_partidas'])*100):.1f}%)")
    print(f" Empates           : {sumario['empates']}")
    print("-" * 68)
    print(f" {sumario['agente1']:<18} -> Média: ${sumario['media_dinheiro_a1']:>9.2f} (±${sumario['desvio_dinheiro_a1']:>7.2f}) [Min: ${sumario['min_dinheiro_a1']:.0f}, Max: ${sumario['max_dinheiro_a1']:.0f}]")
    print(f" {sumario['agente2']:<18} -> Média: ${sumario['media_dinheiro_a2']:>9.2f} (±${sumario['desvio_dinheiro_a2']:>7.2f}) [Min: ${sumario['min_dinheiro_a2']:.0f}, Max: ${sumario['max_dinheiro_a2']:.0f}]")
    print(f" Vantagem Média (Delta): +${sumario['delta_medio']:>9.2f}")
    print("-" * 68)
    print(f" Desperdício Médio (A1) -> Celeiro: {sumario['media_sobra_celeiro_a1']:.1f} itens | Sementes: {sumario['media_sobra_sementes_a1']:.1f} sementes")
    
    # Avaliação conforme diretriz
    aprovado = (sumario['winrate_a1_pct'] >= 55.0) and (sumario['delta_medio'] > 0)
    veredito = "APROVADO (Superou a baseline)" if aprovado else "REPROVADO (Não atendeu aos critérios do protocolo)"
    print(f" Veredito DOE       : {veredito}")
    
    if "log_path" in sumario:
        print(f" Log salvo em      : {sumario['log_path']}")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa benchmark estatístico entre dois agentes.")
    parser.add_argument("--agente1", default="atual", help="Nome do Agente 1 (default: atual)")
    parser.add_argument("--agente2", default="v4", help="Nome do Agente 2 (default: v4)")
    parser.add_argument("--partidas", type=int, default=4, help="Número de partidas da bateria (default: 4)")
    parser.add_argument("--passos", type=int, default=720, help="Passos por partida (default: 720)")

    args = parser.parse_args()

    sumario = executar_benchmark(args.agente1, args.agente2, num_partidas=args.partidas, passos=args.passos)
    imprimir_relatorio_benchmark(sumario)
