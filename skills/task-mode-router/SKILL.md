---
name: task-mode-router
description: Use para escolher o peso certo de execucao de uma tarefa: fast, quick, full ou audit, evitando processo caro quando uma rota leve basta.
---

# Task Mode Router

## Objetivo
Escolher rapidamente o modo de trabalho proporcional ao risco, tamanho e incerteza da tarefa, antes de acionar skills mais caras em contexto, tempo ou coordenacao.

## Quando usar
- No inicio de uma tarefa de codigo, backend, bugfix, refatoracao, auditoria ou release.
- Quando nao esta claro se basta agir direto ou se precisa planejar.
- Quando o usuario quer resultado parecido com GSD, mas sem overhead excessivo.
- Antes de chamar `workflow-orchestrator` para confirmar se a tarefa realmente precisa de orquestracao.

## Quando nao usar
- Quando o usuario pediu explicitamente uma skill especifica.
- Para tarefa puramente conversacional sem acao em repo, arquivo ou processo.
- Quando a tarefa ja esta classificada por risco alto evidente; va direto para `full`.

## Entradas esperadas
- Pedido do usuario.
- Contexto do repo, se ja carregado.
- Risco aparente: contratos, dados, auth, billing, migration, infra, concorrencia ou dependencia externa.
- Numero aproximado de arquivos, areas e comandos envolvidos.

## Workflow
1. Classifique a tarefa por risco e incerteza, sem ler o repo inteiro.
2. Escolha um modo:
   - `fast`: edicao trivial, escopo obvio, ate 3 arquivos, sem contrato ou teste complexo.
   - `quick`: bugfix ou feature pequena, poucos arquivos, precisa ler contexto local e validar.
   - `full`: backend complexo, API publica, dados, auth, migration, filas, integracao, concorrencia, release ou multiplas fases.
   - `audit`: pedido e revisar, verificar, comparar, liberar ou encontrar risco sem implementar.
3. Liste as skills recomendadas para o modo escolhido.
4. Defina a verificacao minima esperada.
5. Se houver duvida entre dois modos, escolha o mais leve que preserve o risco principal; escale se aparecer evidencia nova.

## Saida obrigatoria
- Modo escolhido: `fast`, `quick`, `full` ou `audit`.
- Justificativa em 1-3 frases.
- Skills a usar agora, no maximo 3.
- Verificacao minima: comando, teste, auditoria ou motivo para nao executar.
- Condicao de escalada para um modo mais pesado.

## Criterios de aceite
- Nao acionar `workflow-orchestrator` para tarefa pequena.
- Nao classificar como `fast` se tocar auth, dados persistidos, API publica, migration, billing ou seguranca.
- `full` deve produzir plano com fases, riscos e criterios de passagem.
- `audit` deve priorizar findings e evidencia, nao resumo longo.

## Arquivos de apoio
- Router geral: ../../skills/agent-framework-router/SKILL.md
- Plano backend: ../../skills/backend-slice-planner/SKILL.md
- Qualidade do plano: ../../skills/plan-quality-checker/SKILL.md
- Cobertura final: ../../skills/goal-coverage-verifier/SKILL.md
- Plano completo: ../../skills/workflow-orchestrator/SKILL.md
- Revisao: ../../skills/diff-reviewer/SKILL.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Backend/API: ../../skills/api-contract-auditor/SKILL.md

## Exemplos de uso
- Codex: `$task-mode-router Classifique esta tarefa e diga qual skill usar primeiro.`
- Claude Code: `/task-mode-router Isto precisa de fluxo completo ou posso resolver rapido?`
