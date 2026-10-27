---
name: agent-framework-router
description: Use primeiro em tarefa nova - escolhe fast, standard ou critical e a categoria (agentes de IA, software, testes, revisao, design, seguranca, infra, orquestracao) com poucos assets.
---

# Agent Framework Router

## Objetivo
Dado um pedido, selecionar explicitamente `fast`, `standard` ou `critical` e
apontar rapidamente os assets certos. Dispatcher leve, nao executor.

## Quando usar
- No inicio de uma nova tarefa.
- Para respeitar `--fast`, `--standard`, `--critical` ou `--auto`.
- Para combinar poucos assets sem transformar trabalho comum em governanca.

## Quando nao usar
- Escolha de modelo/agente: use `model-routing`.
- Skill alvo ja obvia: chame-a direto.
- Retomada explicitamente persistente: use `framework-next`.

## Workflow
1. Leia a escolha explicita: `--fast`, `--standard`, `--critical` ou `--auto`;
   sem flag, use `auto`.
2. Em `auto`, `standard` e o padrao. E o modo do desenvolvimento normal.
3. Escolha `fast` apenas com evidencia positiva de trabalho curto e contido:
   ~10 minutos, poucos arquivos, comportamento previsivel, baixo impacto, facil
   reversao, sem decisao arquitetural.
4. `critical` e sempre uma escolha explicita: so selecione com `--critical` ou
   com pedido claro do usuario. Recomende-o — nomeando o dano — quando um
   defeito causar dano grave: quebrar o
   nucleo de auth/sessoes, invasao ou escalada de privilegio, vazamento entre
   tenants, perda/corrupcao seria de dados, movimentar dinheiro, gateway de
   pagamento, criptografia/segredos, recuperacao de conta, migration destrutiva
   ou dificil de reverter, derrubar parte essencial da producao, operacao
   irreversivel de grande blast radius.
5. Nao escale por area nem por tamanho. Tocar auth, ter migration, mexer em
   permissoes, envolver dados financeiros, exigir muitos testes ou alterar
   varios arquivos **nao** torna a tarefa `critical`.
6. Respeite a flag do usuario. Nunca eleve `--fast`/`--standard` para
   `critical` por conta propria: relate o dano detectado, recomende
   `--critical` e siga no modo pedido. A unica correcao automatica e o piso:
   area sensivel derruba `fast` para `standard`.
7. Se for retomada ou `critical`, e `.agent/STATE.md` existir, encaminhe para
   `framework-next`. A mera existencia de `.agent/` nao obriga uma nova tarefa a
   usar o kernel.
8. Identifique a categoria (secao "Roteamento por categoria"), siga a instrucao
   do bloco, liste 1-4 assets relevantes e corte o resto.
9. Indique o primeiro asset a invocar.
10. Se CI, PR, merge ou integracao fizer parte do fluxo, acrescente o perfil de
    CI e as politicas de espera/proxima unidade, e selecione
    `ci-throughput-controller`. O modo continua sendo risco/execucao; o perfil de
    CI e um eixo separado.

## Modos

| Modo | Caminho | Defaults |
|---|---|---|
| `fast` | route → inspect → implement → targeted verification → diff review | sem `.agent/`, spec, contrato, seal, ledger, reviewers separados ou worktree |
| `standard` | route → focused grounding → short plan → implement → tests → integrated review | estado opcional, spec/contrato leves, uma review integrada, sem seal |
| `critical` | lifecycle persistente completo P0/P1 | estado, spec, contratos, seal, ledger e duas reviews independentes |

Regra de desempate: duvida → `standard`; curto e contido comprovado → `fast`;
dano grave comprovado → `critical`.

Calibracao esperada, como referencia e nao como cota: `fast` ~30%, `standard`
~65-70%, `critical` ~1-5%.

