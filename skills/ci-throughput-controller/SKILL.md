---
name: ci-throughput-controller
description: "Use para escolher perfil de CI (minimal/targeted/full), decidir esperar ou seguir, classificar a proxima unidade (independente/stacked/wait) e tratar contencao de runner compartilhado."
---

# CI Throughput Controller

## Objetivo
Decidir quais gates a mudanca deve e o que pode acontecer enquanto eles rodam.
CI bloqueia integracao, nao desenvolvimento continuo.

## Quando usar
- Ao abrir PR, empurrar branch ou planejar a proxima unidade com CI pendente.
- Quando a mudanca tem impacto claro: docs, frontend, backend, contratos, banco,
  security core, E2E ou release.
- Quando o runner self-hosted divide maquina com o desenvolvimento.
- Quando alguem pergunta se pode continuar antes do CI ficar verde.

## Quando nao usar
- Para escolher `fast`/`standard`/`critical`: use `agent-framework-router`.
- Para escolher commit/branch/PR: use `git-decision-router`.
- Para mapear comandos reais do repo por nivel: use `test-confidence-mapper`.
- Para decidir profundidade de review: use `code-review-gate`.

## Entradas esperadas
Contexto operacional entra como dado, nunca como texto ambiguo no pedido:
`scripts/agent-framework-route --ci-context-json '{...}'` ou as flags
`--runner-kind`, `--remote-ci-running`, `--next-unit`, `--unit-merged`,
`--merge-tree-validated`, `--main-status`, `--release-in-flight`,
`--deploy-in-flight`, `--ci-profile`, `--local-workload`, `--unit-ref`.
Campo ausente usa o default documentado; nada e inventado.

- Diff ou escopo da mudanca e modo de execucao ja selecionado.
- Impactos: docs, metadata, refactor mecanico, frontend, backend, contracts,
  database, security_core, e2e_relevant, release.
- Runner: `hosted`, `self_hosted_dedicated`, `self_hosted_shared` ou `unknown`,
  e se ha run remoto em execucao.
- Proxima unidade planejada e se ela depende desta PR.
- Se ha release/deploy em andamento ou dependencia externa.

## Workflow
1. Classifique impactos da mudanca; nao assuma pipeline completo por uniformidade.
2. Escolha `ci_profile`: `minimal` sem comportamento executavel, `full` para
   migration, security core, release, blast radius amplo, irreversivel ou modo
   `critical`, `targeted` para o resto.
3. Selecione gates por impacto e separe `local_gates`, `remote_gates` e
   `deferred_gates` — nomeando onde o gate adiado roda de fato.
4. Separe os dois eixos. `ci_blocking_point` diz onde a integracao e barrada
   (`before_merge` quase sempre); `ci_wait_policy` diz o que o agente faz agora.
   Perfil `full` levanta `publication_hold`, nao espera: com trabalho seguro
   disponivel, a wait policy continua `background`. `blocking_now` exige uma das
   razoes nomeadas — release/deploy ativo, resultado muda a proxima decisao,
   dependencia externa, risco critico proibindo trabalho especulativo. "CI ainda
   rodando", perfil `full` e modo `critical` nao sao razoes.
5. Classifique a proxima unidade: `continue_independent`, `stack_local` ou
   `wait`. Em `stack_local`, branch local a partir da HEAD pendente, sem publicar
   PR dependente antes da pai integrar; depois do merge, rebase e so entao valide.
6. Aplique politica de runner compartilhado: trabalho leve liberado, carga pesada
   em espera; nao leia contencao como instabilidade.
7. Separe merge gate da PR de observacao pos-merge em `main`; main vermelho e
   incidente a investigar.
8. Recomende `concurrency` + `cancel-in-progress` para runs superados; SHA
   superada nao e gate.
9. Depois do verde, prefira auditoria incremental quando HEAD, escopo e gates
   anteriores nao mudaram.
10. Reporte os tres bloqueios em linhas separadas: `MERGE BLOCKER`,
    `NEXT-WORK BLOCKER`, `POST-MERGE OBSERVATION`.

## Saida obrigatoria
Preencha `../../templates/ci-throughput-decision.md` com perfil, gates, wait
policy, next-work policy, runner policy, blockers e observacao pos-merge.

Referencia executavel: `kernel/runtime/ci_policy.py`
(`ci_decision`, `select_ci_profile`, `select_wait_policy`, `classify_next_work`,
`runner_policy`, `post_merge_observation`).

## Criterios de aceite
- Nao transformar `standard` em pipeline completo automaticamente.
- Nao mandar esperar CI sem nomear o motivo do `blocking_now`.
- Gate adiado sempre declara onde roda (nightly, release, perfil full).
- Caminho critico de usuario nunca e enfraquecido em silencio.
- Distinguir merge blocker, next-work blocker e observacao pos-merge.
- Nao exigir runner hospedado; o tipo de runner e capability do executor.
- Nunca derivar `blocking_now` de perfil, modo ou "CI rodando".
- Nao confundir "nao pode mergear" com "nao pode continuar trabalhando".
- Gate kind e abstrato; binding para comandos reais fica em repo, nao aqui.

## Arquivos de apoio
- Politica: ../../kernel/ci-throughput-policy.md
- Workflow: ../../workflows/ci-throughput.md
- Template: ../../templates/ci-throughput-decision.md
- Comandos por nivel: ../../skills/test-confidence-mapper/SKILL.md
- Git/PR: ../../skills/git-decision-router/SKILL.md
- Contrato reprovado por CI: ../../workflows/ci-contract-correction.md

## Exemplos de uso
- Codex: `$ci-throughput-controller Posso comecar a proxima unidade com esta PR em CI?`
- Claude Code: `/ci-throughput-controller Escolha o perfil de CI para este diff de frontend.`
