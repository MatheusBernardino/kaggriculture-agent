"""
Script de Geracao de Replay Interativo (HTML) - Kaggriculture

Executa uma partida entre dois agentes, renderiza o replay visual interativo
utilizando a engine oficial do Kaggle Environments e salva em um arquivo HTML.
"""

import argparse
import os
import sys
import webbrowser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from execution.rodar_partida import carregar_agente, suprimir_saida


def gerar_replay(
    agente1_ref: str = "atual",
    agente2_ref: str = "v4",
    caminho_saida: str = "resultado.html",
    largura: int = 800,
    altura: int = 600,
    abrir_navegador: bool = True,
    passos: int = 720,
) -> str:
    """
    Executa a simulacao e gera o arquivo HTML do replay interativo.

    Returns:
        Caminho absoluto do arquivo HTML gerado.
    """
    print(f"[*] Carregando agentes: {agente1_ref} vs {agente2_ref}...")
    fn1 = carregar_agente(agente1_ref)
    fn2 = carregar_agente(agente2_ref)

    with suprimir_saida():
        from kaggle_environments import make

        env = make("kaggriculture", configuration={"episodeSteps": passos}, debug=False)
        env.run([fn1, fn2])

    print("[*] Renderizando replay HTML...")
    html_content = env.render(mode="html", width=largura, height=altura)

    caminho_absoluto = os.path.abspath(caminho_saida)
    os.makedirs(os.path.dirname(caminho_absoluto) or ".", exist_ok=True)
    with open(caminho_absoluto, "w", encoding="utf-8") as f:
        f.write(html_content)

    tamanho_mb = os.path.getsize(caminho_absoluto) / (1024 * 1024)
    print(f"[+] Replay salvo com sucesso em: {caminho_absoluto} ({tamanho_mb:.1f} MB)")

    if abrir_navegador:
        print("[*] Abrindo replay no navegador padrao...")
        webbrowser.open(caminho_absoluto)

    return caminho_absoluto


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera replay HTML interativo de uma partida Kaggriculture.")
    parser.add_argument("--agente1", default="atual", help="Agente 1 (default: atual)")
    parser.add_argument("--agente2", default="v4", help="Agente 2 (default: v4)")
    parser.add_argument("--saida", default="resultado.html", help="Caminho do arquivo HTML de saida (default: resultado.html)")
    parser.add_argument("--passos", type=int, default=720, help="Total de turnos da partida (default: 720)")
    parser.add_argument("--no-browser", action="store_true", help="Nao abrir automaticamente no navegador")

    args = parser.parse_args()
    gerar_replay(
        agente1_ref=args.agente1,
        agente2_ref=args.agente2,
        caminho_saida=args.saida,
        abrir_navegador=not args.no_browser,
        passos=args.passos,
    )
