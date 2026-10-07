---
name: integration-batch-manager
description: Use para agrupar multiplos PRs abertos em batches temporarios de integracao, validando a arvore combinada e reduzindo CI redundante antes dos merges.
---

# Integration Batch Manager

## Objetivo

Quando ha mais de um PR aberto ao mesmo tempo, reduzir espera e CI redundante
validando o conjunto candidato como uma arvore de integracao antes de merges
sequenciais.

## Trigger

Com **2 ou mais PRs abertos** do mesmo projeto, o orquestrador deve criar ou
atualizar um registro de integration batch.

O batch inventaria todos os PRs abertos. Para executar CI combinada, inclua o
maior conjunto compativel de heads que:

- compartilha a mesma base de integracao;
- pode coexistir segundo dependencias e scopes;
- nao e mutuamente exclusivo.

PRs ainda draft/experimentais podem ficar inventariados como `not_ready` sem
entrar na composicao executavel. PR incompatível deve ser separado em outro batch
ou marcado com motivo explicito; nunca some silenciosamente da fila.

## Batch shape

Use uma branch/worktree efemera, por exemplo:

`integration/<run-id>/<batch-id>`

Se os checks combinados do repositorio so disparam em evento `pull_request`,
abra um PR efemero de integration batch contra a base. Esse PR existe para
validacao combinada e nao substitui os PRs reais.

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
- all open PRs inventoried;
- branch and optional batch PR;
- base SHA;
- included PRs + exact head SHAs;
- excluded/not-ready PRs + reason;
- CI profile and result;
- exclusion/rebuild reason;
- integration order.

Remove the ephemeral worktree/branch/batch PR after all included PRs integrate
or the batch is abandoned. If 2+ PRs remain open afterwards, immediately create
or refresh the next batch record.

## Saida obrigatoria

- batch inventory de todos os PRs abertos;
- composicao executavel com base/head SHAs exatos;
- branch/worktree e batch PR quando necessario;
- perfil/resultado de CI combinada;
- ordem de merge e motivos de exclusao/rebuild.

## Criterios de aceite

- 2+ PRs abertos sempre geram/atualizam um batch inventory.
- CI combinada nunca e usada para fingir que required checks individuais passaram.
- Mudanca de qualquer SHA invalida o batch anterior.
- PR excluido permanece visivel com motivo.
- Falha combinada e roteada ao menor owner acionavel.
