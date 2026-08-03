# Review Application Workflow

Use para registrar formalmente o veredito de uma revisao independente nos gates
`spec_compliance` e `code_quality`, incluindo o retorno a correcao quando a
revisao encontra algo.

## Quando usar

- `next_action` e `run-spec-review -> <ID>` ou `run-quality-review -> <ID>`.
- A fase esta em `reviewing` e a tarefa tambem.
- O relatorio de revisao ja existe como documento na fase ativa.

## Quando nao usar

- Gate sem revisao: `gate-status` recusa os dois gates de propósito.
- Contrato mudou: use `amend-plan` e veja
  `workflows/ci-contract-correction.md`. Correcao de codigo que nao altera o
  contrato **nao** e emenda.
- Fase fora de `reviewing`: a revisao descreve trabalho sob revisao.

## Escritores formais

| Gate | Escritor | Recusado por |
| --- | --- | --- |
| `spec_compliance` | `framework-next validate-spec-review` | `gate-status` |
| `code_quality` | `framework-next validate-quality-review` | `gate-status` |

Nao existe segundo escritor, e validar e aplicar sao **um ato so**. Um estado
durável em que a revisao foi validada mas nao registrada e a mesma meia-verdade
que o framework recusa em todo lugar.

## Sequencia

1. Confirme a operacao com `framework-next validate` e o `next_action`.
2. Escreva o relatorio de spec review na fase ativa. Ele precisa carregar
   `task_id`, `phase`, `plan_revision`, `reviewed_commit`, `branch`,
   `reviewer`, `classification`, `diff_inspected`, `files_inspected`,
   `evidence_inspected` e a tabela de `acceptance`.
3. Aplique a spec review:

```bash
framework-next validate-spec-review \
  --contract .agent/phases/<slug>/TASKS.md --task-id <ID> \
  --result .agent/phases/<slug>/<ID>-result.md \
  --review .agent/phases/<slug>/<ID>-spec-review.md \
  --actor <quem-aplica>
```

Use `--check` para rodar todos os guards **sem escrever nada**.

4. Com `spec_compliance` aprovado, aplique a quality review:

```bash
framework-next validate-quality-review \
  --result .agent/phases/<slug>/<ID>-result.md \
  --spec-review .agent/phases/<slug>/<ID>-spec-review.md \
  --review .agent/phases/<slug>/<ID>-quality-review.md \
  --actor <quem-aplica>
```

5. Rode `validate` e confirme `state: valid`.
6. Faca a transicao, que continua sendo um ato deliberado:

```bash
framework-next transition --to verifying \
  --actor workflow-runner --reason "both reviews applied"
```

## Classificacoes

`PASS → passed`, `PASS_WITH_NOTES → passed_with_notes`, `BLOCKED → blocked`;
`APPROVED → approved`, `APPROVED_WITH_NOTES → approved_with_notes`,
`CHANGES_REQUIRED → changes_required`. **Nao existe `REJECTED`**: a rejeicao
deste framework e `CHANGES_REQUIRED`.

Uma revisao aprovadora nao pode carregar um achado com `required_change`. Se
existe mudanca exigida, a classificacao e `CHANGES_REQUIRED`. Notas sem mudanca
exigida sao legais — e para isso que serve `APPROVED_WITH_NOTES`.

## O que a aplicacao faz

Numa unica operacao: registra o gate, escreve o `gate_record` carimbado com a
`plan_revision`, anexa a entrada em `REVIEW.md`, registra o evento no ledger da
fase, atualiza `next_action` e — so na aprovacao de qualidade — move a tarefa
para `reviewed` no indice.

`reviewed` e o que torna `reviewing → verifying` alcancavel: nao existe aresta
`reviewing → verifying` em `TASK_STATUS_TRANSITIONS`.

A aplicacao **nunca** move o ciclo de vida. Depois da spec review, fase e tarefa
continuam em `reviewing`, `code_quality` continua `pending` e a proxima operacao
e `run-quality-review`. Depois da quality review aprovada, a fase continua em
`reviewing` e a proxima operacao e `verify-phase`.

## Pre-condicoes que recusam

- reviewer igual ao executor do resultado;
- `diff_inspected` diferente de `true`, `files_inspected` ou
  `evidence_inspected` vazios;
- relatorio de outra tarefa, de outra fase ou de outro documento de fase;
- `plan_revision` ausente ou diferente da revisao atual do plano;
- `reviewed_commit` diferente de `HEAD`;
- `HEAD` destacado, branch diferente da branch vinculada, ou arvore de trabalho
  com mudancas de produto que o reviewer nao leu (`.agent/` e ignorado);
- quality review antes da spec review passar, ou apontando para um documento de
  spec diferente do que foi aplicado — inclusive se ele foi editado depois;
- spec review depois da quality review ja ter aprovado;
- estado com erros de `validate`: uma revisao julga trabalho, nao conserta
  estado;
- ausencia de `--actor`.

Recusa nao escreve nada.

## CHANGES_REQUIRED

1. A spec review passa.
2. A quality review encontra um achado e classifica `CHANGES_REQUIRED`.
3. O gate registra `changes_required`, o achado vira blocker com evidencia,
   `next_action` aponta `return-to-execution` — e a transicao **nao** acontece.
4. `transition --to executing` devolve a tarefa a correcao. O binding atravessa
   intacto; a `plan_revision` **nao** muda.
5. Os cinco gates de revisao sao reabertos: nenhuma aprovacao e herdada.
6. Feita a correcao, `task-status --to implementation_complete`, self review, e
   `transition --to reviewing`.
7. As duas revisoes sao pagas de novo, com reviewers independentes.
8. A quality review que aprova o trabalho corrigido fecha o blocker que ela
   mesma abriu. A revisao anterior permanece em `history` como registro do
   achado — **ela nao e apagada**.
9. `code_quality` fica `approved`, a tarefa fica `reviewed`, e
   `reviewing → verifying` abre.

## Revisoes e revisao do plano

Todo record e carimbado com a `plan_revision` sob a qual foi concedido. Depois
de `amend-plan`, a aprovacao antiga vira historico carimbado e uma revisao da
v1 e recusada contra a v2 — a revisao tem que ser refeita contra o contrato que
o reviewer realmente leu.

Records legados sem carimbo continuam legiveis e nunca contam como aplicacao.

## Repeticao

Repetir a mesma aplicacao e no-op: nao duplica evento, nao cria record, nao
muda timestamp. Repetir com outro relatorio, resultado, reviewer, commit,
branch ou revisao e recusado — inclusive quando o relatorio foi editado depois
de aplicado, porque o digest do documento faz parte da identidade.

## Atomicidade

Quatro documentos se movem juntos, nesta ordem: ledger, `REVIEW.md`,
`TASKS.md`, `STATE.md`. Falha em qualquer etapa restaura os quatro byte a byte.
Se o processo morrer entre duas escritas, o resultado seguro e o registrado:
ledger e entrada de review sem o gate descrevem uma revisao que nao teve efeito,
`validate` fica limpo, o gate continua bloqueando e o comando e simplesmente
rodado de novo.

## Saidas

- Gate registrado com record coerente e carimbado.
- `validate` limpo.
- Proxima operacao calculada pelo kernel.