O modo pertence a tarefa. Uma fase pode conter tarefas `fast`, `standard` e
`critical`; uma tarefa `critical` nao eleva as vizinhas. Para corrigir uma
classificacao ja registrada, use
`framework-next set-execution-mode` — escalada exige `--risk` nomeando o dano
grave; reducao exige apenas `--reason`.

## Roteamento por categoria

Como usar:
1. Identifique a categoria principal do pedido pelos gatilhos de cada bloco.
2. Siga a instrucao do bloco antes de escolher assets.
3. Escolha 1-4 assets dentro do bloco. Pisos obrigatorios (agentes e frontend) nao
   contam no limite.
4. Pedido que cruza categorias: assets da categoria principal + no maximo 1 de outra.
5. O modo (`fast`/`standard`/`critical`) vale para todos os blocos; o bloco nao muda
   o modo.

### 1. Agentes de IA

Gatilhos: codigo que chama LLM, system prompt, tools de agente, chatbot/WhatsApp/
assistente, comportamento de conversa, eval de conversa, troca de modelo.

Instrucao obrigatoria, em qualquer modo e fora do limite de 4: aplique
`rubrics/agent-design.md`. Comece minimo (um agente, prompt curto, tools); camada
nova so por falha medida; protecao na entrada e nos efeitos, nunca na fala; corrija
pela escada (descricao de tool, prompt, dado pronto, contrato tipado, verificacao
estreita, codigo). Sequencia em `workflows/agent-workflow.md`. Infra de canal
(fila, outbox, webhook, persistencia) e desenvolvimento de software comum: reuse,
nao duplique.

| Situacao | Skill | Apoio |
|---|---|---|
| Criar ou refatorar agente | agent-builder | templates/agent-design, agent-tool-designer, agent-eval-planner |
| Corrigir comportamento (encaminha demais, inventa, nao chama tool) | agent-prompt-refiner | agent-eval-planner, agent-builder |
| Desenhar tool de agente | agent-tool-designer | templates/agent-tool-design, tool-contract-auditor |
| Auditar contrato de tool | tool-contract-auditor | templates/tool-contract-report, api-contract-auditor |
| Validar tool em runtime | tool-runtime-validator | templates/tool-runtime-validation, runtime-qa-audit |
| Protecao para risco nomeado (crise, pagamento, efeito irreversivel) | agent-guardrails-implementer | templates/agent-guardrails-plan, agent-security-auditor |
| Medir mudanca / regressao pareada | agent-eval-planner | templates/agent-eval-plan, test-confidence-mapper |
| Ciclo com conversas de producao (Eval Flywheel) | agent-eval-flywheel | templates/agent-eval-flywheel-report, agent-eval-planner, skill-evolution-loop |
| Trocar modelo/provider | model-flexibility-auditor | templates/model-flexibility-report, agent-eval-planner |
| Custo, latencia, tokens | agent-optimization-auditor | templates/agent-optimization-report, model-routing |
| Logs/traces/custo por turno | agent-observability-auditor | templates/agent-observability-report, persistent-debug-session |
| Seguranca de agente (injection, exfiltracao, tool insegura) | agent-security-auditor | templates/agent-security-report, templates/prompt-injection-eval |
| Hardcode de comportamento, modelo, provider | agent-anti-hardcode-auditor | templates/agent-hardcode-report, config-surface-auditor |
| QA do agente rodando | agent-runtime-qa | templates/agent-runtime-qa-report, tool-runtime-validator |
| Revisar diff de agente | agent-code-reviewer | templates/agent-code-review-report, diff-reviewer |
| Documentar agente | agent-doc-writer | templates/agent-doc, docs-sync-auditor |
| Voz/visao em tempo real | agent-realtime-multimodal | templates/multimodal-streaming-design, architecture-decision |
| Deploy de agente em nuvem (Cloud Run/GCP) | agent-cloud-deployer | templates/agent-cloud-deploy-spec, infra-security-auditor |

### 2. Desenvolvimento de software

Gatilhos: feature, endpoint, bug, refatoracao, backend, plano de implementacao,
repo novo, ideia aberta.

