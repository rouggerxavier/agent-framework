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
