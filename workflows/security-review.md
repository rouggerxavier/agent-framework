# Security Review Workflow

Use para decidir quando a revisao de seguranca e obrigatoria, qual auditor
chamar e o que precisa existir antes de integrar.

Seguranca aqui nao e um modo. E um eixo separado: `fast`, `standard` e
`critical` continuam definindo o peso do processo, e esta tabela define se um
auditor entra e qual.

## Gatilhos obrigatorios

Se o diff toca qualquer linha abaixo, o auditor correspondente e obrigatorio no
modo em vigor. Sem ele, o gate de review nao fecha.

| Gatilho no diff | Auditor obrigatorio |
| --- | --- |
| Query montada em codigo, comando de SO, parser XML/YAML, template, deserializacao, requisicao HTTP com URL variavel, redirect por parametro, bind de payload em modelo | `injection-vulnerability-auditor` |
| Render de conteudo vindo do usuario em HTML, atributo ou script | `injection-vulnerability-auditor` |
| Login, token, JWT, sessao, cookie de auth, middleware de permissao, papel/role, endpoint que recebe id de recurso, mutacao por cookie | `authn-authz-auditor` |
| Fluxo com dinheiro, saldo, cota, cupom ou etapas obrigatorias | `authn-authz-auditor` |
| Credencial, chave, certificado, hash de senha, cifra, assinatura, geracao de token, config de TLS | `crypto-secrets-auditor` |
| Dockerfile, compose, manifest k8s, helm, terraform, workflow de CI, CORS, headers, porta publicada, flag de debug | `infra-security-auditor` |
| Dependencia nova, upgrade de lib, mudanca de lockfile | `dependency-risk-auditor` |
| Prompt, tool, memoria de agente, model routing ou consumo de conteudo nao confiavel por agente | `agent-security-auditor` |
| Dado pessoal, financeiro ou confidencial em novo fluxo, log, export ou integracao | `security-privacy-audit` |
| Evento de seguranca sem rastro (login, falha de autorizacao, mudanca de permissao, operacao privilegiada) | `feature-logging-planner` |

Nada disso escala o modo por conta propria. Um gatilho torna o auditor
obrigatorio; escalar para `critical` continua sendo escolha explicita, conforme
`agent-framework-router`.

## Sequencia

1. Rode `./scripts/security-check` como primeira passada estatica e trate os
   `[fail]` antes de revisar a mao.
2. Selecione os auditores pela tabela; nao rode os quatro por reflexo.
3. Cada auditor entrega `templates/security-audit-report.md` com escopo e o que
   ficou de fora.
4. Consolide achados por severidade; `Critical` e `High` bloqueiam integracao.
5. Cada achado `Critical`/`High` vira correcao e teste negativo, nao apenas nota.
6. Reexecute a verificacao e registre a evidencia no gate de review
   (`code-review-gate`) ou no ledger, quando o modo for `critical`.

## Proporcionalidade por modo

- `fast`: auditor entra apenas se o gatilho aparecer; o relatorio pode ser a
  secao de achados, sem preencher o template inteiro.
- `standard`: relatorio completo do auditor disparado, integrado a review unica.
- `critical`: auditores rodam como reviewers independentes do executor, com
  evidencia no ledger e risco residual explicito.

## Gates

- Achado `Critical` ou `High` sem correcao bloqueia commit, PR e release.
- Segredo real exposto exige rotacao antes de qualquer merge; remover do codigo
  nao encerra o achado.
- Waiver exige dono nomeado, prazo e risco residual registrado.
- Ausencia de teste negativo em achado corrigido mantem o achado aberto.

## Saidas

- Relatorios de seguranca dos auditores disparados.
- Lista de achados com severidade, correcao e teste.
- Risco residual e waivers com dono.
- Evidencia de reexecucao das verificacoes.
