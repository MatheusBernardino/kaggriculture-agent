try:
    from .agente3 import agent as agentv3
except ImportError:
    from agente3 import agent as agentv3
if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando simulacao local do Agente Kaggriculture V4...")
    print("=" * 60)

    try:
        from kaggle_environments import make

        # Simulacao completa de uma temporada (720 turnos = 30 dias x 24 horas)
        env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
        env.run([agentv3, "random"])

        final_obs = env.steps[-1][0].observation
        farm = final_obs["farms"][final_obs["player"]]
        privado = final_obs["private"]

        print("\n" + "=" * 60)
        print("SIMULACAO CONCLUIDA COM SUCESSO!")
        print("=" * 60)
        print(f"Dia final: {final_obs.get('day', 0)} | Hora: {final_obs.get('hour', 0)}")
        print(f"Dinheiro final: ${farm.get('money', 0):.2f}")
        print(f"Celeiro (Shed): {privado.get('shed', {})}")
        print(f"Sementes restantes: {privado.get('seeds', {})}")
        print(f"Ajudantes ativos: {len(farm.get('hands', []))}")
        print("=" * 60)
    except Exception as e:
        print(f"Erro ao rodar simulacao: {e}")
