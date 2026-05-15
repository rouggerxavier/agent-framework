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
Para refator de API, siga `../../workflows/api-refactor.md`. Especifico:
1. Identifique consumidores, endpoints, schemas e comportamento publico.
2. Aplique a rubric de contrato e a de testes (ver Arquivos de apoio).
3. Recomende mitigacao, migracao ou comunicacao.

## Saida obrigatoria
Conforme `../../templates/audit-report.md`: contratos afetados, riscos de
breaking change, problemas de request/response/status/error e plano de
mitigacao ou versionamento.

## Criterios de aceite
- Diferencie contrato publico de detalhe interno.
- Nao aprove quebra sem plano de migracao.
- Demais criterios: rubric de contrato em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/api-refactor.md
- Rubric: ../../rubrics/api-contract.md
- Rubric: ../../rubrics/testing.md
- Template: ../../templates/audit-report.md

## Exemplos de uso
- Codex: `$api-contract-auditor Revise esta mudanca de endpoint antes do deploy.`
- Claude Code: `/api-contract-auditor Audite payloads, status codes e compatibilidade.`
