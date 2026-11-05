# Diretriz: Regras da Engine do Kaggriculture

Esta diretriz resume os parâmetros e regras determinísticas do ambiente **Kaggriculture** (Kaggle Simulation Competition). Todo agente desenvolvido ou modificado deve respeitar estritamente estas especificações.

---

## 1. Parâmetros Gerais da Simulação

- **Temporada:** 30 dias in-game (Dias 0 a 29).
- **Horas por dia:** 24 horas (0 a 23).
- **Total de Turnos:** 720 turnos por episódio (`episodeSteps: 720`).
- **Dimensão do Tabuleiro:** Grid 10x10 (coordenadas `r, c` de 0 a 9).
- **Caixa Inicial:** $3.000 para cada jogador.
- **Jogadores:** 2 competidores disputando o mesmo mercado.
- **Celeiro (Shed):** Ocupa 4 posições centrais: `(4,4)`, `(4,5)`, `(5,4)`, `(5,5)`.
  - Capacidade máxima do celeiro: **100 itens**.
- **Quadrantes de Terra:**
  - Inicialmente desbloqueado: Quadrante **NW** (5x5).
  - Desbloqueios adicionais (`BUY_LAND`): Quadrantes **NE**, **SW**, **SE** com custos progressivos de **$1.000**, **$2.000** e **$4.000**.

---

## 2. Unidades e Ações Permitidas

### 2.1 Fazendeiro Principal (`farmer`)
- Permanente, 1 ação por turno.
- Inventário pessoal: capacidade máxima definida pela engine.
- Ações possíveis:
  - `MOVE`: Movimentação cardeal (`UP`, `DOWN`, `LEFT`, `RIGHT`).
  - `PLANT`: Plantar semente na célula atual (requer semente no inventário ou privada).
  - `WATER`: Regar a planta na célula atual (essencial para o crescimento diário).
  - `HARVEST`: Colher produto da planta ou animal maduro.
  - `DROP`: Descarregar produtos da colheita no celeiro central.
  - `BUY_SEEDS`: Comprar sementes (quando no celeiro ou loja).
  - `BUY_LAND`: Desbloquear novo quadrante.
  - `HIRE`: Contratar ajudante temporário.

### 2.2 Ajudantes (`hands`)
- Contratados por turno/dia para acelerar tarefas (rega, colheita, transporte).
- Cada ajudante executa 1 ação por turno.

### 2.3 Ações de Mercado (`market`)
- Até **10 ordens de mercado por turno** (`maxMarketOrdersPerTurn: 10`).
- As ordens de mercado são independentes do movimento do fazendeiro e não consomem o turno de movimento.
- Ações:
  - `SELL`: Vender produto do celeiro no mercado global.
  - `BUY`: Comprar insumos.

---

## 3. Critério de Vitória e Pontuação

- **Apenas o dinheiro em caixa (`farm["money"]`) no turno final (720) determina o vencedor.**
- Produtos remanescentes no celeiro, sementes e colheitas ainda no solo têm valor **zero** ao final do episódio.
- **Modo Liquidação:** Toda produção deve ser vendida antes ou durante o dia 29 para converter inventário em dinheiro vivo.
