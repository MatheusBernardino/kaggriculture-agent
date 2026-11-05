# DOE Framework — Kaggriculture Agent

Este repositório adota o **DOE Framework** (Directives, Orchestration, Execution) para estruturar o desenvolvimento, testes e validações do agente da competição **Kaggriculture** de forma determinística e reproduzível.

---

## Estrutura das 3 Camadas

```
kaggriculture-agent/
├── directives/                        # [D] Diretrizes e Regras de Negócio (POPs)
│   ├── regras_kaggriculture.md        # Regras formais da engine (Grid 10x10, 720 turnos, ações)
│   ├── estrategia_mercado.md          # Lógica econômica, janelas de culturas e curvas de preços
│   └── protocolo_benchmark.md         # Procedimento padrão para avaliação e critérios de aceite
│
├── execution/                         # [E] Scripts Determinísticos de Teste e Apoio
│   ├── rodar_partida.py               # Executa 1 partida individual entre 2 agentes
│   ├── benchmark_agentes.py           # Bateria de N partidas com alternância de lados e winrate
│   └── validar_submissao.py           # Validação estática e smoke test para submissão Kaggle
│
├── .tmp/                              # Logs temporários e dados brutos de simulação
│   └── simulacoes/
│
└── agente3.py                         # [O] Camada de Orquestração (Código do Agente)
```

---

## Comandos Rápidos de Execução

### 1. Rodar uma partida individual rápida
Testa o `agente3` contra um adversário aleatório ou versão anterior por 720 turnos:
```bash
python execution/rodar_partida.py --agente1 agente3 --agente2 random
```
Ou contra o `agente2`:
```bash
python execution/rodar_partida.py --agente1 agente3 --agente2 agente2
```

### 2. Rodar Benchmark Estatístico (Bateria de Partidas)
Executa $N$ partidas alternando posições (P0/P1) para eliminar viés de iniciativa e calcula Winrate %, Média de Dinheiro e Desvio Padrão:
```bash
python execution/benchmark_agentes.py --agente1 agente3 --agente2 agente2 --partidas 10
```
*O resultado é salvo automaticamente em `.tmp/simulacoes/`.*

### 3. Validar arquivo para Submissão no Kaggle
Verifica sintaxe, ponto de entrada `agent(obs)` e executa um smoke test dinâmico:
```bash
python execution/validar_submissao.py agente3.py
```