Instrucao: menor mudanca completa; reuse helpers e padroes do repo antes de criar
abstracao. Planejamento so na medida do modo. Se o pedido mencionar brief, plano de
execucao, quebrar em etapas ou preparar trabalho para outro agente, priorize
`execution-plan-builder` (`workflows/execution-brief`); prompts por etapa ou
delegacao, `execution-prompt-builder`.

| Situacao | Skill | Apoio |
|---|---|---|
| Entrar em repo novo | project-context-loader, repo-map-builder | — |
| Ideias / objetivo aberto | brainstorm-lab | — |
| Brief/documentacao/plano de execucao | execution-plan-builder | workflows/execution-brief, plan-quality-checker |
| Prompts por etapa para execucao | execution-prompt-builder | templates/execution-prompt-package, handoff-builder, code-review-gate |
| Refinar pedido cru ou prompt por acao | prompt-refiner | templates/prompt-package, templates/action-prompt-package |
| Plano de implementacao | implementation-planner | templates/implementation-plan |
| Planejar backend em fatias | backend-slice-planner | templates/backend-slice-plan, api-contract-auditor, test-strategy-builder |
| Auditar plano antes de executar | plan-quality-checker | templates/plan-quality-report, rubrics/testing, rubrics/api-contract |
| Decisao de arquitetura | architecture-decision | rubrics/architecture, templates/adr |
| Aplicar padroes locais antes de codar | coding-standards-enforcer | rubrics/coding-standards, repo-map-builder |
| Contrato de API | api-contract-auditor | rubrics/api-contract, workflows/api-refactor |
| Bug | bug-repro-lab | workflows/bugfix, rubrics/testing |
| Debug persistente | persistent-debug-session | templates/debug-session, bug-repro-lab, handoff-builder |
| Mapear deadcode/orfaos | deadcode-orphan-mapper | templates/deadcode-orphan-map, repo-map-builder |

### 3. Testes e verificacao

Gatilhos: estrategia de testes, cobertura, "esta pronto?", QA do app rodando.

Instrucao: verificacao proporcional ao modo; teste novo para logica nao trivial.
Agente: use o bloco 1 (`agent-eval-planner`, `agent-runtime-qa`).

| Situacao | Skill | Apoio |
|---|---|---|
| Estrategia de testes | test-strategy-builder | rubrics/testing, templates/test-plan |
| Mapa de confianca de testes | test-confidence-mapper | templates/test-confidence-map, test-strategy-builder |
| Verificar cobertura do objetivo | goal-coverage-verifier | templates/goal-coverage-report, diff-reviewer |
| QA app rodando | runtime-qa-audit | — |

### 4. Revisao

Gatilhos: revisar diff/PR, decidir profundidade de review.

Instrucao: `fast`/`standard` usam uma review integrada; `critical` usa duas
independentes (spec antes de qualidade). Diff de agente inclui `agent-code-reviewer`.

| Situacao | Skill | Apoio |
|---|---|---|
| Revisar diff/PR | diff-reviewer | rubrics/diff-review, templates/audit-report |
| Decidir gate de code review | code-review-gate | templates/code-review-gate-report, agent-code-reviewer |
| Revisar conformidade com spec | spec-compliance-reviewer | templates/spec-compliance-review, workflows/review-application |
| Revisar qualidade depois da spec | code-quality-reviewer | diff-reviewer, workflows/review-application |

### 5. Design e frontend

Gatilhos: componente, pagina, layout, estilo, animacao, gesto, UI web ou mobile.

Instrucao obrigatoria: qualquer tarefa que toque frontend inclui **sempre**
`apple-design` e `impeccable:impeccable`, em qualquer modo e fora do limite de 4,
mesmo que o pedido nao cite UI. Os demais assets sao proporcionais.

