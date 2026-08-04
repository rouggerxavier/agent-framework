---
name: agent-framework-router
description: Use primeiro para selecionar fast, standard ou critical e escolher poucos assets proporcionais, com standard como padrão e critical apenas por escolha explícita.
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
8. Classifique a intencao, liste 1-4 assets relevantes e corte o resto.
9. Indique o primeiro asset a invocar.

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

## Prioridade alta
- Se o pedido mencionar brief, documentacao de feature/refatoracao, plano de execucao, organizar tarefa, quebrar em etapas ou preparar trabalho para outro agente, priorize `execution-plan-builder`.
- Se o pedido mencionar prompts por etapa, prompt para proximo agente, pacote de prompts ou delegar execucao, priorize `execution-prompt-builder`.
- Para esse fluxo, referencie `workflows/execution-brief` e mantenha o router como dispatcher.

## Tabela de roteamento
| Intencao | Skill | Apoio |
|---|---|---|
| Inicializar ou retomar estado persistente | framework-next | kernel/protocol, templates/project-state |
| Especificar e planejar fase persistente | workflow-planner | execution-plan-builder, plan-quality-checker |
| Executar plano persistente | workflow-runner | task-runner, kernel/state-machine |
| Executar contrato de tarefa | task-runner | kernel/test-policy, templates/task-result |
| Revisar conformidade com spec | spec-compliance-reviewer | templates/spec-compliance-review, workflows/review-application |
| Revisar qualidade depois da spec | code-quality-reviewer | diff-reviewer, workflows/review-application |
| Entrar em repo novo | project-context-loader, repo-map-builder | — |
| Ideias / objetivo aberto | brainstorm-lab | — |
| Brief/documentacao/plano de execucao | execution-plan-builder | workflows/execution-brief, brainstorm-lab, plan-quality-checker |
| Prompts por etapa para execucao | execution-prompt-builder | templates/execution-prompt-package, handoff-builder, code-review-gate |
| Criar/refatorar agente | agent-builder | workflows/agent-workflow, templates/agent-design |
| Auditar hardcode em agente | agent-anti-hardcode-auditor | templates/agent-hardcode-report, model-flexibility-auditor, config-surface-auditor |
| Auditar flexibilidade de modelo | model-flexibility-auditor | templates/model-flexibility-report, model-routing, runtime-qa-audit |
| Auditar configs/env/gitignore | config-surface-auditor | templates/config-surface-report, security-privacy-audit, docs-sync-auditor |
| Escolher peso da tarefa | task-mode-router | workflow-orchestrator, diff-reviewer, test-strategy-builder |
| Planejar backend em fatias | backend-slice-planner | templates/backend-slice-plan, api-contract-auditor, test-strategy-builder |
| Auditar plano antes de executar | plan-quality-checker | templates/plan-quality-report, rubrics/testing, rubrics/api-contract |
| Verificar cobertura do objetivo | goal-coverage-verifier | templates/goal-coverage-report, diff-reviewer, release-verifier |
| Empacotar release backend | backend-release-packager | templates/backend-release-package, release-verifier, goal-coverage-verifier |
| Decisao de arquitetura | architecture-decision | rubrics/architecture, templates/adr |
| Plano de implementacao | implementation-planner | templates/implementation-plan |
| Bug | bug-repro-lab | workflows/bugfix, rubrics/testing |
| Debug persistente | persistent-debug-session | templates/debug-session, bug-repro-lab, handoff-builder |
| Estrategia de testes | test-strategy-builder | rubrics/testing, templates/test-plan |
| Mapa de confianca de testes | test-confidence-mapper | templates/test-confidence-map, test-strategy-builder, release-verifier |
| Revisar diff/PR | diff-reviewer | rubrics/diff-review, templates/audit-report |
| Aplicar padroes locais antes de codar | coding-standards-enforcer | rubrics/coding-standards, repo-map-builder, diff-reviewer |
| Contrato de API | api-contract-auditor | rubrics/api-contract, workflows/api-refactor |
| Auditar dependencia | dependency-risk-auditor | templates/dependency-risk-report, security-privacy-audit, architecture-decision |
| Auditar migration/dados | data-migration-auditor | templates/data-migration-report, rubrics/data-migration, release-verifier |
| Sincronizar docs | docs-sync-auditor | templates/docs-sync-report, rubrics/docs-sync, release-verifier |
| Seguranca/privacidade | security-privacy-audit | rubrics/security-privacy |
| UI/UX | ui-ux-pro-max-audit | rubrics/ui-ux, workflows/frontend-refactor |
| QA app rodando | runtime-qa-audit | — |
| Release | release-verifier | workflows/release, templates/release-checklist |
| Handoff entre agentes | handoff-builder | workflows/agent-handoff, templates/handoff-summary |
| Conversa longa / contexto cheio | context-compressor | workflows/long-conversation-handoff |
| Refinar pedido cru | prompt-refiner | templates/prompt-package |
| Refinar prompt por acao | prompt-refiner | templates/action-prompt-package |
| Refinar prompt de agente | agent-prompt-refiner | templates/action-prompt-package, agent-builder, agent-anti-hardcode-auditor |
| Desenhar tool de agente | agent-tool-designer | templates/agent-tool-design, agent-builder, security-privacy-audit |
| Auditar contrato de tool | tool-contract-auditor | templates/tool-contract-report, api-contract-auditor, security-privacy-audit |
| Validar tool em runtime | tool-runtime-validator | templates/tool-runtime-validation, runtime-qa-audit, test-confidence-mapper |
| Implementar guardrails de agente | agent-guardrails-implementer | templates/agent-guardrails-plan, agent-security-auditor, tool-contract-auditor |
| Auditar seguranca de agente | agent-security-auditor | templates/agent-security-report, security-privacy-audit, env-gitignore-auditor |
| Auditar env/gitignore/secrets | env-gitignore-auditor | templates/env-gitignore-report, config-surface-auditor, docs-sync-auditor |
| QA runtime de agente | agent-runtime-qa | templates/agent-runtime-qa-report, runtime-qa-audit, tool-runtime-validator |
| Planejar evals de agente | agent-eval-planner | templates/agent-eval-plan, test-strategy-builder, test-confidence-mapper |
| Auditar observabilidade de agente | agent-observability-auditor | templates/agent-observability-report, persistent-debug-session, agent-security-auditor |
| Planejar logs de feature | feature-logging-planner | templates/feature-logging-plan, runtime-qa-audit, security-privacy-audit |
| Decidir gate de code review | code-review-gate | templates/code-review-gate-report, diff-reviewer, agent-code-reviewer |
| Revisar codigo de agente | agent-code-reviewer | templates/agent-code-review-report, tool-contract-auditor, agent-security-auditor |
| Decidir git/commit/PR | git-decision-router | templates/git-decision-report, commit-readiness-checker, pr-description-builder |
| Checar commit readiness | commit-readiness-checker | templates/commit-readiness-report, docs-sync-auditor, env-gitignore-auditor |
| Montar descricao de PR | pr-description-builder | templates/pr-description, backend-release-packager, goal-coverage-verifier |
| Decidir documentacao | documentation-decision-router | templates/documentation-decision, architecture-decision, docs-sync-auditor |
| Documentar agente | agent-doc-writer | templates/agent-doc, templates/agent-design, docs-sync-auditor |
| Mapear deadcode/orfaos | deadcode-orphan-mapper | templates/deadcode-orphan-map, repo-map-builder, test-confidence-mapper |
| Otimizar agente | agent-optimization-auditor | templates/agent-optimization-report, model-routing, agent-runtime-qa |
| Auditar performance budget | performance-budget-auditor | templates/performance-budget-report, rubrics/performance-budget, runtime-qa-audit |
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
- No maximo 4 assets; sem listar tudo.
- Nao duplicar checklist de rubric/workflow aqui; so referenciar.
- Backend simples nao e automaticamente `critical`.
- Roteamento nao cria `.agent/` nem instancia templates.

## Exemplos de uso
- Codex: `$agent-framework-router Qual skill para auditar este PR de API?`
- Codex: `$agent-framework-router --fast Corrija o typo no título da página.`
- Codex: `$agent-framework-router --standard Implemente o endpoint e os testes.`
- Codex: `$agent-framework-router --critical Troque o gateway de pagamento.`
- Claude Code: `/agent-framework-router Por onde começo neste repo desconhecido?`
