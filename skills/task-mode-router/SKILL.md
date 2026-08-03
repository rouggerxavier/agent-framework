---
name: task-mode-router
description: "Use para escolher fast, standard ou critical com standard como padrao, fast para trabalho curto e contido e critical somente para dano grave."
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
- Quando a tarefa ja esta classificada por risco critico evidente; va direto para `critical`.

## Entradas esperadas
- Pedido do usuario.
- Contexto do repo, se ja carregado.
- Risco aparente: contratos, dados, auth, billing, migration, infra, concorrencia ou dependencia externa.
- Numero aproximado de arquivos, areas e comandos envolvidos.

## Workflow
1. Classifique a tarefa aplicando os fatores nesta ordem: prejuizo potencial de
   uma falha, sensibilidade da area, reversibilidade, blast radius, complexidade
   e tamanho, tempo estimado. Nao leia o repo inteiro para isso.
2. Escolha um modo:
   - `standard`: **default**; a maioria das features medias e grandes. Plano
     curto, testes proporcionais e uma review integrada.
   - `fast`: trabalho curto e contido (~10 min, poucos arquivos, facil reversao);
     inspecao, implementacao, teste direcionado e diff review.
   - `critical`: um defeito causaria dano grave; kernel persistente completo.
3. Liste as skills recomendadas para o modo escolhido.
4. Defina a verificacao minima esperada.
5. Na duvida, escolha `standard`.
6. O tempo separa `fast` de `standard` e nada mais. Uma tarefa de varias horas
   continua `standard`; uma alteracao curta no nucleo de pagamentos ou
   autenticacao pode ser `critical`.
7. Aceite `--fast`, `--standard`, `--critical`, `--auto`. Sem flag use `auto`.
8. Preserve aliases legados apenas para compatibilidade: `quick → standard`,
   `full/audit → critical`.

## Saida obrigatoria
- Modo escolhido: `fast`, `standard` ou `critical`.
- Justificativa em 1-3 frases.
- Skills a usar agora, no maximo 3.
- Verificacao minima: comando, teste, auditoria ou motivo para nao executar.
- Condicao de escalada para um modo mais pesado.

## Criterios de aceite
- Nao acionar `workflow-orchestrator` para tarefa pequena.
- Backend/API simples pode ser `fast` ou `standard`.
- `critical` exige um caminho de dano grave nomeado, nao "parece arriscado".
- Feature grande, migration controlada, permissoes, dados financeiros, muitos
  testes ou muitos arquivos **nao** justificam `critical` por si.
- Trabalho enorme e acoplado que pode ser dividido vira `standard` apos a
  divisao; `critical` so quando dividir com seguranca nao for possivel.
- Escolha explicita so escala diante de dano grave, com a evidencia dita.
- O modo e por tarefa: uma fase pode misturar `fast`, `standard` e `critical`.

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
