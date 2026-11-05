"""
Script de Compilacao de Submissao Kaggle: Gerar main.py Autocontido

Gera um arquivo 'main.py' unico e 100% autocontido a partir dos modulos
de src/kaggriculture_agent/, pronto para submissao direta no Kaggle:
    kaggle competitions submit kaggriculture -f main.py -m "Agente V6 Modular"

Verifica a conformidade com a engine do Kaggle executando um smoke test completo.
"""

import ast
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def remover_imports_relativos(codigo: str) -> str:
    """
    Remove todos os comandos 'from . import ...' ou 'from .modulo import ...',
    inclusive aqueles com multiplas linhas entre parenteses.
    """
    linhas = codigo.splitlines()
    novas_linhas = []
    dentro_de_parenteses_relativo = False

    for linha in linhas:
        linha_strip = linha.strip()

        # Início de um import relativo
        if linha_strip.startswith("from .") or linha_strip.startswith("import ."):
            if "(" in linha and ")" not in linha:
                dentro_de_parenteses_relativo = True
            continue

        # Continuação de um import relativo em múltiplas linhas
        if dentro_de_parenteses_relativo:
            if ")" in linha:
                dentro_de_parenteses_relativo = False
            continue

        # Remove imports de typing repetidos
        if linha_strip.startswith("from typing import"):
            continue

        novas_linhas.append(linha)

    return "\n".join(novas_linhas)


def compilar_submissao(caminho_saida: str = "main.py") -> str:
    """Concatena e organiza todas as definicoes dos modulos em um unico arquivo main.py."""
    caminho_absoluto = os.path.abspath(caminho_saida)
    os.makedirs(os.path.dirname(caminho_absoluto) or ".", exist_ok=True)

    modulos = [
        "src/kaggriculture_agent/config.py",
        "src/kaggriculture_agent/dados.py",
        "src/kaggriculture_agent/navegacao.py",
        "src/kaggriculture_agent/fazenda.py",
        "src/kaggriculture_agent/estrategia.py",
        "src/kaggriculture_agent/mercado.py",
        "src/kaggriculture_agent/alvos.py",
        "src/kaggriculture_agent/agente.py",
    ]

    blocos = [
        '"""',
        "Kaggriculture Autonomous Agent - Submission File",
        "Arquivo autocontido compilado para execucao direta no sandbox do Kaggle.",
        "Ponto de entrada oficial: def agent(obs)",
        '"""',
        "",
        "from typing import Dict, List, Optional, Set, Tuple",
        "",
    ]

    for rel_path in modulos:
        full_path = os.path.join(BASE_DIR, rel_path)
        with open(full_path, "r", encoding="utf-8") as f:
            conteudo = f.read()

        limpo = remover_imports_relativos(conteudo)
        blocos.append(f"# {'=' * 70}")
        blocos.append(f"# MODULO: {rel_path}")
        blocos.append(f"# {'=' * 70}")
        blocos.append(limpo)
        blocos.append("")

    codigo_final = "\n".join(blocos)

    # Validar sintaxe antes de salvar
    ast.parse(codigo_final)

    with open(caminho_absoluto, "w", encoding="utf-8") as f:
        f.write(codigo_final)

    print(f"[+] Arquivo de submissao compilado com sucesso: {caminho_absoluto}")
    print(f"    Tamanho: {os.path.getsize(caminho_absoluto)} bytes | Linhas: {len(codigo_final.splitlines())}")
    return caminho_absoluto


def validar_arquivo_submissao(caminho_arquivo: str) -> bool:
    """Executa o smoke test oficial passando o caminho do arquivo para o kaggle_environments."""
    print(f"[*] Validando submissao no ambiente Kaggle com env.run(['{caminho_arquivo}', 'random'])...")
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": 15}, debug=True)
    env.run([caminho_arquivo, "random"])

    ultimo_passo = env.steps[-1]
    status_p0 = ultimo_passo[0].status
    acao_p0 = ultimo_passo[0].action

    if status_p0 == "DONE" or acao_p0 is not None:
        print("[+] Validacao concluida com SUCESSO! O arquivo esta 100% compativel com o Kaggle.")
        return True
    else:
        print(f"[-] Falha na validacao: status={status_p0}, acao={acao_p0}")
        return False


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    arquivo_gerado = compilar_submissao(caminho)
    ok = validar_arquivo_submissao(arquivo_gerado)
    if not ok:
        sys.exit(1)
