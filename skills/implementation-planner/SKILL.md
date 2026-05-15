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
1. Resuma objetivo e limites.
2. Identifique arquivos, modulos e contratos afetados.
3. Divida em fases pequenas e ordenadas.
4. Defina testes e verificacoes por fase.
5. Liste riscos, mitigacoes e rollback.

## Saida obrigatoria
- Plano por fases.
- Escopo de arquivos ou modulos.
- Criterios de aceite.
- Testes e comandos de verificacao.
- Riscos, mitigacoes e rollback.

## Criterios de aceite
- Cada fase deve deixar o projeto coerente.
- O plano deve evitar refatoracao lateral.
- Verificacao deve ser proporcional ao risco.
- Dependencias bloqueantes devem estar explicitas.

## Exemplos de uso
- Codex: `$implementation-planner Planeje a implementacao de billing em fases.`
- Claude Code: `/implementation-planner Quebre esta refatoracao em passos seguros.`
