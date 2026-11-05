import webbrowser
from kaggle_environments import make
try:
    from .agente2 import agent as agentv2
    from .agente import agent as agentv1
    from .agente3 import agent as agentv3
except ImportError:
    from agente2 import agent as agentv2
    from agente import agent as agentv1
    from agente3 import agent as agentv3
def run_random(show:bool=True)-> None:
    env = make("kaggriculture", debug=False)
    env.run([agentv1, agentv3])
    if show:
        html_content = env.render(mode="html", width=800, height=600)
        output_path = "resultado.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Visualização salva em {output_path}. Abrindo no navegador...")
        webbrowser.open(output_path)

def main() -> None:
    print("Hello from fazendinha!")
    run_random()

if __name__ == "__main__":
    main()