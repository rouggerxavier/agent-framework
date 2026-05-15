---
name: api-contract-auditor
description: Use para auditar contratos de API, payloads, status codes, erros, compatibilidade, versionamento, webhooks e impacto em clientes.
---

# API Contract Auditor

## Objetivo
Encontrar riscos de quebra em APIs e orientar mudancas compativeis, testaveis e comunicaveis.

## Quando usar
- Ao criar, alterar ou revisar endpoints, webhooks, SDKs ou schemas.
- Antes de refatorar API consumida por clientes.
- Quando ha risco de breaking change.

## Quando nao usar
- Para logica interna sem fronteira de contrato.
- Para performance sem mudanca de comportamento externo.
- Para substituir testes de integracao ou contrato.

## Entradas esperadas
- Especificacao, diff, rotas, schemas ou exemplos de payload.
- Consumidores conhecidos e requisitos de compatibilidade.
- Mudanca pretendida ou bug report.

## Workflow
1. Identifique consumidores, endpoints, schemas e comportamento publico.
2. Revise request, response, erros, auth, idempotencia e paginacao.
3. Avalie compatibilidade e versionamento.
4. Liste testes de contrato e casos limite.
5. Recomende mitigacao, migracao ou comunicacao.

## Saida obrigatoria
- Contratos afetados.
- Riscos de breaking change.
- Problemas de request, response, status ou error shape.
- Testes de contrato recomendados.
- Plano de mitigacao ou versionamento.

## Criterios de aceite
- Diferencie contrato publico de detalhe interno.
- Inclua exemplos concretos quando possivel.
- Nao aprove quebra sem plano de migracao.
- Considere auth, erro e idempotencia quando relevantes.

## Exemplos de uso
- Codex: `$api-contract-auditor Revise esta mudanca de endpoint antes do deploy.`
- Claude Code: `/api-contract-auditor Audite payloads, status codes e compatibilidade.`
