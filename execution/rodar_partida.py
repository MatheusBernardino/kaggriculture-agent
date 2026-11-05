"""
Script de Execução Determinística: Rodar Partida (Kaggriculture)
DOE Framework - Camada de Execução (E)

Executa uma partida completa de simulação entre dois agentes, suprime ruídos
desnecessários do console e exibe um relatório financeiro estruturado.
"""

import sys
import os
import argparse
import importlib
import contextlib

# Garante que o diretório raiz do projeto esteja no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@contextlib.contextmanager
def suprimir_saida():
    """Redireciona stdout e stderr a nível de descritores de arquivo (C/C++ e Python)."""
    try:
        null_fd = os.open(os.devnull, os.O_RDWR)
        save_out = os.dup(1)
        save_err = os.dup(2)
        os.dup2(null_fd, 1)
        os.dup2(null_fd, 2)
        try:
            yield
        finally:
            os.dup2(save_out, 1)
            os.dup2(save_err, 2)
            os.close(save_out)
            os.close(save_err)
            os.close(null_fd)
    except Exception:
        # Fallback se dup2 falhar no ambiente
        yield


def carregar_agente(nome_ou_caminho):
    """Carrega uma função de agente a partir do nome do módulo ou string reservada."""
    if nome_ou_caminho in ("random", "reaction"):
        return nome_ou_caminho
    
    modulo_nome = nome_ou_caminho.replace(".py", "").replace("/", ".").replace("\\", ".")
    try:
        try:
            mod = importlib.import_module(modulo_nome)
        except ModuleNotFoundError:
            if not modulo_nome.startswith("src."):
                mod = importlib.import_module(f"src.{modulo_nome}")
            else:
                raise
        if hasattr(mod, "agent"):
            return mod.agent
        elif hasattr(mod, "agente"):
            return mod.agente
        else:
            raise AttributeError(f"O módulo '{modulo_nome}' não possui função 'agent(obs)' ou 'agente(obs)'")
    except Exception as e:
        print(f"[ERRO] Falha ao carregar agente '{nome_ou_caminho}': {e}")
        sys.exit(1)


def executar_partida(agente1_ref, agente2_ref, passos=720, debug=False):
    """
    Executa uma partida única e retorna o dicionário com todas as métricas finais.
    """
    with suprimir_saida():
        from kaggle_environments import make

        fn1 = carregar_agente(agente1_ref)
        fn2 = carregar_agente(agente2_ref)

        env = make("kaggriculture", configuration={"episodeSteps": passos}, debug=debug)
        env.run([fn1, fn2])

    final_step = env.steps[-1]
    obs0 = final_step[0].observation
    obs1 = final_step[1].observation

    farm0 = obs0["farms"][0]
    farm1 = obs0["farms"][1]

    money0 = farm0.get("money", 0)
    money1 = farm1.get("money", 0)

    # Identificar vencedor
    if money0 > money1:
        vencedor = "Agente 1"
        saldo_vencedor = money0 - money1
    elif money1 > money0:
        vencedor = "Agente 2"
        saldo_vencedor = money1 - money0
    else:
        vencedor = "Empate"
        saldo_vencedor = 0

    resultado = {
        "agente1": agente1_ref,
        "agente2": agente2_ref,
        "passos": passos,
        "dia_final": obs0.get("day", 0),
        "hora_final": obs0.get("hour", 0),
        "player0": {
            "money": money0,
            "shed": obs0.get("private", {}).get("shed", {}),
            "seeds": obs0.get("private", {}).get("seeds", {}),
            "hands": len(farm0.get("hands", []))
        },
        "player1": {
            "money": money1,
            "shed": obs1.get("private", {}).get("shed", {}),
            "seeds": obs1.get("private", {}).get("seeds", {}),
            "hands": len(farm1.get("hands", []))
        },
        "vencedor": vencedor,
        "delta": saldo_vencedor
    }

    return resultado


def imprimir_relatorio(resultado):
    """Exibe o resultado da partida formatado em ASCII no terminal."""
    p0 = resultado["player0"]
    p1 = resultado["player1"]

    print("\n" + "=" * 65)
    print("                 RELATÓRIO DE PARTIDA (DOE)")
    print("=" * 65)
    print(f" Agente 1 (P0): {resultado['agente1']:<20} | Dinheiro Final: ${p0['money']:>10.2f}")
    print(f" Agente 2 (P1): {resultado['agente2']:<20} | Dinheiro Final: ${p1['money']:>10.2f}")
    print("-" * 65)
    print(f" Vencedor: {resultado['vencedor']} (Delta: +${resultado['delta']:.2f})")
    print(f" Duração: {resultado['passos']} turnos (Dia {resultado['dia_final']}, Hora {resultado['hora_final']})")
    print("-" * 65)
    print(f" Itens no Celeiro P0 : {sum(p0['shed'].values()):>3} un | Sementes P0 : {sum(p0['seeds'].values()):>3} un")
    print(f" Itens no Celeiro P1 : {sum(p1['shed'].values()):>3} un | Sementes P1 : {sum(p1['seeds'].values()):>3} un")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa uma partida local no Kaggriculture.")
    parser.add_argument("--agente1", default="agente3", help="Nome do módulo ou script do Agente 1 (default: agente3)")
    parser.add_argument("--agente2", default="random", help="Nome do módulo ou script do Agente 2 (default: random)")
    parser.add_argument("--passos", type=int, default=720, help="Total de passos/turnos (default: 720)")
    parser.add_argument("--debug", action="store_true", help="Ativar logs de debug da engine")

    args = parser.parse_args()

    print(f"[*] Iniciando partida: {args.agente1} vs {args.agente2} ({args.passos} turnos)...")
    res = executar_partida(args.agente1, args.agente2, passos=args.passos, debug=args.debug)
    imprimir_relatorio(res)
