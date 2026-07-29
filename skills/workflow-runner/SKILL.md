---
name: workflow-runner
description: Use para coordenar plano leve em standard ou a maquina de estados completa em critical; nao e necessario em fast.
---

# Workflow Runner

## Objetivo

Coordenar execucao proporcional: plano leve em `standard` ou fase persistente
completa em `critical`.

## Quando usar

- Em `standard`, quando um plano curto tem etapas dependentes.
- Em `critical`, nos estados `planned`, `executing`, `reviewing`, `verifying` ou
  `blocked`.
- Para retomar estado persistente existente respeitando `execution_mode`.

## Quando nao usar

- Para decidir requisitos ou arquitetura ainda aberta.
- Para implementar diretamente o conteudo de uma tarefa.
- Em `fast`, salvo pedido explicito.

## Entradas esperadas

- Modo e plano selecionados.
- `standard`: plano curto, diff/contexto focado e verificacao.
- `critical`: `STATE.md`, contratos, evidencia, Git e gates.

## Workflow

1. Confirme o `execution_mode` do router ou de `STATE.md`.
2. Em `standard`, coordene os passos do plano curto, use `task-runner` sem
   contrato formal quando adequado, registre resultados no proprio plano/retorno
   e finalize com uma revisao integrada.
3. Em `standard`, nao aplique plan seal, ledger completo, transicoes formais ou
   reviewers separados.
4. Em `critical`, use `framework-next`, valide estado/Git/contratos, selecione a
   tarefa elegivel, acione `task-runner` e registre resultado no ledger.
5. Em `critical`, preserve self-review → spec compliance → code quality →
   goal coverage/runtime, com transicoes guardadas e plan revision formal.
6. Depois de correcao localizada, revise apenas novo diff, criterios afetados e
   regressoes relacionadas, salvo mudanca material de escopo.

## Saida obrigatoria

- `standard`: proximo passo, resultados, testes e review integrado.
- `critical`: operacao, pacote, evidencia, reviews independentes, transicao e
  proxima operacao.

## Criterios de aceite

- `standard` permanece leve e nao simula lifecycle formal.
- `critical` preserva separacao de autoridade, contratos e evidencia.
- `fast` nao depende deste runner.

## Arquivos de apoio

- Protocolo: ../../kernel/protocol.md
- Delegacao: ../../kernel/delegation-policy.md
- Evidencia: ../../kernel/evidence-policy.md
- Retomada: ../../skills/framework-next/SKILL.md

## Exemplos de uso

- Codex: `$workflow-runner Execute a proxima tarefa elegivel desta fase.`
- Claude Code: `/workflow-runner Retome o workflow pelo STATE.md.`
