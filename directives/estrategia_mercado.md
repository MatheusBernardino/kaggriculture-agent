# Diretriz: Estratégia de Mercado e Seleção de Culturas

Esta diretriz estabelece a lógica econômica para maximização do lucro líquido no Kaggriculture, balanceando ciclo de vida das culturas e curvas dinâmicas de preços.

---

## 1. Dados Econômicos das Culturas Principais

| Cultura | Custo Semente | Preço Base | Dias para Maturação | Tipo | Rendimento Típico |
|---|---|---|---|---|---|
| **CARROT** | $20 | $35 | 3 dias | One-time | 3 a 4 unidades |
| **WHEAT** | $10 | $25 | 4 dias | One-time | 4 a 6 unidades |
| **MELON** | $150 | $250 | 11 dias | One-time | Alta margem líquida |
| **TOMATO** | $50 | $60 | 8-11 dias | Recorrente (diário) | 4 colheitas |
| **STRAWBERRY**| $100 | $120 | 10-16 dias | Recorrente (a cada 2 dias) | 4 colheitas |

---

## 2. Janelas de Seleção de Culturas por Dia

O horizonte de 30 dias (dias 0 a 29) impõe prazos fatais para que cada semente plantada chegue à colheita:

```
Dias Restantes = 29 - obs["day"]

IF Dias Restantes >= 12 E preco_mercado(MELON) >= 150:
    -> Plantar MELON (Maior retorno financeiro por célula)

ELSE IF Dias Restantes >= 4:
    -> Plantar CARROT (Ciclo rápido de 3 dias, alto giro)

ELSE IF Dias Restantes >= 3:
    -> Plantar WHEAT (Ciclo de emergência para últimas moedas)

ELSE:
    -> NÃO PLANTAR (Sementes não irão maturar até o dia 29)
```

---

## 3. Dinâmica de Mercado e Vendas

### 3.1 Drenagem dos Comércios da Cidade
- Os comércios da cidade drenam o estoque do mercado a cada **4 turnos** (`townShopSellInterval: 4`).
- Se o mercado estiver saturado e os preços caírem, esperar alguns turnos permite que a cidade absorva o excesso e o preço se recupere.

### 3.2 Regras de Venda por Turno
Para evitar afundar a curva de preço vendendo em massa de uma só vez:

1. **Liquidação Final (Dia >= 28):**
   - Vender **tudo** imediatamente. Qualquer item que sobrar no celeiro no turno 720 vale $0.
2. **Preço Alto (`preco >= base_price * 0.80`):**
   - Vender até 5 unidades por turno.
3. **Preço Médio (`preco >= base_price * 0.50`):**
   - Vender até 2 unidades por turno.
4. **Preço Baixo (`preco < base_price * 0.50`):**
   - **Reter estoque** no celeiro aguardando recuperação pela drenagem da cidade.
   - *Exceção de segurança:* Se o celeiro atingir mais de 80 itens (capacidade máxima 100), vender 2 unidades para evitar bloqueio de colheitas.
