---
name: workflow-runner
description: Use para executar um plano persistente pelo STATE.md, selecionar tarefa elegivel, acionar executor e reviews, registrar evidencias e aplicar somente transicoes permitidas.
---

# Workflow Runner

## Objetivo

Ser o unico controlador da execucao de uma fase, consumindo o plano aprovado sem
redesenha-lo livremente.

## Quando usar

- Nos estados `planned`, `executing`, `reviewing`, `verifying` ou `blocked`.
- Para retomar uma fase apos interrupcao, falha, review ou troca de agente.
- Quando tarefas e reviewers precisam de contexto limpo e limitado.

## Quando nao usar

- Para decidir requisitos ou arquitetura ainda aberta.
- Para implementar diretamente o conteudo de uma tarefa.
- Para aprovar evidencia, review ou verificacao do proprio executor.

## Entradas esperadas

- `STATE.md` valido e artefatos referenciados.
- Plano aprovado, contratos integrais, evidencia e estado do Git.
- Politicas do kernel e gates selecionados pelo planner.

## Workflow

1. Use `framework-next` e aceite somente a operacao unica retornada.
2. Valide estado, contexto/Git, dependencias, contrato e conflitos.
3. Selecione a primeira tarefa elegivel e monte o pacote definido pela politica
   de delegacao.
4. Acione `task-runner`; registre resultado e falhas no ledger.
5. Depois de validar resultado, use `framework-next task-status` para registrar
   `implementation_complete`; exija self-review antes de `executing → reviewing`.
6. Acione primeiro `spec-compliance-reviewer`, depois
   `code-quality-reviewer`; reviewers inspecionam codigo e evidencia diretamente.
7. Em blocker, registre evidencia e retorne a `executing` ou `blocked`.
8. Depois das aprovacoes, use `goal-coverage-verifier` e verificacao de runtime.
9. Atualize estado somente por transicoes permitidas e determine novamente a
   unica proxima operacao.
10. Sincronize status do contrato e `current_task`; depois de verificar uma
    tarefa, selecione a proxima elegivel ou inicie verificacao da fase.
11. Revisoes do plano voltam a `specified`, registram decisao e repetem o plan gate.

## Saida obrigatoria

- Tarefa/operacao selecionada e pacote de contexto.
- Resultado validado e evidencia registrada.
- Reviews independentes e transicao aplicada ou blocker.
- Estado atualizado e uma unica proxima operacao.

## Criterios de aceite

- Uma tarefa ativa por executor.
- Nenhum conflito de arquivos ou contratos em paralelo.
- Implementador nao marca `reviewed` ou `verified`.
- Falha preserva evidencia e nunca avanca por inferencia.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Delegacao: ../../kernel/delegation-policy.md
- Evidencia: ../../kernel/evidence-policy.md
- Retomada: ../../skills/framework-next/SKILL.md

## Exemplos de uso

- Codex: `$workflow-runner Execute a proxima tarefa elegivel desta fase.`
- Claude Code: `/workflow-runner Retome o workflow pelo STATE.md.`
