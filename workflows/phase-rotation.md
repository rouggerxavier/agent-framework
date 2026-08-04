# Phase Rotation Workflow

Use para abrir uma fase que ja existe e ja esta contratada, depois que a fase
atual foi encerrada.

## Quando usar

- A proxima fase ja tem SPEC, PLAN, TASKS, EVIDENCE, REVIEW e HANDOFF em disco.
- A fase atual esta `shipped` ou `superseded`.
- Nenhuma tarefa da fase de destino foi executada.

## Quando nao usar

- Fase nova, sem diretorio: use `init-phase`.
- Trabalho da fase ja executado e commitado sem indice: use `reconcile-phase`.
- Fase atual ainda em `ready_to_ship`: pague o gate de release e feche primeiro,
  senao a decisao de shipping fica orfa.

## Sequencia

1. Feche a fase atual: `gate-status --gate release --to passed`, depois
   `transition --to shipped`. Ver `workflows/release.md`.
2. Confirme que a fase de destino aparece no `ROADMAP.md`.
3. Rode a rotacao:

```bash
framework-next activate-phase \
  --id U3 --name "Onboarding e setup" \
  --slug u3-membership-onboarding \
  --actor planner \
  --reason "U2 encerrada; U3 ja contratada"
```

4. Rode `validate` e confirme `state: valid`.
5. Siga a operacao que o kernel devolver.

## Onde a rotacao aterrissa

| Plano da fase de destino | Estado | Proxima operacao |
| --- | --- | --- |
| nao selado | `specified` | `build-plan`, depois `seal-plan` |
| selado, fingerprint confere | `planned` | `execute-task` na primeira tarefa elegivel |

O plano so conta como selado quando o fingerprint armazenado, recalculado contra
a fase que esta sendo ativada, ainda confere. Qualquer outro caso e plano nao
selado: `plan_revision` e zerado e o gate de plano e pago de novo. Ativar uma
fase nunca produz `execute-task` prematuro.

## Gates que a rotacao reabre

Um gate julga o trabalho de **uma** fase. A rotacao reabre em `pending` os cinco
gates de review (`self_review`, `spec_compliance`, `code_quality`, `acceptance`,
`verification`) e o gate de `release`, e a fase ativada comeca a pagar os seus.

`release` e o caso critico. Ele guarda `ready_to_ship -> shipped`: herdado, a
fase nova nasce ja `passed` com evidencia apontando para o diretorio da fase
anterior — e nunca conseguiria registrar o proprio veredito, porque
`GATE_TRANSITIONS` nao tem aresta de `passed` para `passed`.

O record anterior nao e reaproveitado nem descartado. No gate fica um record
`pending` da fase agora ativa, carimbado com a revisao dela; o veredito da fase
encerrada vai para `history` com o campo `phase` nomeando a fase que ele julgou.

`specification` e `plan_quality` nao sao reabertos, pela mesma razao que
`amend-plan` os preserva: a rotacao aterrissa em `specified` justamente porque o
SPEC da fase de destino existe, e `plan_quality` e o que `specified -> planned` e
`planned -> executing` exigem. Quem cobra o plano da fase ativada e o selo — o
fingerprint e zerado a menos que descreva de fato a fase agora ativa.
`waivers` e um registro, nao um julgamento sobre a fase.

A fase encerrada entra em `completed_phases` na propria rotacao, com id, nome,
status, indice de tarefas e `closed_at`. Ninguem edita esse registro a mao.

Depois de selar, `specified -> planned` e uma transicao normal:

```bash
framework-next seal-plan --version 1 --decision D-044 \
  --evidence ".agent/phases/<slug>/EVIDENCE.md#plan-gate" --actor planner
framework-next transition --to planned --actor planner --reason "plan gate passed"
```

## Pre-condicoes que recusam

- fase atual nao esta `shipped` nem `superseded`;
- fase de destino ja e a ativa;
- diretorio ou algum dos seis artefatos ausente;
- fase ausente do `ROADMAP.md`;
- alguma tarefa em `executing`, `reviewing`, `verifying` ou `verified`;
- indice de tarefas malformado ou com dependencia pendente;
- blocker de lifecycle aberto.

Recusa nao escreve nada: estado e ledger ficam intactos.

## Saidas

- Fase anterior preservada e registrada em `completed_phases`.
- Fase de destino ativa, com artefatos reapontados.
- Nenhuma tarefa marcada como executada.
- Proxima operacao calculada pelo kernel.
