---
name: plan-quality-checker
description: Use para auditar planos antes da execucao, encontrando tarefas vagas, dependencias erradas, aceite nao verificavel e gates ausentes.
---

# Plan Quality Checker

## Objetivo
Verificar se um plano esta pronto para execucao por agente ou humano sem depender de adivinhacao, retrabalho ou criterios subjetivos.

## Quando usar
- Antes de executar plano backend, refatoracao, migration, API ou feature multi-arquivo.
- Depois de `backend-slice-planner`, `implementation-planner` ou plano escrito por outro agente.
- Quando o plano parece plausivel, mas pode estar vago ou incompleto.
- Antes de delegar execucao para outro agente.

## Quando nao usar
- Para revisar codigo ja implementado; use `diff-reviewer`.
- Para criar o plano do zero; use `backend-slice-planner` ou `implementation-planner`.
- Para tarefa trivial classificada como `fast`.

## Entradas esperadas
- Plano, PRD, issue ou lista de tarefas.
- Objetivo e restricoes conhecidas.
- Mapa do repo ou arquivos citados no plano.
- Rubrics relevantes: API, dados, testes, seguranca ou performance.

## Workflow
1. Identifique objetivo, escopo e criterio de done prometido pelo plano.
2. Cheque atomicidade: cada tarefa deve ter uma responsabilidade clara.
3. Cheque `read_first`: arquivos a editar, contratos e testes relevantes devem ser lidos antes.
4. Cheque acoes: rejeite verbos vagos como "alinhar", "melhorar" ou "ajustar" sem mudanca concreta.
5. Cheque aceite: cada criterio deve ser verificavel por teste, comportamento, comando ou evidencia.
6. Cheque dependencias e ordem: migrations, contratos e callers devem entrar em sequencia segura.
7. Cheque gates backend: API, dados, auth, security, dependencies, rollback e docs quando aplicavel.
8. Emita veredito e correcoes minimas para deixar o plano executavel.

## Saida obrigatoria
Preencha `../../templates/plan-quality-report.md` com veredito, achados, gates ausentes, revisao sugerida e verificacao recomendada.

## Criterios de aceite
- Achados aparecem antes do resumo.
- Cada blocker/high tem evidencia no plano ou lacuna concreta.
- Nao exigir burocracia para tarefa de baixo risco.
- O resultado diz exatamente o que editar no plano.

## Arquivos de apoio
- Template: ../../templates/plan-quality-report.md
- Padrao backend: ../../templates/backend-slice-plan.md
- Rubric de testes: ../../rubrics/testing.md
- API: ../../rubrics/api-contract.md
- Dados: ../../rubrics/data-migration.md

## Exemplos de uso
- Codex: `$plan-quality-checker Audite este plano backend antes de executar.`
- Claude Code: `/plan-quality-checker Encontre tarefas vagas e gates ausentes neste plano.`
