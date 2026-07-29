---
name: task-runner
description: Use para executar uma unica tarefa por contrato integral, aplicar testes obrigatorios, limitar arquivos, fazer self-review e retornar implementation_complete com evidencias.
---

# Task Runner

## Objetivo

Implementar exatamente uma tarefa autorizada e produzir um resultado estruturado
que o runner e reviewers possam validar sem confiar em resumo.

## Quando usar

- Depois de `workflow-runner` selecionar uma tarefa elegivel.
- Ao retomar uma tarefa `executing` com contrato e commit inicial validos.
- Em contexto limpo, quando o pacote integral da tarefa foi recebido.

## Quando nao usar

- Sem contrato completo ou com dependencia pendente.
- Para alterar plano, spec, lifecycle ou arquivos fora de escopo.
- Para marcar trabalho `reviewed`, `verified` ou concluido.

## Entradas esperadas

- Contrato integral, nao apenas caminho para ele.
- Contexto/spec/decisoes relevantes, estado atual e commit inicial.
- Politicas de teste/evidencia, arquivos e resultados anteriores aplicaveis.

## Workflow

1. Valide o contrato com `scripts/framework-next validate-task`; pare em qualquer
   erro, dependencia, conflito de Git ou contexto stale.
2. Leia todos os `read_first` e confirme objetivo, invariantes e limites.
3. Aplique `kernel/test-policy.yaml`: RED primeiro para regra/regressao,
   characterization-first para legado e gates especificos para contrato,
   migration, integracao, UI ou config.
4. Registre comandos e falhas; retry somente conforme a politica.
5. Implemente apenas `allowed_files`. Necessidade externa interrompe e solicita
   revisao do contrato/plano.
6. Rode testes e runtime checks requeridos.
7. Inspecione o diff completo e preencha todo o self-review.
8. Preencha `templates/task-result.md` com evidencia por criterio.
9. Rode `validate-result`; registre resultado/falhas em `EVIDENCE.md`.
10. Retorne `implementation_complete`; o runner, nao o executor, aplica
    `framework-next task-status` e encaminha ao review.

## Saida obrigatoria

- Resultado estruturado completo.
- Arquivos criados, modificados e removidos.
- Comandos, estagios, resultados e logs.
- Evidencia por criterio, desvios, riscos e self-review.
- Status maximo `implementation_complete`.

## Criterios de aceite

- Dependencias satisfeitas e todos os `read_first` lidos.
- Nenhum arquivo fora do contrato ou expansao silenciosa.
- Politica de testes ou waiver valido possui evidencia.
- Self-review completo nao substitui os dois reviewers.

## Arquivos de apoio

- Execucao: ../../kernel/execution-policy.md
- Testes: ../../kernel/test-policy.yaml
- Evidencia: ../../kernel/evidence-policy.md
- Resultado: ../../templates/task-result.md

## Exemplos de uso

- Codex: `$task-runner Execute este contrato integral e retorne implementation_complete.`
- Claude Code: `/task-runner Retome a tarefa ativa sem expandir o escopo.`
