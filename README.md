# 🌾 Kaggriculture Autonomous Agent

Agente autônomo de tomada de decisão econômica e controle espacial desenvolvido para a competição [Kaggle Simulation: Kaggriculture](https://www.kaggle.com/competitions/kaggriculture).

O projeto adota engenharia de software modular e boas práticas de Ciência de Dados, integrando **estratégia macroeconômica**, **modelagem preditiva de saturação de mercado (Front-Running)** e **coordenação multiagente espacial (fazendeiro e ajudantes)**.

---

## 🎯 Sobre a Competição Kaggriculture

O ambiente simula a gestão de uma fazenda competitiva durante uma temporada de **30 dias in-game** (24 horas por dia = **720 turnos** ao total). Dois jogadores disputam o mesmo tabuleiro e vendem seus produtos num mercado compartilhado com curvas de oferta e demanda dinâmicas.

- **Dimensão**: Grid 10x10 (com celeiro central 2x2 nas posições `(4,4)` a `(5,5)`).
- **Critério de Vitória**: Vence quem tiver o maior volume de **dinheiro em caixa (`farm["money"]`) no turno 720**.
- **Regra Fundamental**: Produtos no celeiro, no inventário dos trabalhadores ou culturas no solo têm **valor zero** ao fim da partida. Toda a produção deve ser colhida e convertida em caixa antes do encerramento.

---

## 🧠 Arquitetura do Agente

O agente foi refatorado a partir dos experimentos iniciais para um pacote modular limpo e testável em `src/kaggriculture_agent/`:

```text
kaggriculture-agent/
├── src/
│   ├── kaggriculture_agent/       # Pacote oficial da versão atual
│   │   ├── __init__.py           # Exporta agent(obs)
│   │   ├── agente.py             # Orquestrador de turnos e fluxo de decisão
│   │   ├── alvos.py              # Priorização espacial de tarefas (colheita, rega, capina, plantio)
│   │   ├── config.py             # Constantes, limiares de preço e hiperparâmetros
│   │   ├── dados.py              # Catálogo estático (culturas, preços base e curvas da engine)
│   │   ├── estrategia.py         # Modos de época e seleção temporal de culturas
│   │   ├── fazenda.py            # Leituras puras do estado do grid e inventários
│   │   ├── mercado.py            # Gestão de ordens (compras, ajudantes, liquidação e front-running)
│   │   └── navegacao.py          # Distância Manhattan e algoritmo de passo cardeal
│   └── baselines/                # Versões históricas congeladas para benchmark
│       ├── agente_v1.py          # V1: baseline original extraída de notebook
│       ├── agente_v3.py          # V3: introdução de épocas e ajudantes
│       └── agente_v4.py          # V4: introdução de front-running de mercado
├── execution/                    # Scripts determinísticos de execução
│   ├── rodar_partida.py          # Executa 1 partida com relatório no console
│   ├── gerar_replay.py           # Renderiza replay visual interativo em HTML
│   ├── benchmark_agentes.py      # Bateria de partidas com alternância de lados
│   └── validar_submissao.py      # Validação estática e smoke test
└── tests/
    └── test_tudo.py              # Bateria de testes unitários e de integração
```

---

## 🚀 Estratégias Principais Implementadas

### 1. Seleção Dinâmica de Culturas por Horizonte Temporal
Cada cultura possui um tempo mínimo para maturação antes do fim da temporada:
- **MELON** (precisa de $\ge 12$ dias): Maior retorno financeiro por tile. Só é semeado se a cotação de mercado estiver saudável ($\ge 60\%$ do preço-base).
- **CARROT** (precisa de $\ge 4$ dias): Ciclo rápido de alto giro para a fase intermediária.
- **WHEAT** (precisa de $\ge 3$ dias): Ciclo de emergência para os últimos dias de plantio.
- **$\le 2$ dias restantes**: Interrupção total de novas sementes para evitar queima de caixa sem retorno.

### 2. Front-Running Preditivo de Mercado
O agente monitora em tempo real os tiles da fazenda adversária:
- Se identificar lavouras do oponente atingindo maturação iminente, o agente prevê a inundação do mercado e despeja o estoque correspondente do celeiro antes do rival, garantindo a venda no topo da curva de preço.

### 3. Modos Estratégicos de Época (Macro)
A partir do dia 18 (turno 432), o agente reavalia seu regime a cada 72 turnos:
- **`balanced`** (padrão): Venda escalonada conforme faixas de preço ($\ge 80\%$, $\ge 50\%$).
- **`protect`**: Quando lidera com ampla folga de caixa ($\Delta C \ge \$1.000$) e mercado deprimido, retém vendas em lotes mínimos para forçar o rival a vender barato.
- **`convert`**: Quando está atrás no caixa ($\Delta C \le -\$1.000$), vende lotes agressivos para capitalização imediata.

### 4. Liquidação Final Determinística
Nos dias 28 e 29, todas as restrições dos modos de época são sobrescritas pela prioridade absoluta de liquidação:
- Dia 28: Vendas progressivas de lote.
- Dia 29 (tarde): Todos os trabalhadores retornam ao celeiro para descarregar inventários (`DROP`).
- Dia 29 (noite): Venda contínua de todo o estoque remanescente no mercado até zerar o celeiro.

---

## 💻 Como Executar

### 1. Instalação do Ambiente
Requer Python 3.10+ com as dependências do `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Rodar uma Partida Rápida
Executa uma partida local de 720 turnos contra a baseline ou adversário aleatório:
```bash
python execution/rodar_partida.py --agente1 atual --agente2 v4
```
Aliases disponíveis: `atual`, `v4`, `v3`, `v1`, `random`.

### 3. Gerar e Visualizar Replay Interativo (HTML)
Executa a simulação completa e abre o replay visual oficial no navegador padrão:
```bash
python execution/gerar_replay.py --agente1 atual --agente2 v4 --saida resultado.html
```

### 4. Rodar Bateria Estatística (Benchmark)
Alterna posições P0/P1 para eliminar viés de iniciativa e calcula Winrate, médias financeiras e desvios:
```bash
python execution/benchmark_agentes.py --agente1 atual --agente2 v4 --partidas 10
```

### 5. Executar os Testes Unitários
```bash
python -m unittest tests/test_tudo.py
```

### 6. Compilar e Submeter no Kaggle
Para submissão, a engine do Kaggle exige um arquivo único `main.py` na raiz contendo a função `agent(obs)`. O script compilador gera e valida esse arquivo autocontido a partir dos módulos em `src/`:
```bash
# Compila e valida o main.py autocontido
python execution/gerar_submissao.py main.py

# Submissão via CLI oficial do Kaggle
kaggle competitions submit kaggriculture -f main.py -m "Agente V6 Modular Autocontido"
```

---

## 📊 Histórico e Comparativo de Versões

| Versão | Descrição | Principais Recursos | Sobra Celeiro (Fim) |
|---|---|---|:---:|
| **V1** | Monolítico Baseline | Apenas colheita simples e ajudantes | Alta |
| **V3** | Épocas + Multi-Crop | Modos Macro + Seleção de culturas | Média |
| **V4** | Front-Running | Monitoramento do rival + Venda preditiva | Média (bug de modo) |
| **V6 (Atual)** | Arquitetura Modular | Modularização completa + Correção de liquidação + Testes | **0 itens** |

