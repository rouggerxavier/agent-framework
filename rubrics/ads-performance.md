# Ads Performance Rubric

Use para avaliar diagnósticos de performance de campanhas de tráfego pago (Google Ads).

## Criterios
- **Evidência de dados:** o diagnóstico é fundamentado em métricas reais (conversions, CPA, Lost IS, CTR), não em intuição.
- **Isolamento de causa-raiz:** separa claramente problemas de tracking (tag quebrada, atraso de conversão) de problemas de entrega (orçamento esgotado, lance insuficiente) ou relevância de anúncio (Ad Rank).
- **Proporcionalidade de ação:** prioriza ações de maior impacto imediato sem sugerir mudanças drásticas que resetem o aprendizado da IA de lances desnecessariamente.
- **Proteção de orçamento:** identifica vazamentos de verba e termos de busca irrelevantes antes de sugerir aumento de investimento.
- **Conformidade e segurança:** sem exposição de tokens, credenciais ou IDs de contas indevidas.

## Checklist
- [ ] O ID da conta (`customer_id`) foi verificado como ativo.
- [ ] O período de comparação tem base temporal equivalente (ex: mesmos dias da semana).
- [ ] A métrica de conversão foi confrontada com o volume no CRM/banco para descartar quebra de webhook.
- [ ] A análise de Lost IS (Budget vs Rank) foi explicitada.
- [ ] Termos de pesquisa negativos ou canais de exibição com alto custo e zero conversão foram verificados.

## Red flags
- Sugerir aumento de orçamento sem verificar se o Lost IS Budget é o gargalo real.
- Confundir queda de conversão no painel com janela de atribuição atrasada (*conversion lag*).
- Resetar estratégias de lances inteligentes (Target CPA / Target ROAS) sem analisar histórico de 14 a 30 dias.