| Situacao | Skill | Apoio |
|---|---|---|
| Frontend obrigatorio (qualquer tarefa de UI) | apple-design, impeccable:impeccable | — |
| UI/UX | ui-ux-pro-max-audit | rubrics/ui-ux, workflows/frontend-refactor |
| Refatorar frontend preservando contratos e rotas | frontend-refactor-contract-guardian | rubrics/ui-ux, workflows/frontend-refactor |
| Polimento de UI, decisoes de componente e animacao | emil-design-eng | apple-design, ui-ux-pro-max-audit |
| Criar animacao do zero na web | animate | animation-performance, emil-design-eng |
| Animacao em React Native / Expo | animate-expo | animation-performance |
| Animacao web fora do frame budget (jank, will-change) | animation-performance | animate |
| Revisar codigo de animacao | review-animations | animation-performance, emil-design-eng |
| Auditar motion de codebase e gerar plano | improve-animations | review-animations, find-animation-opportunities |
| Achar onde animar (somente leitura) | find-animation-opportunities | animate |
| Nomear um efeito de motion (glossario) | animation-vocabulary | — |
| Toasts com Sonner | ask-sonner | — |
| Testar UI com dados extremos | break-ui | ui-ux-pro-max-audit |
| Comparar versoes de componente visualmente | prototype | emil-design-eng |
| Escolher biblioteca de frontend | pick-ui-library | — |
| Web app com cara de nativo no celular | mobile-native | apple-design |
| Swift moderno, concorrencia, testes | write-swift | — |

### 6. Motion e video

Gatilhos: video, MP4, HyperFrames, Remotion, animacao renderizada.

| Situacao | Skill | Apoio |
|---|---|---|
| Video em motion e pipeline HyperFrames | motion-video-director, hyperframes | rubrics/motion-video, hyperframes-core, hyperframes-studio, hyperframes-creative, hyperframes-animation, hyperframes-audio, hyperframes-cli, hyperframes-keyframes, hyperframes-registry |

### 7. Seguranca

Gatilhos: vulnerabilidade, auth, segredo, dados pessoais, pen test.

Instrucao: tocar area sensivel impede `fast`, mas nao escala para `critical`
sozinho. Escolha o auditor especifico; `security-audit` so para varredura completa.
Agente: `agent-security-auditor` (bloco 1).

| Situacao | Skill | Apoio |
|---|---|---|
| Seguranca/privacidade e dados pessoais | security-privacy-audit | rubrics/security-privacy, workflows/security-review, docs/security-coverage |
| Auditoria de seguranca completa / pen test do codigo | security-audit | security-privacy-audit, workflows/security-review |
| SQLi, XSS, RCE, XXE, SSRF, deserializacao, redirect, mass assignment | injection-vulnerability-auditor | rubrics/injection-vulnerabilities, templates/security-audit-report |
| Auth, JWT, sessao, CSRF, IDOR, papel admin, bypass de fluxo | authn-authz-auditor | rubrics/access-control, templates/security-audit-report |
| Segredo hardcoded, chave, hash fraco, TLS sem verificacao | crypto-secrets-auditor | rubrics/crypto-secrets, env-gitignore-auditor |
| Debug em producao, CORS, portas, Docker root, IaC, pipeline | infra-security-auditor | rubrics/infra-security, dependency-risk-auditor |

### 8. Infraestrutura e operacao

Gatilhos: deploy, release, CI, migration, env/config, dependencia, logs, performance.

Instrucao: escolha pela parte da infra tocada. Perfil de CI e eixo separado do
modo (ver "Saida obrigatoria"). Nao crie infra nova para necessidade futura.

