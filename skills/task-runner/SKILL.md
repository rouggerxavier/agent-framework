---
name: task-runner
description: Use para executar uma tarefa com escopo proporcional; contrato e evidencia formais sao obrigatorios apenas em critical.
---

# Task Runner

## Objetivo

Implementar uma tarefa no escopo autorizado, com verificacao e self-review
proporcionais ao modo.

## Quando usar

- Diretamente em `fast`, sem contrato formal.
- Em `standard`, com objetivo/plano e contrato leve opcional.
- Em `critical`, depois de `workflow-runner` selecionar contrato elegivel.

## Quando nao usar

- Para alterar plano, spec, lifecycle ou arquivos fora de escopo.
- Para marcar trabalho `reviewed`, `verified` ou concluido.
- Em `critical`, sem contrato completo ou com dependencia pendente.

## Entradas esperadas

- Sempre: modo, objetivo, arquivos relevantes, comportamento esperado e testes.
- `standard`: plano/contrato leve quando existir.
- `critical`: contrato integral, spec/decisoes, estado, commit e politicas.

## Workflow

1. Leia os arquivos relevantes e confirme objetivo, invariantes e limites.
2. Aplique `kernel/test-policy.yaml` proporcionalmente e registre comandos.
3. Implemente apenas o escopo; rode testes direcionados/proporcionais.
4. Inspecione o diff e faca self-review integrado.
5. Em `fast`, retorne arquivos, testes, resultado e riscos; nao crie contrato,
   spec, ledger ou task result formal.
6. Em `standard`, use contrato/resultados leves somente se agregarem valor e
   encaminhe uma revisao integrada.
7. Em `critical`, valide contrato, dependencias e contexto; limite
   `allowed_files`; preencha `task-result`, valide resultado, registre no ledger e
   retorne no maximo `implementation_complete`.

## Saida obrigatoria

- Sempre: mudancas, comandos/resultados, self-review e riscos.
- `fast`/`standard`: retorno conciso proporcional.
- `critical`: resultado estruturado, evidencia por criterio e status maximo
  `implementation_complete`.

## Criterios de aceite

- Nenhuma expansao silenciosa e alguma evidencia antes de declarar sucesso.
- `fast` exige teste direcionado e diff review, nao contrato.
- `standard` exige testes e review integrado, nao reviewers separados.
- `critical` preserva contrato, waiver, ledger e dois reviewers.

## Arquivos de apoio

- Execucao: ../../kernel/execution-policy.md
- Testes: ../../kernel/test-policy.yaml
- Evidencia: ../../kernel/evidence-policy.md
- Resultado: ../../templates/task-result.md

## Exemplos de uso

- Codex: `$task-runner Execute este contrato integral e retorne implementation_complete.`
- Claude Code: `/task-runner Retome a tarefa ativa sem expandir o escopo.`
