---
name: integration-batch-manager
description: Agrupa multiplos PRs candidatos em uma branch/worktree temporaria de integracao para validar conflitos e CI combinada antes de merges sequenciais.
---

# Integration Batch Manager

## Objetivo

Quando ha mais de um PR aberto ao mesmo tempo, reduzir espera e CI redundante
validando o conjunto candidato como uma arvore de integracao antes de merges
sequenciais.

## Trigger

Avalie um integration batch sempre que existirem **2 ou mais PRs abertos** do
mesmo projeto.

Crie o batch quando pelo menos dois PRs:

- estao prontos ou proximos de integrar;
- compartilham a mesma base de integracao;
- podem coexistir segundo dependencias e scopes;
- ganham valor real com teste combinado.

Nao force batch para PRs experimentais, mutuamente exclusivos ou claramente
distantes de merge.

## Batch shape

Use uma branch/worktree efemera, por exemplo:

`integration/<run-id>/<batch-id>`

A partir da base atual:

1. ordene PRs por dependencias;
2. integre os heads candidatos na branch batch sem alterar os PRs;
3. resolva apenas conflitos mecanicos autorizados; conflito semantico volta para
   a lane dona;
4. rode o perfil de CI exigido pela **uniao** dos impactos;
5. registre exatamente quais PR heads/SHAs formam o batch.

## CI economy

The batch is an additional combined-integration proof, not magic permission to
ignore repository protection.

- If branch protection requires checks on each PR head, those required checks
  still run.
- Do not duplicate optional/full suites on every PR when one batch run safely
  covers the combined tree.
- Cancel superseded/non-authoritative runs when repository policy permits.
- Rebuild the batch when any included PR head changes.
- A green batch applies only to the exact ordered set of included SHAs.

## Merge sequence

After a green batch:

1. merge PRs in dependency order;
2. after each merge, confirm the remaining batch tree is still equivalent to the
   validated composition;
3. if merge strategy/base movement changes the tree materially, rerun affected
   checks or rebuild the batch;
4. observe main according to the CI throughput policy.

Do not claim that a batch proves an individual PR head check that GitHub or the
repository explicitly requires.

## When batch fails

Classify the failure:

- merge conflict between PRs;
- combined behavioral regression;
- flaky/infrastructure failure;
- one PR independently failing.

Route the smallest actionable failure back to its owner. Other independent work
continues.

## Notebook/state

Record:

- batch id;
- branch;
- base SHA;
- included PRs + exact head SHAs;
- CI profile and result;
- exclusion/rebuild reason;
- integration order.

Remove the ephemeral worktree/branch after all included PRs integrate or the
batch is abandoned.
