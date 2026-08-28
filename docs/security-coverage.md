# Cobertura de Seguranca

Mapa das classes de vulnerabilidade cobertas pelo framework: qual skill audita,
qual rubric define o criterio e o que a checagem automatica alcanca.

`scripts/security-check` e uma primeira passada estatica. Ela reduz ruido obvio,
nunca substitui o auditor: `[fail]` bloqueia, `[warn]` indica onde olhar.

## Aplicacao

| # | Classe | Skill | Rubric | `security-check` |
| --- | --- | --- | --- | --- |
| 1 | Injecao de SQL | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | parcial (concatenacao em query) |
| 2 | Cross-Site Scripting | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | parcial (sinks de render) |
| 3 | Quebra de autenticacao | `authn-authz-auditor` | `rubrics/access-control.md` | parcial (`alg: none`, JWT sem expiracao) |
| 4 | Exposicao de dados sensiveis | `crypto-secrets-auditor` | `rubrics/crypto-secrets.md` | sim (segredo literal, `.env` versionado) |
| 5 | XML External Entities | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | parcial (parser sem hardening) |
| 6 | Controle de acesso quebrado (BOLA/IDOR) | `authn-authz-auditor` | `rubrics/access-control.md` | nao (exige modelo de atores) |
| 7 | Configuracao insegura | `infra-security-auditor` | `rubrics/infra-security.md` | parcial (debug, CORS `*`) |
| 8 | Injecao de comando de SO | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | parcial (`eval`, `shell=True`) |
| 9 | Componentes vulneraveis | `dependency-risk-auditor` | — | parcial (`npm audit`, `pip-audit`) |
| 10 | Falta de logging e monitoramento | `feature-logging-planner` | — | nao (exige leitura do fluxo) |
| 11 | CSRF | `authn-authz-auditor` | `rubrics/access-control.md` | nao |
| 12 | Desserializacao insegura | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | parcial (`pickle`, `yaml.load`) |
| 13 | Sessao fraca | `authn-authz-auditor` | `rubrics/access-control.md` | parcial (`Math.random`, `random` em token) |
| 14 | Open redirect | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | nao |
| 15 | Criptografia fraca | `crypto-secrets-auditor` | `rubrics/crypto-secrets.md` | parcial (MD5, SHA1, DES, `verify=False`) |
| 16 | SSRF | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | nao (exige rastrear a origem da URL) |
| 17 | Controle de acesso por funcao | `authn-authz-auditor` | `rubrics/access-control.md` | nao |
| 18 | Logica de negocio | `authn-authz-auditor` | `rubrics/access-control.md` | nao (exige invariantes do dominio) |
| 19 | Mass assignment | `injection-vulnerability-auditor` | `rubrics/injection-vulnerabilities.md` | nao |
| 20 | Container e IaC | `infra-security-auditor` | `rubrics/infra-security.md` | parcial (root, imagem sem pin, segredo em YAML) |

## Agentes

| Classe | Skill | Asset |
| --- | --- | --- |
| Prompt injection direta e indireta | `agent-security-auditor` | `templates/prompt-injection-eval.md` |
| Exfiltracao por resposta, tool ou memoria | `agent-security-auditor` | `templates/agent-security-report.md` |
| Tool com permissao excessiva | `agent-guardrails-implementer`, `tool-contract-auditor` | `templates/agent-guardrails-plan.md` |
| Segredo em log/trace de agente | `agent-observability-auditor` | `templates/agent-observability-report.md` |

## Transversal

| Necessidade | Asset |
| --- | --- |
| Quando o auditor e obrigatorio | `workflows/security-review.md` |
| Privacidade, retencao e ciclo de vida do dado | `skills/security-privacy-audit/SKILL.md` |
| Higiene de `.env`, `.gitignore` e artefatos | `skills/env-gitignore-auditor/SKILL.md` |
| Superficie de configuracao e defaults | `skills/config-surface-auditor/SKILL.md` |
| Primeira passada automatica | `scripts/security-check` |

## Limites conhecidos
- `security-check` usa apenas ferramentas nativas do repo e do sistema; sem
  scanner instalado, ele registra a lacuna em vez de aprovar.
- Nenhuma linha aqui substitui pentest, revisao legal ou threat model de produto.
- Classes que dependem de intencao (6, 10, 11, 14, 16, 17, 18, 19) exigem leitura
  humana ou de agente sobre o modelo de atores e os invariantes do dominio.