| Parte | Situacao | Skill | Apoio |
|---|---|---|---|
| Dados | Auditar migration/dados | data-migration-auditor | templates/data-migration-report, rubrics/data-migration |
| Config | Auditar configs/env | config-surface-auditor | templates/config-surface-report, docs-sync-auditor |
| Config | Auditar env/gitignore/secrets | env-gitignore-auditor | templates/env-gitignore-report, config-surface-auditor |
| Dependencias | Auditar dependencia | dependency-risk-auditor | templates/dependency-risk-report, architecture-decision |
| CI | Escolher perfil de CI e politica de espera | ci-throughput-controller | kernel/ci-throughput-policy, templates/ci-throughput-decision |
| CI | Agrupar PRs para CI de integracao | integration-batch-manager | workflows/integration-batch, kernel/ci-throughput-policy |
| Release | Release | release-verifier | workflows/release, templates/release-checklist |
| Release | Empacotar release backend | backend-release-packager | templates/backend-release-package, goal-coverage-verifier |
| Deploy de agente | Implantar e operar agente em nuvem | agent-cloud-deployer | templates/agent-cloud-deploy-spec, infra-security-auditor |
| Logs | Planejar logs de feature | feature-logging-planner | templates/feature-logging-plan, security-privacy-audit |
| Performance | Auditar performance budget | performance-budget-auditor | templates/performance-budget-report, rubrics/performance-budget |

### 9. Orquestracao, estado e contexto

Gatilhos: varios agentes, Maestri, worktrees, retomar trabalho, estado persistente,
contexto cheio, handoff, escolher modelo para a tarefa.

Instrucao: estado persistente so em retomada ou `critical`; a existencia de `.agent/`
nao obriga o kernel.

| Situacao | Skill | Apoio |
|---|---|---|
| Inicializar ou retomar estado persistente | framework-next | kernel/protocol, templates/project-state |
| Especificar e planejar fase persistente | workflow-planner | execution-plan-builder, plan-quality-checker |
| Executar plano persistente | workflow-runner | task-runner, kernel/state-machine |
| Executar contrato de tarefa | task-runner | kernel/test-policy, templates/task-result |
| Escolher peso da tarefa | task-mode-router | workflow-orchestrator, test-strategy-builder |
| Orquestrar equipe multiagente/Maestri | team-orchestrator | workflows/multi-agent-development.md, decision-authority-router, templates/agent-dispatch |
| Preparar sessao limpa para nova task | fresh-task-session | kernel/context-budget-policy, templates/agent-dispatch |
| Gerir writers paralelos em worktrees | worktree-lane-manager | kernel/orchestration-policy, templates/orchestration-state |
| Manter notas/perguntas/progresso do projeto | project-notebook | templates/project-notes, workflows/decision-pause-and-continue |
| Classificar decisao descoberta na execucao | decision-authority-router | workflows/decision-pause-and-continue |
| Handoff entre agentes | handoff-builder | workflows/agent-handoff, templates/handoff-summary |
| Conversa longa / contexto cheio | context-compressor | workflows/long-conversation-handoff |
| Escolher Codex/Claude/ChatGPT/modelo para a tarefa | model-routing | — |

### 10. Git, PR e documentacao

| Situacao | Skill | Apoio |
|---|---|---|
| Decidir git/commit/PR | git-decision-router | templates/git-decision-report, commit-readiness-checker, pr-description-builder |
| Checar commit readiness | commit-readiness-checker | templates/commit-readiness-report, env-gitignore-auditor |
| Montar descricao de PR | pr-description-builder | templates/pr-description, goal-coverage-verifier |
| Decidir documentacao | documentation-decision-router | templates/documentation-decision, architecture-decision |
| Sincronizar docs | docs-sync-auditor | templates/docs-sync-report, rubrics/docs-sync |

### 11. Marketing e anuncios

| Situacao | Skill | Apoio |
|---|---|---|
| Diagnosticar campanhas e trafego pago (Google Ads) | ads-performance-auditor | rubrics/ads-performance, templates/ads-performance-audit-report |
| Sincronizar CRM e audiencias com Ads (Customer Match) | crm-ad-sync-planner | templates/crm-ad-sync-plan, authn-authz-auditor, security-privacy-audit |

### 12. Manutencao do framework

