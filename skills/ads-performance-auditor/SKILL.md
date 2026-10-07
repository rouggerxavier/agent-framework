---
name: ads-performance-auditor
description: Use para auditar performance de Google Ads, diagnosticar quedas de conversões, fluxo reduzido de leads, restrições de orçamento e impressões perdidas (Lost IS) por lance ou ranking via MCP e consultas GAQL.
---

# Ads Performance Auditor

## Objetivo
Diagnosticar quedas de desempenho, anomalias de conversão, estrangulamentos de orçamento e perda de oportunidades em campanhas de tráfego pago (Google Ads) utilizando consultas GAQL estruturadas e integração via MCP Server.

## Quando usar
- Ao investigar quedas repentinas de conversões (volume ou valor) em campanhas de Google Ads.
- Quando o volume de leads qualificados gerados por anúncios estiver abaixo do esperado.
- Para auditar perda de impressões (*Lost Impression Share*) por orçamento (*budget*) ou classificação de anúncio (*rank*).
- Para analisar restrições de lances, orçamentos limitados ou reprovações de políticas de anúncios.
- Ao conduzir auditorias periódicas de eficiência de gastos em tráfego pago.

## Quando nao usar
- Para criar campanhas do zero no painel ou redigir criativos/copywriting sem análise de dados.
- Para gerenciar anúncios em redes de afiliados ou SDKs de monetização mobile in-app (AdMob/IMA).
- Para sincronizar listas de CRM e dados de conversão offline (use `crm-ad-sync-planner`).
- Sem acesso a credenciais, MCP server do Google Ads ou dados de relatório exportados.

## Entradas esperadas
- ID do cliente Google Ads (`customer_id` formatado como 10 dígitos, sem traços nas chamadas de API).
- Período de análise (ex: últimos 7 dias vs 7 dias anteriores, ou últimos 30 dias).
- Sintoma observado (ex: "queda de 40% em leads", "CPA subiu para o dobro", "campanha limitada por orçamento").
- MCP Server do Google Ads configurado ou permissão para consultar métricas via API/export.

## Workflow
1. **Identificar contas ativas:**
   - Obter lista de IDs acessíveis via `customer_client` filtrando por `status = 'ENABLED'` e `manager = FALSE`.
   - Confirmar o ID da conta do cliente antes de disparar queries.

2. **Diagnóstico de conversão e leads:**
   - Consultar `campaign` e `metrics`: comparar `conversions`, `conversions_value`, `cost_per_conversion` e `all_conversions` no período afetado contra a linha de base anterior.
   - Segmentar por tipo de ação de conversão (`conversion_action`) para isolar se a falha é no tracking ou na demanda.

3. **Diagnóstico de entrega e fatia de impressões:**
   - Consultar métricas de visibilidade:
     - `search_impression_share`
     - `search_budget_lost_impression_share` (Lost IS Budget)
     - `search_rank_lost_impression_share` (Lost IS Rank)
   - Avaliar se o anúncio parou de imprimir por falta de verba diária ou por qualidade/lance baixo.

4. **Auditoria de lances e status de campanha:**
   - Verificar `primary_status` e `primary_status_reasons` da campanha (ex: `BUDGET_CONSTRAINED`, `BID_CONSTRAINED`, `POLICY_UNDER_REVIEW`).
   - Identificar grupos de anúncios ou palavras-chave com CTR baixo ou índice de qualidade crítico.

5. **Consolidar relatório e ações corretivas:**
   - Preencher `templates/ads-performance-audit-report.md`.
   - Avaliar os achados segundo `rubrics/ads-performance.md`.
   - Listar ações em ordem de prioridade: ajuste de orçamento, realocação de lances, revisão de termos de pesquisa negativos ou correção de tags.

## Saida obrigatoria
- Relatório de diagnóstico estruturado contendo:
  - Resumo executivo do sintoma vs causa-raiz identificada.
  - Tabela comparativa de métricas (período anterior vs período atual).
  - Segmentação de Lost IS (orçamento vs ranking).
  - Diagnóstico de tracking e status de conversões.
  - Recomendações imediatas e de médio prazo categorizadas por impacto.

## Criterios de aceite
- O diagnóstico aponta a causa-raiz com base em dados de GAQL/métricas, não em suposições genéricas.
- IDs de clientes e parâmetros são validados antes da consulta.
- Nenhuma chave de API, token ou credencial é exposta em logs ou relatórios.
- Recomendações respeitam o orçamento e os limites de negócio informados.

## Arquivos de apoio
- Rubric: `rubrics/ads-performance.md`
- Template: `templates/ads-performance-audit-report.md`

## Exemplos de uso
- "Investigue por que o fluxo de leads da campanha de lançamentos caiu pela metade nesta semana."
- "Audite se a campanha do Google Ads está limitada por orçamento ou perdendo impressões por lance."
- "Rode uma auditoria completa na conta do cliente via Google Ads MCP e aponte os maiores desperdícios de verba."
