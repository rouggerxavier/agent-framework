---
name: execution-plan-builder
description: Use para criar brief, documentacao enxuta, plano de execucao ou organizacao de feature, refatoracao, bugfix amplo, melhoria, migracao ou tarefa delegavel antes de codar.
---

# Execution Plan Builder

## Objetivo
Transformar uma ideia, pedido cru ou decisao em um brief operacional e, quando o
kernel estiver ativo, alimentar `workflow-planner` com tarefas verificaveis.

## Quando usar
- Quando o usuario pedir "brief", "documentacao", "plano de execucao", "organizar isso", "quebrar em etapas" ou "preparar para outro agente".
- Antes de delegar feature, refatoracao, bugfix amplo, migracao, auditoria ou melhoria multi-arquivo.
- Quando o objetivo existe, mas a ordem de execucao, os limites e os gates ainda estao nebulosos.

## Quando nao usar
- Para escrever prompts finais por etapa; use `execution-prompt-builder` depois.
- Para planejar backend profundamente; use `backend-slice-planner` como apoio.
- Para executar codigo diretamente.

## Entradas esperadas
- Objetivo e contexto conhecido.
- Repositorio, produto, modulo ou area afetada quando houver.
- Restricoes, prazo, risco, stack, criterios de sucesso ou preferencias do usuario.
- Incertezas que precisam aparecer no plano.

## Workflow
Siga `../../workflows/execution-brief.md`. Especifico desta skill:
1. Reescreva o objetivo em uma frase e declare suposicoes.
2. Separe escopo incluido, fora de escopo e perguntas bloqueantes.
3. Escolha o caminho: feature, refatoracao, bugfix, organizacao, documentacao, auditoria ou migracao.
4. Divida em etapas pequenas, ordenadas e verificaveis.
5. Para cada etapa, defina entrada, acao, saida, areas provaveis, verificacao e criterio de done.
6. Liste riscos, dependencias, rollback e pontos onde `plan-quality-checker` deve revisar.
7. Para execucao persistente, converta cada etapa em contrato integral usando
   `templates/task-contract.md`; nao implemente a etapa.
8. Termine indicando `plan-quality-checker`, `workflow-planner` ou
   `execution-prompt-builder` conforme o consumidor.

## Saida obrigatoria
Preencha `../../templates/execution-plan.md` com:
- Brief curto.
- Escopo e nao escopo.
- Etapas numeradas.
- Verificacao por etapa.
- Riscos e dependencias.
- Perguntas abertas.
- Proximo passo recomendado.
- No kernel: entradas suficientes para `PLAN.md` e contratos em `TASKS.md`.

## Criterios de aceite
- O plano deve ser curto, executavel e sem verbos vagos.
- Cada etapa deve deixar um estado verificavel, nao apenas uma intencao.
- O plano deve preservar incertezas em vez de inventar contexto.
- Tarefas de alto risco devem apontar skills de apoio: `plan-quality-checker`, `test-strategy-builder`, `security-privacy-audit`, `api-contract-auditor` ou `data-migration-auditor`.
- Se a execucao sera delegada, recomendar `execution-prompt-builder`.
- O builder nao promove `planned`; somente `workflow-planner` apos o plan gate.
