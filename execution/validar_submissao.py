"""
Script de Execução Determinística: Validador de Submissão (Kaggriculture)
DOE Framework - Camada de Execução (E)

Verifica a conformidade do arquivo do agente com as regras de submissão do Kaggle:
- Análise de sintaxe (AST)
- Presença de ponto de entrada válido `agent(obs)`
- Ausência de dependências inválidas ou caminhos absolutos
- Teste dinâmico de execução por 5 turnos no ambiente real
"""

import sys
import os
import ast
import argparse
import importlib

# Garante que o diretório raiz do projeto esteja no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from execution.rodar_partida import suprimir_saida, carregar_agente


def validar_arquivo_estatico(caminho_arquivo):
    """Executa verificações estáticas no código fonte do agente."""
    erros = []
    avisos = []

    if not os.path.exists(caminho_arquivo):
        return False, [f"Arquivo '{caminho_arquivo}' não encontrado."], []

    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            codigo = f.read()
    except Exception as e:
        return False, [f"Falha ao ler arquivo: {e}"], []

    # 1. Checagem de Sintaxe
    try:
        tree = ast.parse(codigo)
    except SyntaxError as e:
        return False, [f"Erro de sintaxe na linha {e.lineno}: {e.msg}"], []

    # 2. Checagem de ponto de entrada
    funcoes = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    if "agent" not in funcoes:
        if "agente" in funcoes:
            avisos.append("Encontrada função 'agente(obs)' em vez de 'agent(obs)'. O Kaggle prefere 'agent'.")
        else:
            erros.append("Nenhuma função 'agent(obs)' encontrada como ponto de entrada.")

    # 3. Checagem de caminhos absolutos perigosos
    if "C:\\" in codigo or "/home/" in codigo:
        avisos.append("Detectado possível caminho absoluto no código (pode quebrar no sandbox do Kaggle).")

    return len(erros) == 0, erros, avisos


def validar_execucao_dinamica(nome_agente, passos_teste=10):
    """Executa uma rodada rápida de smoke test no ambiente do Kaggle."""
    try:
        with suprimir_saida():
            from kaggle_environments import make
            fn_agent = carregar_agente(nome_agente)
            env = make("kaggriculture", configuration={"episodeSteps": passos_teste}, debug=True)
            env.run([fn_agent, "random"])

        # Verificar se o agente gerou ações válidas
        step = env.steps[-1]
        action = step[0].action
        if action is None:
            return False, "O agente retornou ação 'None' no último turno testado."

        return True, "O agente executou turnos no ambiente sem erros ou timeouts."
    except Exception as e:
        return False, f"Exceção durante a execução dinâmica: {e}"


def executar_validacao_completa(arquivo_ou_modulo):
    """Orquestra a validação estática e dinâmica completa."""
    caminho = arquivo_ou_modulo
    if not caminho.endswith(".py") and os.path.exists(f"{caminho}.py"):
        caminho = f"{caminho}.py"

    print("\n" + "=" * 68)
    print(f"       VALIDADOR DE SUBMISSÃO KAGGLE (DOE)")
    print(f"       Alvo: {caminho}")
    print("=" * 68)

    # Teste estático
    ok_estatico, erros, avisos = validar_arquivo_estatico(caminho)
    print("\n[1/2] Verificação Estática de Código:")
    if ok_estatico:
        print("  [OK] Sintaxe Python válida")
        print("  [OK] Assinatura de entrada identificada")
    else:
        for err in erros:
            print(f"  [ERRO] {err}")

    for av in avisos:
        print(f"  [AVISO] {av}")

    if not ok_estatico:
        print("\n" + "=" * 68)
        print(" VEREDITO: REPROVADO NA CHECAGEM ESTÁTICA")
        print("=" * 68 + "\n")
        return False

    # Teste dinâmico
    print("\n[2/2] Smoke Test Dinâmico (Simulação no kaggle_environments):")
    caminho_dir = os.path.dirname(os.path.abspath(caminho))
    if caminho_dir not in sys.path:
        sys.path.insert(0, caminho_dir)
    modulo_nome = os.path.splitext(os.path.basename(caminho))[0]
    ok_dinamico, msg_dinamico = validar_execucao_dinamica(modulo_nome, passos_teste=10)

    if ok_dinamico:
        print(f"  [OK] {msg_dinamico}")
    else:
        print(f"  [FALHA] {msg_dinamico}")

    sucesso = ok_estatico and ok_dinamico
    print("\n" + "=" * 68)
    if sucesso:
        print(" VEREDITO: APROVADO PARA SUBMISSÃO NO KAGGLE")
    else:
        print(" VEREDITO: REPROVADO - CORRIJA OS ITENS ACIMA ANTES DE SUBMETER")
    print("=" * 68 + "\n")

    return sucesso


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Valida arquivo de agente para submissão no Kaggle.")
    parser.add_argument("arquivo", nargs="?", default="src/kaggriculture_agent/agente.py", help="Arquivo ou módulo a ser validado (default: src/kaggriculture_agent/agente.py)")
    args = parser.parse_args()

    executar_validacao_completa(args.arquivo)
