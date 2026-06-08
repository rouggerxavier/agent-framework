# Framework Roadmap

## Diagnostico rapido
- O repo ja tem boa separacao entre `skills/`, `rubrics/`, `workflows/`, `templates/` e `docs/`.
- As skills sao curtas e consistentes, com media perto de 50 linhas.
- O ponto fraco principal era evolucao: nao havia memoria de recorrencia nem criterio para promover tarefa repetida para skill.
- O segundo ponto fraco era validacao: o verificador aceitava qualquer frontmatter com `name` e `description`, mesmo se nome e pasta divergissem.

## Norte
Criar um framework que ajude o agente a fazer quatro coisas bem:
1. Escolher o asset certo.
2. Executar tarefas recorrentes com padrao.
3. Aprender com repeticao sem salvar contexto sensivel.
4. Verificar qualidade antes de sincronizar ou delegar.

## Lacunas atuais
- A skill de auditoria de qualidade existe; falta usa-la em revisoes reais para calibrar severidade e duplicacao.
- Existem rubrics sem skill correspondente: docs sync, data migration, performance budget e coding standards.
- Falta inventario de dependencias entre skills, rubrics, workflows e templates.
- Falta criterio de versao/changelog para mudancas grandes no framework.
- Falta uma camada de exemplos reais por skill, mesmo que minima.

## Skills criadas a partir da roadmap
| Skill | Motivo | Status |
| --- | --- | --- |
| skill-quality-auditor | Revisa gatilho, escopo, duplicacao, saida, criterios e referencias de uma skill. | criada |
| task-mode-router | Escolhe fast, quick, full ou audit para evitar processo pesado quando uma rota leve basta. | criada |
| backend-slice-planner | Traz plano executavel para backend com read_first, contratos, testes, rollback e aceite verificavel. | criada |
| plan-quality-checker | Audita plano antes da execucao, pegando tarefas vagas, dependencia errada e aceite nao verificavel. | criada |
| goal-coverage-verifier | Verifica objetivo, decisoes, contratos e gaps depois da implementacao. | criada |
| test-confidence-mapper | Mapeia comandos por nivel: inner loop, PR ready, merge/release e caminhos especiais. | criada |
| dependency-risk-auditor | Revisa novas libs, licencas, manutencao, seguranca, lockfile e custo operacional. | criada |
| persistent-debug-session | Mantem investigacoes longas de bug com hipoteses, experimentos, evidencias e retomada. | criada |
| backend-release-packager | Empacota release backend com escopo, evidencias, contratos, migrations, docs, riscos e rollback. | criada |
| docs-sync-auditor | Transforma a rubric de docs-sync em procedimento para checar docs afetadas e riscos. | criada |
| data-migration-auditor | Usa a rubric de data migration para revisar schema, backfill, compatibilidade e rollback. | criada |
| agent-builder | Cria/refatora agentes com design de prompt, tools, memoria, modelo configuravel, guardrails e validacao. | criada |
| agent-anti-hardcode-auditor | Procura hardcode em modelos, providers, prompts, tools, paths, env vars, constantes e flags. | criada |
| model-flexibility-auditor | Audita configurabilidade, fallback, capability routing, custo, latencia e troca segura de modelo/provider. | criada |
| config-surface-auditor | Revisa env vars, defaults, overrides, secrets, `.env.example`, `.gitignore`, logs e artefatos locais. | criada |
| agent-prompt-refiner | Refina prompts de agentes, system prompts, tool instructions, guardrails, exemplos negativos e evals. | criada |
| agent-tool-designer | Define tools de agente com schema, permissao, side effects, erros, timeout, retry, idempotencia e exemplos. | criada |
| tool-contract-auditor | Audita contrato de tools: schema, payloads, erros, permissoes, side effects, timeout, retry e logs. | criada |
| tool-runtime-validator | Valida tools em execucao com casos reais, input invalido, falha externa, timeout, retry, logs e evidencias. | criada |
| agent-guardrails-implementer | Especifica guardrails de input, output, tool permission, escalation, stop conditions e audit logs. | criada |
| agent-security-auditor | Audita prompt injection, data exfiltration, unsafe tool use, secret leakage, logs sensiveis e permissao excessiva. | criada |
| env-gitignore-auditor | Checa `.gitignore`, `.env.example`, secrets, tokens, config local, logs, traces, caches e artefatos. | criada |
| agent-runtime-qa | Valida agente rodando com happy path, bad input, missing env, tool failure, timeout, retry, fallback e escalation. | criada |
| agent-eval-planner | Planeja evals simples com casos, expected behavior, allowed variance, failure modes e regressao. | criada |
| agent-observability-auditor | Audita logs, traces, metrics, cost tracking, prompt/tool audit, redaction e debug readiness. | criada |
| feature-logging-planner | Avalia, planeja, implementa ou revisa logs proporcionais de features sem overlogging nem vazamento. | criada |
| code-review-gate | Decide profundidade obrigatoria de review e bloqueia conclusao quando diff toca areas de risco. | criada |
| agent-code-reviewer | Revisa diffs de agentes com foco em prompts, tools, guardrails, config, observabilidade, fallback e testes. | criada |
| git-decision-router | Decide commit direto, esperar validacao, criar branch, abrir PR, deixar unstaged ou pedir review. | criada |
| commit-readiness-checker | Checa diff, escopo, testes, docs, secrets, arquivos mistos, mensagem e validacao pendente antes de commit. | criada |
| pr-description-builder | Gera descricao de PR com escopo, evidencias, riscos, rollback, docs, screenshots/logs e checklist. | criada |
| documentation-decision-router | Decide entre ADR, README update, runbook, changelog, prompt/package docs, release notes ou nada. | criada |
| agent-doc-writer | Documenta agentes com objetivo, tools, config, env, guardrails, evals, runtime QA, observabilidade e troubleshooting. | criada |
| deadcode-orphan-mapper | Mapeia codigo morto/orfao, exports nao usados, rotas mortas, jobs, configs, prompts e tools desconectados. | criada |
| agent-optimization-auditor | Otimiza agentes quanto a tokens, latencia, tool calls, retries, cache, prompt size, model tier e contexto. | criada |
| performance-budget-auditor | Audita budget de performance em backend e agentes: latencia, custo, memoria, queries, batch, cache e timeout. | criada |

