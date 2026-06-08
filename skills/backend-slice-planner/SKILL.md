---
name: backend-slice-planner
description: Use para planejar fatias backend executaveis com read_first, contratos, dados, riscos, testes, rollback e aceite verificavel.
---

# Backend Slice Planner

## Objetivo
Transformar uma demanda backend em fatias pequenas, ordenadas e verificaveis, preservando contratos, dados e operacao sem carregar um fluxo GSD completo.

## Quando usar
- Para API, jobs, filas, workers, banco, auth, billing, integracoes ou regras de dominio.
- Quando `task-mode-router` escolher `quick` ou `full` para backend.
- Antes de implementar mudanca multi-arquivo ou com risco de contrato/dados.
- Quando um plano generico nao deixa claro o que ler, alterar e testar.

## Quando nao usar
- Para edicao trivial classificada como `fast`.
- Para decidir arquitetura ainda aberta; use `architecture-decision` primeiro.
- Para auditoria sem plano de implementacao; use `plan-quality-checker` ou `diff-reviewer`.

## Entradas esperadas
- Objetivo, contexto e restricoes.
- Mapa do repo ou arquivos provaveis, se conhecidos.
- Contratos afetados: endpoints, eventos, schemas, jobs, migrations ou clients.
- Comandos de teste/build disponiveis.

## Workflow
1. Declare objetivo e fora de escopo em uma frase cada.
2. Liste decisoes travadas e incertezas que bloqueiam execucao.
3. Defina `read_first`: arquivos, rotas, schemas, testes e docs que o executor deve ler antes de editar.
4. Divida em fatias pequenas, cada uma deixando o sistema coerente.
5. Para cada fatia, especifique:
   - arquivos provaveis;
   - contratos e dados afetados;
   - acao concreta;
   - verificacao minima;
   - aceite observavel.
6. Marque dependencias entre fatias e riscos de rollback.
7. Se houver API publica, dados persistidos, auth ou migration, inclua gate explicito de contrato/teste.

## Saida obrigatoria
Preencha `../../templates/backend-slice-plan.md` com objetivo, decisoes, `read_first`, fatias, testes, riscos, rollback e criterios de aceite.

## Criterios de aceite
- Cada fatia tem acao concreta e criterio verificavel.
- Nenhuma fatia mistura refatoracao lateral com mudanca funcional sem motivo.
- Contratos, migrations e rollback aparecem quando aplicavel.
- O plano e curto o bastante para executar sem replanejar do zero.

## Arquivos de apoio
- Template: ../../templates/backend-slice-plan.md
- API: ../../skills/api-contract-auditor/SKILL.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Dados: ../../rubrics/data-migration.md
- Arquitetura: ../../rubrics/architecture.md

## Exemplos de uso
- Codex: `$backend-slice-planner Planeje esta mudanca de API em fatias backend verificaveis.`
- Claude Code: `/backend-slice-planner Divida este worker + migration em passos seguros.`
