---
name: implementation-planner
description: Use para transformar decisao, PRD ou especificacao em plano de implementacao por fases, arquivos, testes, riscos e aceite.
---

# Implementation Planner

## Objetivo
Criar plano incremental para implementar mudancas com baixo risco, verificacao clara e escopo controlado.

## Quando usar
- Antes de feature, bugfix complexo, refatoracao ou migracao.
- Quando ha decisao aprovada, mas falta ordem de execucao.
- Quando e preciso dividir trabalho em fases testaveis.

## Quando nao usar
- Para tarefas de uma linha com solucao obvia.
- Para substituir investigacao tecnica necessaria.
- Para planejar release final; use `release-verifier`.

## Entradas esperadas
- Objetivo implementavel.
- Repositorio, stack e areas impactadas.
- Requisitos, restricoes e criterios de aceite.
- Riscos ou dependencias conhecidas.

## Workflow
Para feature, siga `../../workflows/feature-build.md`. Especifico desta skill:
1. Resuma objetivo e limites; identifique arquivos/modulos/contratos.
2. Divida em fases pequenas, ordenadas, com teste por fase.
3. Liste riscos, mitigacoes e rollback.

## Saida obrigatoria
Preencha `../../templates/implementation-plan.md` (fases, escopo, aceite,
testes/comandos, riscos, rollback).

## Criterios de aceite
- Cada fase deixa o projeto coerente; sem refatoracao lateral.
- Verificacao proporcional ao risco; dependencias bloqueantes explicitas.
- Decisoes de arquitetura: rubric em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Workflow: ../../workflows/feature-build.md
- Rubric: ../../rubrics/architecture.md
- Template: ../../templates/implementation-plan.md

## Exemplos de uso
- Codex: `$implementation-planner Planeje a implementacao de billing em fases.`
- Claude Code: `/implementation-planner Quebre esta refatoracao em passos seguros.`