## Backlog de novas skills
| Prioridade | Skill | Por que ajuda |
| --- | --- | --- |
| Media | coding-standards-enforcer | Aplica padroes locais antes de refatorar, revisar ou gerar patch. |
| Baixa | local-env-doctor | Diagnostica setup local, comandos, portas, env vars e falhas comuns. |
| Baixa | observability-runbook-builder | Cria runbook de logs, metricas, alertas, rollback e troubleshooting. |
| Baixa | skill-example-curator | Mantem exemplos curtos de prompts e saidas esperadas por skill. |

## Experimentos recomendados
1. Usar `skill-evolution-loop` por uma semana e ver quais entradas chegam a 2 ocorrencias.
2. Usar `skill-quality-auditor` nas proximas 3 skills criadas para calibrar o padrao.
3. Usar `task-mode-router` antes de tarefas de backend para medir se reduziu overhead.
4. Testar o ciclo prioridade 1 em uma tarefa backend real: `task-mode-router` -> `backend-slice-planner` -> `plan-quality-checker` -> implementacao -> `goal-coverage-verifier`.
5. Testar prioridade 2 em repo real: `test-confidence-mapper`, `dependency-risk-auditor` e `persistent-debug-session`.
6. Testar prioridade 3 no fechamento de uma entrega: `data-migration-auditor` -> `docs-sync-auditor` -> `backend-release-packager`.
7. Testar etapa 2 em agente real: `agent-anti-hardcode-auditor` -> `model-flexibility-auditor` -> `config-surface-auditor`.
8. Testar etapa 3 em prompts reais: `prompt-refiner` com modos -> `agent-prompt-refiner` -> `action-prompt-package`.
9. Testar etapa 4 em tool real: `agent-tool-designer` -> `tool-contract-auditor` -> `tool-runtime-validator`.
10. Testar etapa 5 em agente real: `agent-guardrails-implementer` -> `agent-security-auditor` -> `env-gitignore-auditor`.
11. Testar etapa 6 em agente real: `agent-eval-planner` -> `agent-observability-auditor` -> `agent-runtime-qa`.
12. Testar etapa 7 em feature real: `feature-logging-planner` antes da implementacao -> runtime QA verificando logs.
13. Testar etapa 8 em diff real: `code-review-gate` -> `agent-code-reviewer` ou `diff-reviewer`.
14. Testar etapa 9 em entrega real: `git-decision-router` -> `commit-readiness-checker` ou `pr-description-builder`.
15. Testar etapa 10 em entrega real: `documentation-decision-router` -> `architecture-decision` ou `agent-doc-writer`.
16. Testar etapa 11 em repo real: `deadcode-orphan-mapper` -> `agent-optimization-auditor` ou `performance-budget-auditor`.
17. Implementar o primeiro lote de agente em `docs/agent-workflow-roadmap.md`.
18. Promover rubrics existentes para skills apenas quando houver workflow claro, nao so checklist.
19. Adicionar `verify-framework.sh` a um hook ou CI quando o repo for remoto.

## Criterio para novas skills
Crie skill quando a tarefa tiver pelo menos uma destas propriedades:
- aparece 3 vezes em tarefas distintas;
- tem sequencia fragil que agentes esquecem;
- envolve risco alto e precisa de saida padronizada;
- exige consulta recorrente a rubrics, templates ou workflows combinados.

Nao crie skill quando:
- e apenas formato de documento;
- e checklist sem procedimento;
- duplica uma skill existente com outro nome;
- depende de contexto sensivel que nao deve morar no repo.