| Situacao | Skill | Apoio |
|---|---|---|
| Instalar/atualizar framework | agent-framework-installer | docs/portability, docs/maintenance |
| Evoluir framework por recorrencia | skill-evolution-loop | docs/task-memory, docs/skill-standards |
| Auditar qualidade de skill | skill-quality-auditor | docs/skill-standards, installers/verify-framework |

## Saida obrigatoria
```yaml
selected_mode: fast | standard | critical
reason:
risk_factors: []      # apenas caminhos de dano grave nomeados
sensitive_areas: []   # impede fast (piso standard); nunca escala sozinho para critical
fast_factors: []
complexity_factors: []
assets_selected: []
assets_skipped: []
```

Quando CI/PR/integracao entra no fluxo, o router tambem reporta o eixo de CI —
campos opcionais e aditivos, que nao alteram o significado de fast/standard/critical:

```yaml
ci_profile: minimal | targeted | full
ci_blocking_point: before_merge | now | none
ci_wait_policy: background | blocking_before_merge | blocking_now
next_work_policy: continue_independent | stack_local | wait
local_gates: []
remote_gates: []
deferred_gates: []      # cada gate adiado declara onde roda de fato
runner_policy:          # contencao de runner self-hosted compartilhado
```

`standard` nao implica pipeline completo nem espera sincrona. CI bloqueia merge,
nao necessariamente a proxima unidade de trabalho. Perfil `full` levanta
`publication_hold`, nao espera automatica. Detalhe em
`kernel/ci-throughput-policy.md`; sequencia operacional em
`workflows/ci-throughput.md`.

Contexto operacional entra como dado, nao como texto do pedido:

```bash
./scripts/agent-framework-route --auto \
  --runner-kind self_hosted_shared --remote-ci-running \
  --next-unit dependent --unit-ref pr-42 \
  "Implemente a tela de fornecedores."
```

Tambem aceita `--ci-context-json '{...}'`. Campo ausente usa o default
documentado; dependencia nao declarada nunca vira dependencia confirmada.

Toda selecao `fast` ou `critical` inclui uma justificativa concreta: `fast`
mostra por que o trabalho e curto e contido; `critical` nomeia o dano grave. A
saida pode ainda indicar intencao e primeiro asset.

## Criterios de aceite
- `standard` e o default quando nada argumenta em contrario.
- `fast` exige evidencia positiva de escopo curto e contido, sem area sensivel.
- `critical` nunca e inferido: exige selecao explicita. Um caminho de dano
  grave detectado vira recomendacao, com o dano nomeado.
- Area sensivel (auth, migration, financeiro, tenant) impede `fast` (piso
  `standard`) mas nunca escala sozinha para `critical`.
- No maximo 4 assets, sem contar os pisos: `rubrics/agent-design.md` em agentes e
  `apple-design` + `impeccable:impeccable` em frontend; sem listar tudo.
- Qualquer tarefa de agente retorna `rubrics/agent-design.md` em `assets_selected`.
- Qualquer tarefa de frontend retorna `apple-design` e `impeccable:impeccable` em `assets_selected`.
- Nao duplicar checklist de rubric/workflow aqui; so referenciar.
- Backend simples nao e automaticamente `critical`.
- Roteamento nao cria `.agent/` nem instancia templates.
- Perfil de CI nunca e derivado do modo sozinho: `standard` pode ser `minimal`,
  `targeted` ou `full` conforme o impacto real da mudanca.
- Nao orientar espera sincrona por CI sem motivo nomeado.

## Exemplos de uso
- Codex: `$agent-framework-router Qual skill para auditar este PR de API?`
- Codex: `$agent-framework-router --fast Corrija o typo no título da página.`
- Codex: `$agent-framework-router --standard Implemente o endpoint e os testes.`
- Codex: `$agent-framework-router --critical Troque o gateway de pagamento.`
- Claude Code: `/agent-framework-router Por onde começo neste repo desconhecido?`
