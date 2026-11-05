# Diretriz: Protocolo de Benchmark e Validação de Agentes

Esta diretriz estabelece o POP (Procedimento Operacional Padrão) para validar qualquer alteração no agente antes de submeter ao Kaggle ou promovê-lo como nova versão oficial.

---

## 1. Princípio da Não-Adivinhação

- **Nunca confie em uma única partida:** O ambiente possui fatores estocásticos (movimentos do adversário, invasão de ervas daninhas, flutuações de preços). Uma única partida pode ter sorte ou azar isolado.
- **Bateria Mínima de Testes:**
  - Teste rápido (Smoke Test): **2 partidas** (1 como Player 0, 1 como Player 1).
  - Benchmark oficial de evolução: Mínimo de **10 a 20 partidas** alternando as posições de jogador para eliminar viés de iniciativa.

---

## 2. Métricas Chave de Avaliação

Toda bateria executada pelo script `execution/benchmark_agentes.py` registrará:

1. **Taxa de Vitória (Winrate %):** Percentual de partidas em que o agente terminou com mais dinheiro que o oponente.
2. **Dinheiro Médio Final ($):** Média de `farm["money"]` ao final do turno 720.
3. **Delta Médio sobre o Adversário ($):** Diferença líquida entre o dinheiro do agente e o do rival.
4. **Desvio Padrão ($\sigma$):** Mede a estabilidade da estratégia. Quanto menor o desvio com média alta, mais robusto é o agente.
5. **Taxa de Desperdício Final:** Quantidade média de itens e sementes não convertidos em dinheiro no turno final.

---

## 3. Critérios de Aceitação para Promoção de Versão

Uma nova versão (ex: `agente4.py`) só substitui a versão atual se atender a **todos** os seguintes requisitos contra a versão anterior:

- [ ] **Zero Falhas:** 100% de partidas concluídas sem exceções (`Exception`, `IndexError`, timeout).
- [ ] **Winrate Positivo:** `Winrate >= 55%` contra a versão anterior.
- [ ] **Superioridade Financeira:** `Dinheiro Médio Final` maior ou igual à baseline.
- [ ] **Validação de Submissão:** Aprovado sem alertas pelo script `execution/validar_submissao.py`.
